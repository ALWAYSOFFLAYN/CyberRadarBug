import os
from datetime import datetime, timedelta, timezone

import requests
import telepot


TELEGRAM_BOT_TOKEN = "8831531377:AAFxheYxTqjWgjUJQEhghmqb14i-D3AmY9I"
NEWS_API_KEY = "a604630b66894d2f8fa9ecbdf7e4d13f"
TARGET_CHAT_ID = "-1003736482333"

MAX_ARTICLES = 5

SEARCH_QUERY = (
    '"research opportunity" OR '
    '"research internship" OR '
    '"research fellowship" OR '
    '"fellowship opportunity" OR '
    '"internship opportunity" OR '
    '"summer internship" OR '
    '"undergraduate research" OR '
    '"graduate fellowship"'
)

RELEVANCE_KEYWORDS = [
    "internship",
    "intern",
    "fellowship",
    "fellow",
    "research opportunity",
    "research program",
    "undergraduate research",
    "graduate research",
    "students",
    "apply",
    "application",
    "applications",
    "deadline",
]


def validate_config():
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")

    if not NEWS_API_KEY:
        missing.append("NEWS_API_KEY")

    if not TARGET_CHAT_ID:
        missing.append("TARGET_CHAT_ID")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )


def is_relevant(article):
    text = " ".join(
        [
            article.get("title") or "",
            article.get("description") or "",
            article.get("content") or "",
        ]
    ).lower()

    return any(keyword in text for keyword in RELEVANCE_KEYWORDS)


def fetch_articles():
    from_date = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).strftime("%Y-%m-%d")

    params = {
        "q": SEARCH_QUERY,
        "searchIn": "title,description",
        "language": "en",
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": 50,
    }

    headers = {
        "X-Api-Key": NEWS_API_KEY
    }

    response = requests.get(
        "https://newsapi.org/v2/everything",
        params=params,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(
            f"NewsAPI error: {data.get('message', 'Unknown error')}"
        )

    results = []
    seen_urls = set()

    for article in data.get("articles", []):
        url = article.get("url")

        if not url or url in seen_urls:
            continue

        if not is_relevant(article):
            continue

        seen_urls.add(url)
        results.append(article)

        if len(results) >= MAX_ARTICLES:
            break

    return results


def format_article(article, number):
    title = article.get("title") or "Untitled opportunity"
    description = article.get("description") or ""
    url = article.get("url") or ""

    if len(description) > 350:
        description = description[:347] + "..."

    text = f"🎓 {number}. {title}\n"

    if description:
        text += f"\n{description}\n"

    text += f"\n🔗 {url}"

    return text


def main():
    validate_config()

    bot = telepot.Bot(TELEGRAM_BOT_TOKEN)
    articles = fetch_articles()

    if not articles:
        bot.sendMessage(
            TARGET_CHAT_ID,
            "🔎 No new research, fellowship, or internship opportunities found today.",
        )
        return

    bot.sendMessage(
        TARGET_CHAT_ID,
        f"🎓 Daily Opportunity Digest\n\n"
        f"{len(articles)} research, fellowship, or internship opportunities found.",
    )

    for i, article in enumerate(articles, start=1):
        bot.sendMessage(
            TARGET_CHAT_ID,
            format_article(article, i),
            disable_web_page_preview=True,
        )


if __name__ == "__main__":
    main()
