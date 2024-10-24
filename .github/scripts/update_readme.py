import os
import feedparser
import requests
from bs4 import BeautifulSoup
import re

def get_blog_posts():
    """
    Fetches blog posts from your website. Modify this function based on your website's structure.
    This example assumes your blog has an RSS feed or similar structure.
    """
    blog_url = os.getenv('BLOG_URL', 'https://munwalker.com')
    
    try:
        # First attempt: Try RSS feed
        feed_url = f"{blog_url}/feed"
        feed = feedparser.parse(feed_url)
        
        if feed.entries:
            return [
                {
                    'title': entry.title,
                    'url': entry.link
                }
                for entry in feed.entries[:4]  # Get latest 4 posts
            ]
            
    except Exception:
        pass
    
    try:
        # Second attempt: Scrape HTML
        response = requests.get(blog_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Modify these selectors based on your website's HTML structure
        posts = soup.select('article.post')[:4]  # Adjust selector as needed
        
        return [
            {
                'title': post.select_one('h2').text.strip(),
                'url': post.select_one('a')['href']
            }
            for post in posts
        ]
        
    except Exception as e:
        print(f"Error fetching blog posts: {e}")
        return []

def update_readme():
    posts = get_blog_posts()
    
    if not posts:
        return
    
    with open('README.md', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Create new blog posts list
    blog_posts_md = '\n'.join([
        f"- [{post['title']}]({post['url']})"
        for post in posts
    ])
    
    # Replace the existing blog posts section
    pattern = r'(<!-- BLOG-POST-LIST:START -->).*(<!-- BLOG-POST-LIST:END -->)'
    new_content = re.sub(
        pattern,
        f"<!-- BLOG-POST-LIST:START -->\n{blog_posts_md}\n<!-- BLOG-POST-LIST:END -->",
        content,
        flags=re.DOTALL
    )
    
    with open('README.md', 'w', encoding='utf-8') as file:
        file.write(new_content)

if __name__ == '__main__':
    update_readme()
