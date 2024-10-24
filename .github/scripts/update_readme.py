import os
import feedparser
import requests
from bs4 import BeautifulSoup
import re
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_blog_posts():
    """
    Fetches blog posts from your website with detailed logging.
    """
    blog_url = os.getenv('BLOG_URL', 'https://munwalker.com')
    logger.info(f"Attempting to fetch posts from: {blog_url}")
    
    posts = []
    
    # First attempt: RSS feed
    try:
        feed_url = f"{blog_url}/feed"
        logger.info(f"Trying RSS feed at: {feed_url}")
        
        feed = feedparser.parse(feed_url)
        if feed.entries:
            logger.info(f"Found {len(feed.entries)} posts in RSS feed")
            posts = [
                {
                    'title': entry.title,
                    'url': entry.link
                }
                for entry in feed.entries[:4]
            ]
            return posts
        else:
            logger.info("No entries found in RSS feed")
            
    except Exception as e:
        logger.error(f"RSS feed error: {str(e)}")
    
    # Second attempt: Direct HTML scraping
    try:
        logger.info(f"Attempting to scrape HTML from: {blog_url}")
        response = requests.get(blog_url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        logger.info("Successfully fetched webpage")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Log the HTML structure for debugging
        logger.debug("Page HTML structure:")
        logger.debug(soup.prettify()[:1000])  # First 1000 chars for brevity
        
        # Try multiple possible selectors
        possible_selectors = [
            'article.post',
            '.post',
            '.blog-post',
            '.entry',
            'article',
            '.post-card'
        ]
        
        for selector in possible_selectors:
            posts_elements = soup.select(selector)
            if posts_elements:
                logger.info(f"Found posts using selector: {selector}")
                posts = []
                for post in posts_elements[:4]:
                    try:
                        # Try different title selectors
                        title_element = (
                            post.select_one('h1') or 
                            post.select_one('h2') or 
                            post.select_one('.post-title') or 
                            post.select_one('.title')
                        )
                        
                        # Try different link selectors
                        link_element = (
                            post.select_one('h1 a') or 
                            post.select_one('h2 a') or 
                            post.select_one('.post-title a') or 
                            post.select_one('.title a') or
                            post.select_one('a')
                        )
                        
                        if title_element and link_element:
                            title = title_element.text.strip()
                            url = link_element.get('href')
                            if not url.startswith('http'):
                                url = blog_url + url
                            posts.append({
                                'title': title,
                                'url': url
                            })
                            logger.info(f"Found post: {title} - {url}")
                    except Exception as e:
                        logger.error(f"Error processing post element: {str(e)}")
                
                if posts:
                    break
        
        if posts:
            return posts
        else:
            logger.error("No posts found with any selector")
            return []
            
    except Exception as e:
        logger.error(f"HTML scraping error: {str(e)}")
        return []

def update_readme():
    logger.info("Starting README update process")
    
    posts = get_blog_posts()
    
    if not posts:
        logger.error("No posts found to update")
        return
    
    logger.info(f"Found {len(posts)} posts to add to README")
    
    try:
        with open('README.md', 'r', encoding='utf-8') as file:
            content = file.read()
            logger.info("Successfully read README.md")
    except Exception as e:
        logger.error(f"Error reading README.md: {str(e)}")
        return
    
    # Create new blog posts list
    blog_posts_md = '\n'.join([
        f"- [{post['title']}]({post['url']})"
        for post in posts
    ])
    
    logger.info("Generated new blog posts markdown")
    logger.debug(f"New blog posts section:\n{blog_posts_md}")
    
    # Replace the existing blog posts section
    pattern = r'(<!-- BLOG-POST-LIST:START -->).*(<!-- BLOG-POST-LIST:END -->)'
    new_content = re.sub(
        pattern,
        f"<!-- BLOG-POST-LIST:START -->\n{blog_posts_md}\n<!-- BLOG-POST-LIST:END -->",
        content,
        flags=re.DOTALL
    )
    
    if new_content == content:
        logger.warning("No changes were made to the content")
    else:
        logger.info("Content was updated")
    
    try:
        with open('README.md', 'w', encoding='utf-8') as file:
            file.write(new_content)
            logger.info("Successfully wrote updated content to README.md")
    except Exception as e:
        logger.error(f"Error writing to README.md: {str(e)}")

if __name__ == '__main__':
    logger.info("Script started")
    update_readme()
    logger.info("Script finished")
