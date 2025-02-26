import scrapy
from newspaper import Article
from pymongo import MongoClient

# MongoDB Atlas connection
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

class BbcSpider(scrapy.Spider):
    name = "bbc_spider"
    allowed_domains = ["bbc.com"]
    start_urls = ["https://www.bbc.com/news"]

    def parse(self, response):
        # Extract article links using correct CSS selectors
        article_links = response.css('a.gs-c-promo-heading::attr(href)').getall()

        for link in article_links:
            full_url = response.urljoin(link)  # Convert relative URLs to absolute
            yield scrapy.Request(full_url, callback=self.parse_article)

    def parse_article(self, response):
        # Use Newspaper3k to extract article content
        article = Article(response.url)
        article.download()
        article.parse()

        news_data = {
            "title": article.title,
            "authors": article.authors,
            "published_date": article.publish_date,
            "content": article.text,
            "url": response.url
        }

        # Store in MongoDB
        collection.insert_one(news_data)
        self.log(f"Article saved: {article.title}")

        yield news_data


