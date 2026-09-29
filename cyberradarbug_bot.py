import os
import html
import asyncio
import requests

from dotenv import load_dotenv

from telegram import (
    Update,
    BotCommand,
    ReplyKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


# Search queries used for NewsAPI.
#
# These are intentionally a little broader than simply searching
# for the command name.
TOPICS = {
    "ai": {
        "title": "🤖 AI",
        "query": (
            '"artificial intelligence" OR '
            '"generative AI" OR '
            '"machine learning" OR '
            'OpenAI OR Anthropic'
        ),
    },

    "cybersecurity": {
        "title": "🔐 Cybersecurity",
        "query": (
            'cybersecurity OR '
            '"cyber security" OR '
            'ransomware OR '
            '"data breach" OR '
            '"zero-day"'
        ),
    },

    "rnd": {
        "title": "🧪 R&D",
        "query": (
            '"research and development" OR '
            '"R&D" OR '
            '"research breakthrough" OR '
            '"new research"'
        ),
    },

    "fellowships": {
        "title": "🎓 Fellowships",
        "query": (
            'fellowship OR '
            '"research fellowship" OR '
            '"fellowship program"'
        ),
    },

    "internships": {
        "title": "💼 Internships",
        "query": (
            'internship OR '
            '"internship program" OR '
            '"summer internship"'
        ),
    },

    "conferences": {
        "title": "🎤 Conferences",
        "query": (
            'conference OR '
            '"research conference" OR '
            '"technology conference" OR '
            '"scientific conference"'
        ),
    },

    "scienceworks": {
        "title": "🔬 Science Works",
        "query": (
            '"scientific research" OR '
            '"researchers discovered" OR '
            '"scientists discovered" OR '
            '"new study" OR '
            '"research breakthrough"'
        ),
    },
}


# Buttons visible underneath the chat.
KEYBOARD = [
    ["🤖 AI", "🔐 Cybersecurity"],
    ["🧪 R&D", "🔬 Science Works"],
    ["🎓 Fellowships", "💼 Internships"],
    ["🎤 Conferences"],
]

BUTTON_TO_TOPIC = {
    "🤖 AI": "ai",
    "🔐 Cybersecurity": "cybersecurity",
    "🧪 R&D": "rnd",
    "🔬 Science Works": "scienceworks",
    "🎓 Fellowships": "fellowships",
    "💼 Internships": "internships",
    "🎤 Conferences": "conferences",
}


def get_news(topic):
    """
    Get up to 3 newest NewsAPI articles for a topic.
    """

    topic_data = TOPICS[topic]

    url = "https://newsapi.org/v2/everything"

    params = {
        "apiKey": NEWS_API_KEY,
        "q": topic_data["query"],
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 3,
    }

    response = requests.get(
        url,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(
            data.get("message", "Unknown NewsAPI error")
        )

    return data.get("articles", [])


def format_articles(topic, articles):
    """
    Turn NewsAPI articles into a Telegram HTML message.
    """

    title = TOPICS[topic]["title"]

    if not articles:
        return (
            f"<b>{html.escape(title)}</b>\n\n"
            "I couldn't find any recent articles."
        )

    lines = [
        f"<b>{html.escape(title)}</b>",
        "",
        "Latest news:",
        "",
    ]

    for i, article in enumerate(articles, start=1):

        article_title = article.get("title") or "Untitled"

        source = (
            article.get("source", {}).get("name")
            or "Unknown source"
        )

        url = article.get("url") or ""

        published = article.get("publishedAt", "")

        # 2026-09-30T12:30:00Z
        # becomes:
        # 2026-09-30 12:30 UTC
        if published:
            published = published.replace(
                "T",
                " ",
            ).replace(
                "Z",
                " UTC",
            )

            published = published[:16] + " UTC"

        article_title = html.escape(article_title)
        source = html.escape(source)

        lines.append(
            f"<b>{i}. {article_title}</b>"
        )

        lines.append(
            f"📰 {source}"
        )

        if published:
            lines.append(
                f"🕐 {published}"
            )

        if url:
            safe_url = html.escape(
                url,
                quote=True,
            )

            lines.append(
                f'🔗 <a href="{safe_url}">Read article</a>'
            )

        lines.append("")

    return "\n".join(lines)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    /start command.
    """

    keyboard = ReplyKeyboardMarkup(
        KEYBOARD,
        resize_keyboard=True,
    )

    message = (
        "👋 <b>Welcome to the News Bot!</b>\n\n"
        "Choose a topic below and I'll find up to "
        "3 of the latest articles.\n\n"
        "You can also use commands:\n\n"
        "/ai\n"
        "/cybersecurity\n"
        "/rnd\n"
        "/fellowships\n"
        "/internships\n"
        "/conferences\n"
        "/scienceworks"
    )

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def send_topic_news(
    update: Update,
    topic: str,
):
    """
    Fetch and send news.
    """

    waiting_message = await update.message.reply_text(
        f"🔎 Searching for {TOPICS[topic]['title']} news..."
    )

    try:
        # requests is synchronous.
        # Run it separately so Telegram's event loop
        # doesn't freeze while NewsAPI responds.
        articles = await asyncio.to_thread(
            get_news,
            topic,
        )

        message = format_articles(
            topic,
            articles,
        )

        await waiting_message.delete()

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    except requests.exceptions.RequestException as error:

        print("NewsAPI request error:", error)

        await waiting_message.edit_text(
            "❌ I couldn't connect to NewsAPI."
        )

    except Exception as error:

        print("Unexpected error:", error)

        await waiting_message.edit_text(
            "❌ Something went wrong while getting the news."
        )


#
# Individual commands
#

async def ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_topic_news(update, "ai")


async def cybersecurity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_topic_news(
        update,
        "cybersecurity",
    )


async def rnd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_topic_news(update, "rnd")


async def fellowships(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_topic_news(
        update,
        "fellowships",
    )


async def internships(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_topic_news(
        update,
        "internships",
    )


async def conferences(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_topic_news(
        update,
        "conferences",
    )


async def scienceworks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_topic_news(
        update,
        "scienceworks",
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handle keyboard button presses.
    """

    text = update.message.text

    topic = BUTTON_TO_TOPIC.get(text)

    if topic:
        await send_topic_news(
            update,
            topic,
        )


async def post_init(
    application: Application,
):
    """
    Register Telegram's / command menu.
    """

    commands = [
        BotCommand(
            "start",
            "Open the news menu",
        ),
        BotCommand(
            "ai",
            "Latest AI news",
        ),
        BotCommand(
            "cybersecurity",
            "Latest cybersecurity news",
        ),
        BotCommand(
            "rnd",
            "Latest R&D news",
        ),
        BotCommand(
            "fellowships",
            "Latest fellowship news",
        ),
        BotCommand(
            "internships",
            "Latest internship news",
        ),
        BotCommand(
            "conferences",
            "Latest conference news",
        ),
        BotCommand(
            "scienceworks",
            "Latest science news",
        ),
    ]

    await application.bot.set_my_commands(
        commands
    )


def main():

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing from .env"
        )

    if not NEWS_API_KEY:
        raise RuntimeError(
            "NEWS_API_KEY is missing from .env"
        )

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    #
    # Commands
    #

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "ai",
            ai,
        )
    )

    app.add_handler(
        CommandHandler(
            "cybersecurity",
            cybersecurity,
        )
    )

    app.add_handler(
        CommandHandler(
            "rnd",
            rnd,
        )
    )

    app.add_handler(
        CommandHandler(
            "fellowships",
            fellowships,
        )
    )

    app.add_handler(
        CommandHandler(
            "internships",
            internships,
        )
    )

    app.add_handler(
        CommandHandler(
            "conferences",
            conferences,
        )
    )

    app.add_handler(
        CommandHandler(
            "scienceworks",
            scienceworks,
        )
    )

    #
    # Keyboard buttons
    #

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            button_handler,
        )
    )

    print("🤖 Bot started.")
    print("Press Ctrl+C to stop.")

    app.run_polling()


if __name__ == "__main__":
    main()