from typing import List, Dict
from datetime import datetime

def save_to_markdown(articles_data: List[Dict], filename: str = None) -> str:
    """
    Save article data to a markdown file
    
    Parameters:
    - articles_data: List of dictionaries containing article data with keys:
                     'title', 'link', 'published', 'summary'
    - filename: Optional filename, defaults to timestamped filename if None
    
    Returns:
    - The filename used to save the data
    """
    if filename is None:
        # Create a timestamped filename
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        filename = f"articles_{date_str}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('# Collected Articles Summary\n\n')
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Write each article
        for idx, article in enumerate(articles_data, 1):
            f.write(f"## {idx}. {article['title']}\n\n")
            f.write(f"- **Published:** {article['published']}\n")
            f.write(f"- **Link:** {article['link']}\n\n")
            
            # Write summary if available
            if 'summary' in article and article['summary']:
                f.write(f"### Summary:\n\n{article['summary']}\n\n")
            
            # Add separator between articles
            if idx < len(articles_data):
                f.write('---\n\n')
    
    return filename
