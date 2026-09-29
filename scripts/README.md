## Telegram Bot for Daily News Updates

### Introduction

In this documentation, we will discuss how to create a Telegram bot that fetches news and sends you daily updates in the morning. We will be using Python to develop the bot and the News API to fetch the latest news articles.

### Key Concepts
Before we dive into the code, let's understand some key concepts:

1. **Telegram Bot**: A Telegram bot is an automated program that interacts with users through the Telegram messaging platform. It can receive and send messages, as well as perform various tasks based on user commands.

2. **News API**: The News API is a service that provides access to a wide range of news articles from various sources. It allows developers to fetch news articles based on different parameters like country, category, and keywords.

3. **dotenv**: The dotenv library is used to load environment variables from a .env file. It helps in keeping sensitive information like API keys and tokens separate from the code.

### Code Structure
The code provided is structured as follows:

1. Importing the necessary libraries and modules:

 - os: Provides functions for interacting with the operating system.
 - time: Provides functions for working with time-related tasks.
 - requests: Allows sending HTTP requests to the News API.
 - telepot: A Python wrapper for the Telegram Bot API.
 - dotenv: Loads environment variables from a .env file.

2. Loading API keys and tokens from the .env file using load_dotenv().

3. Defining a function fetch_technology_news() to fetch the latest technology news articles from the News API. It takes parameters like API key, country, category, and the number of articles to fetch.

4. Implementing error handling and returning the fetched articles if the API request is successful.

5. Defining a function send_news_on_start() to send the fetched news articles to the specified chat ID. It takes parameters like API key and chat ID.

6. Creating an instance of the Telegram bot using the provided token.

7. Sending news articles when the bot starts by calling the send_news_on_start() function.

### Code Examples

Let's take a closer look at some code examples to understand how the Telegram bot works:

1. Fetching Technology News:
```python
def fetch_technology_news(api_key, country='in', category='technology', num_articles=5):
    base_url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'country': country,
        'category': category,
        'apiKey': api_key,
        'pageSize': num_articles
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'ok':
            articles = data['articles']
            return articles
        else:
            print(f"Error: {data['message']}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []
```

This function fetches the latest technology news articles from the News API. It takes parameters like API key, country, category, and the number of articles to fetch. It sends an HTTP GET request to the News API with the specified parameters and handles any exceptions that may occur. If the API request is successful, it returns the fetched articles otherwise, it prints an error message and returns an empty list.

2. Sending News on Start:
```python
 Copy code
def send_news_on_start(api_key, chat_id):
    articles = fetch_technology_news(api_key)

    if articles:
        for idx, article in enumerate(articles, start=1):
            title = article['title']
            url = article['url']
            news_message = f"{idx}. {title}\n   {url}\n"
            bot.sendMessage(chat_id, news_message)
    else:
        bot.sendMessage(chat_id, "Error fetching news. Please try again later.")
```

This function sends the fetched news articles to the specified chat ID. It calls the `fetch_technology_news()` function to get the articles and iterates over them to create a message with the article title and URL. It then uses the `bot.sendMessage()` method to send the message to the chat ID. If there are no articles fetched, it sends an error message instead.



