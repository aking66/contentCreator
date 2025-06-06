# List of RSS feed URLs for technology news
RSS_FEEDS = [
    # Arabic Tech News
    "https://aitnews.com/feed",
    "https://www.tech-wd.com/wd/feed",
    "https://www.unlimit-tech.com/feed",
    "https://www.electrony.net/feed/",
    "https://menatech.net/feed/",
    "http://feeds.feedburner.com/arabhardware",
    "https://www.aljazeera.net/aljazeera/rss",
    
    # International Tech News
    "http://feeds.feedburner.com/TechCrunch",
    "https://www.theverge.com/rss/index.xml",
    "https://www.engadget.com/rss.xml",
    "https://www.cnet.com/rss/news/",
    "https://www.wired.com/feed/rss",
    "http://feeds.arstechnica.com/arstechnica/index",
    "https://gizmodo.com/rss",
    "https://www.zdnet.com/news/rss.xml",
    "https://www.techradar.com/rss",
    "https://mashable.com/feeds/rss/tech",
    
    # General News with Tech Sections
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://edition.cnn.com/rss/edition_technology.rss",
    
    # Reddit Tech Communities
    "https://www.reddit.com/r/technology/.rss",
    "https://www.reddit.com/r/technews/.rss"
]

def get_feeds_by_category(category=None):
    """
    Get RSS feeds filtered by category
    
    Args:
        category (str, optional): Filter feeds by category. 
                               Options: 'arabic', 'international', 'general', 'reddit'
                               
    Returns:
        list: List of RSS feed URLs
    """
    categories = {
        'arabic': RSS_FEEDS[0:7],
        'international': RSS_FEEDS[7:18],
        'general': RSS_FEEDS[18:20],
        'reddit': RSS_FEEDS[20:22]
    }
    
    if category and category.lower() in categories:
        return categories[category.lower()]
    return RSS_FEEDS
