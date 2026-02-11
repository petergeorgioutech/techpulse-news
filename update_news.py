#!/usr/bin/env python3
"""
TechPulse News Updater
Fetches latest AI, dev tools, and tech industry news and regenerates the site.

Uses NewsAPI.org - Get your free API key at: https://newsapi.org/register
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from html import escape

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "index.html")
API_KEY_FILE = os.path.join(SCRIPT_DIR, ".newsapi_key")

# News categories with search queries
CATEGORIES = {
    "Artificial Intelligence": [
        "artificial intelligence",
        "OpenAI OR Anthropic OR DeepMind",
        "large language model OR LLM",
    ],
    "Developer Tools": [
        "developer tools OR IDE",
        "GitHub OR VS Code OR programming",
        "software development",
    ],
    "Tech Industry": [
        "tech industry",
        "Apple OR Google OR Microsoft OR Meta",
        "startup funding OR tech stocks",
    ],
}


def get_api_key():
    """Read API key from file or environment."""
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE) as f:
            return f.read().strip()
    return os.environ.get("NEWSAPI_KEY", "")


def fetch_news(query, api_key, page_size=3):
    """Fetch news from NewsAPI."""
    params = urllib.parse.urlencode({
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": api_key,
    })
    url = f"https://newsapi.org/v2/everything?{params}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TechPulse/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("articles", [])
    except Exception as e:
        print(f"Error fetching news for '{query}': {e}")
        return []


def fetch_category_news(category_queries, api_key):
    """Fetch news for a category using multiple queries."""
    all_articles = []
    seen_urls = set()
    
    for query in category_queries:
        articles = fetch_news(query, api_key, page_size=4)
        for article in articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_articles.append(article)
    
    # Sort by date and return top 6
    all_articles.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return all_articles[:6]


def format_date(iso_date):
    """Format ISO date to readable string."""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                return "Just now"
            return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%b %d")
    except:
        return ""


def generate_story_html(article, featured=False):
    """Generate HTML for a single story card."""
    title = escape(article.get("title", "Untitled") or "Untitled")
    # Clean up titles that end with " - Source Name"
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
    
    url = escape(article.get("url", "#"))
    source = escape(article.get("source", {}).get("name", "Unknown"))
    date = format_date(article.get("publishedAt", ""))
    description = escape(article.get("description", "") or "")
    
    # Truncate description
    if len(description) > 150:
        description = description[:147] + "..."
    
    css_class = "story featured" if featured else "story"
    
    return f'''                <a href="{url}" class="{css_class}" target="_blank">
                    <h3 class="story-title">{title}</h3>
                    <div class="story-meta">
                        <span class="story-source">{source}</span>
                        <span>{date}</span>
                    </div>
                    <p class="story-excerpt">{description}</p>
                </a>'''


def generate_html(news_by_category):
    """Generate the complete HTML page."""
    today = datetime.now().strftime("%B %d, %Y")
    
    sections_html = ""
    for category, articles in news_by_category.items():
        if not articles:
            continue
        
        stories_html = "\n".join(
            generate_story_html(article, featured=(i == 0))
            for i, article in enumerate(articles)
        )
        
        sections_html += f'''
        <section class="section">
            <h2 class="section-title">{category}</h2>
            <div class="stories">
{stories_html}
            </div>
        </section>
'''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Pulse | AI • Dev Tools • Industry</title>
    <style>
        :root {{
            --bg: #fafafa;
            --card: #ffffff;
            --text: #1a1a1a;
            --muted: #666;
            --accent: #2563eb;
            --border: #e5e5e5;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        
        header {{
            background: var(--card);
            border-bottom: 1px solid var(--border);
            padding: 1.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
            text-decoration: none;
        }}
        
        .logo span {{
            color: var(--accent);
        }}
        
        .date {{
            color: var(--muted);
            font-size: 0.875rem;
        }}
        
        main {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .section {{
            margin-bottom: 3rem;
        }}
        
        .section-title {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--accent);
            margin-bottom: 1rem;
            font-weight: 600;
        }}
        
        .stories {{
            display: grid;
            gap: 1rem;
        }}
        
        .story {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            text-decoration: none;
            color: inherit;
            transition: box-shadow 0.2s, transform 0.2s;
        }}
        
        .story:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transform: translateY(-2px);
        }}
        
        .story-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text);
        }}
        
        .story-meta {{
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
            color: var(--muted);
        }}
        
        .story-source {{
            font-weight: 500;
        }}
        
        .story-excerpt {{
            margin-top: 0.75rem;
            font-size: 0.9rem;
            color: var(--muted);
        }}
        
        .featured {{
            grid-column: 1 / -1;
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
        }}
        
        .featured .story-title {{
            color: white;
            font-size: 1.4rem;
        }}
        
        .featured .story-meta,
        .featured .story-excerpt {{
            color: rgba(255,255,255,0.85);
        }}
        
        @media (min-width: 768px) {{
            .stories {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (min-width: 1024px) {{
            .stories {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
        
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--muted);
            font-size: 0.875rem;
            border-top: 1px solid var(--border);
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <a href="#" class="logo">Tech<span>Pulse</span></a>
            <span class="date">{today}</span>
        </div>
    </header>
    
    <main>{sections_html}
    </main>
    
    <footer>
        <p>Curated tech news • Updated {today}</p>
    </footer>
</body>
</html>
'''


def main():
    api_key = get_api_key()
    
    if not api_key:
        print("Error: No API key found.")
        print(f"Create a file at: {API_KEY_FILE}")
        print("Or set NEWSAPI_KEY environment variable.")
        print("Get a free key at: https://newsapi.org/register")
        return 1
    
    print(f"Fetching news at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    news_by_category = {}
    for category, queries in CATEGORIES.items():
        print(f"  Fetching {category}...")
        news_by_category[category] = fetch_category_news(queries, api_key)
    
    total = sum(len(articles) for articles in news_by_category.values())
    print(f"  Found {total} articles")
    
    html = generate_html(news_by_category)
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    
    print(f"Updated: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    exit(main())
