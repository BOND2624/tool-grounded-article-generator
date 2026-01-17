"""
HTML rendering module for converting Article JSON to HTML
"""

from typing import Dict, Any


def render_article_html(article_json: Dict[str, Any], seo_json: Dict[str, Any]) -> str:
    """
    Render Article JSON and SEO metadata into a complete HTML document
    
    Args:
        article_json: Article data structure
        seo_json: SEO metadata structure
    
    Returns:
        Complete HTML document as string
    """
    title = article_json.get("title", "Generated Article")
    meta_title = seo_json.get("meta_title", title)
    meta_description = seo_json.get("meta_description", "")
    keywords = seo_json.get("keywords", [])
    canonical_url = seo_json.get("canonical_url", "")
    
    # Build meta keywords string
    keywords_str = ", ".join(keywords) if keywords else ""
    
    # Build article sections HTML
    sections_html = ""
    sections = article_json.get("sections", [])
    
    for section in sections:
        heading = section.get("heading", "")
        content = section.get("content", "")
        sources = section.get("sources", [])
        
        # Convert content to paragraphs (split by double newlines)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        content_html = "\n      ".join([f"<p>{escape_html(p)}</p>" for p in paragraphs])
        
        # Build sources HTML
        sources_html = ""
        if sources:
            sources_list = "\n        ".join([
                f'<li><a href="{escape_html(src)}" target="_blank" rel="noopener noreferrer">{escape_html(src)}</a></li>'
                for src in sources
            ])
            sources_html = f"""
      <div class="sources">
        <h4>Sources:</h4>
        <ul>
          {sources_list}
        </ul>
      </div>"""
        
        sections_html += f"""
    <section>
      <h2>{escape_html(heading)}</h2>
      {content_html}
      {sources_html}
    </section>"""
    
    # Build summary HTML
    summary = article_json.get("summary", "")
    summary_html = ""
    if summary:
        summary_html = f"""
    <div class="summary">
      <h3>Summary</h3>
      <p>{escape_html(summary)}</p>
    </div>"""
    
    # Complete HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(meta_title)}</title>
  <meta name="description" content="{escape_html(meta_description)}">
  {f'<meta name="keywords" content="{escape_html(keywords_str)}">' if keywords_str else ''}
  {f'<link rel="canonical" href="{escape_html(canonical_url)}">' if canonical_url else ''}
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      color: #333;
    }}
    h1 {{
      color: #2c3e50;
      border-bottom: 3px solid #3498db;
      padding-bottom: 10px;
    }}
    h2 {{
      color: #34495e;
      margin-top: 30px;
      margin-bottom: 15px;
    }}
    h3 {{
      color: #555;
      margin-top: 25px;
    }}
    h4 {{
      color: #666;
      font-size: 1em;
      margin-top: 20px;
      margin-bottom: 10px;
    }}
    p {{
      margin-bottom: 15px;
      text-align: justify;
    }}
    .summary {{
      background-color: #f8f9fa;
      padding: 20px;
      border-left: 4px solid #3498db;
      margin: 30px 0;
    }}
    .sources {{
      margin-top: 20px;
      padding: 15px;
      background-color: #f1f3f5;
      border-radius: 5px;
    }}
    .sources ul {{
      list-style-type: none;
      padding-left: 0;
    }}
    .sources li {{
      margin-bottom: 8px;
    }}
    .sources a {{
      color: #3498db;
      text-decoration: none;
    }}
    .sources a:hover {{
      text-decoration: underline;
    }}
    section {{
      margin-bottom: 40px;
    }}
  </style>
</head>
<body>
  <article>
    <h1>{escape_html(title)}</h1>
    {summary_html}
    {sections_html}
  </article>
</body>
</html>"""
    
    return html


def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))
