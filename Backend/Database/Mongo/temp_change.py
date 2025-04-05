# import requests
# from bs4 import BeautifulSoup
# from pymongo import MongoClient
# import concurrent.futures
# from dateutil import parser
# from dotenv import load_dotenv
# import os

# load_dotenv()

# # MongoDB Connection
# MONGO_URI = os.getenv("MONGO_URI")
# client = MongoClient(MONGO_URI)
# db = client["news_db"]
# collection = db["articles"]

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
# }

# def is_placeholder_image(img_url):
#     """Check if the image URL is a placeholder."""
#     if not img_url:
#         return True
#     placeholder_strings = [
#         "grey-placeholder.png",
#         "/bbcx/grey-placeholder.png",
#         "https://www.bbc.com/bbcx/grey-placeholder.png"
#     ]
#     return any(placeholder in img_url for placeholder in placeholder_strings)

# def get_article_images(article_url):
#     """Fetch images only from within the article content"""
#     try:
#         response = requests.get(article_url, headers=headers, timeout=10)
#         if response.status_code != 200:
#             return []

#         soup = BeautifulSoup(response.text, "html.parser")
#         article = soup.find('article')  # Focus only on the article content
#         if not article:
#             return []

#         img_urls = set()

#         # Find all images within the article
#         for img in article.find_all('img'):
#             # Check src attribute first
#             if img.get('src'):
#                 img_url = img['src']
#                 if not is_placeholder_image(img_url):
#                     img_urls.add(img_url)
            
#             # Check srcset if exists
#             if img.get('srcset'):
#                 # Get all URLs from srcset (take the first part before space)
#                 for src in img['srcset'].split(','):
#                     src_url = src.strip().split(' ')[0]
#                     if src_url and not is_placeholder_image(src_url):
#                         img_urls.add(src_url)

#         # Convert to absolute URLs and return as list
#         return [
#             f'https://www.bbc.com{url}' if url.startswith('/') else url
#             for url in img_urls
#             if not url.startswith('data:')  # Skip data URIs
#         ]

#     except Exception as e:
#         print(f"❌ Error fetching images for {article_url}: {e}")
#         return []

# def backfill_images_for_articles():
#     """Backfill images for articles that have no images or only placeholders."""
#     # Find articles that need image updates
#     query = {
#         "$or": [
#             {"images": {"$exists": False}},
#             {"images": {"$size": 0}},
#             {"images": {"$elemMatch": {"$regex": "grey-placeholder.png"}}}
#         ]
#     }
    
#     articles_to_update = list(collection.find(query))
#     print(f"Found {len(articles_to_update)} articles needing image updates")
    
#     if not articles_to_update:
#         print("No articles need image updates")
#         return
    
#     # Process articles in parallel
#     with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
#         # Create a mapping of URL to article for easy lookup
#         url_to_article = {article['url']: article for article in articles_to_update}
        
#         # Fetch images for all URLs
#         futures = {executor.submit(get_article_images, url): url for url in url_to_article.keys()}
        
#         for future in concurrent.futures.as_completed(futures):
#             url = futures[future]
#             try:
#                 new_images = future.result()
#                 if new_images:
#                     # Update the article in MongoDB
#                     result = collection.update_one(
#                         {"url": url},
#                         {"$set": {"images": new_images}}
#                     )
#                     if result.modified_count == 1:
#                         print(f"✅ Updated images for {url} - found {len(new_images)} images")
#                     else:
#                         print(f"⚠️ No update made for {url} (may have been modified concurrently)")
#                 else:
#                     print(f"ℹ️ No valid images found for {url}")
#             except Exception as e:
#                 print(f"❌ Failed to process {url}: {e}")

# if __name__ == "__main__":
#     backfill_images_for_articles()



