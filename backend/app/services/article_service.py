"""Article generation and HTML rendering service."""
import re
from typing import Optional, Dict, Any
from app.services.llm_service import generate_article, generate_seo_metadata, regenerate_article


def markdown_to_html(text: str) -> str:
    """
    Convert markdown formatting to HTML.
    Handles bold (**text**), lists (* item), and basic formatting.
    """
    if not text:
        return ""
    
    # First convert bold text **text** to <strong>text</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Split text into lines for processing
    lines = text.split('\n')
    html_parts = []
    in_list = False
    current_paragraph = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if line is a list item (* item or - item)
        # But not if it starts with ** (already converted to bold)
        list_match = re.match(r'^[\*\-\+]\s+(.+)$', stripped)
        
        if list_match and not stripped.startswith('<strong>'):
            # This is a list item
            if not in_list:
                # Close any open paragraph first
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text:
                        html_parts.append(f'<p>{para_text}</p>')
                    current_paragraph = []
                html_parts.append('<ul>')
                in_list = True
            
            # Add list item (content may contain bold tags)
            item_content = list_match.group(1).strip()
            html_parts.append(f'<li>{item_content}</li>')
        else:
            # This is not a list item
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            
            if stripped:
                current_paragraph.append(stripped)
            else:
                # Empty line - close current paragraph
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text:
                        html_parts.append(f'<p>{para_text}</p>')
                    current_paragraph = []
        
        i += 1
    
    # Close any remaining structures
    if in_list:
        html_parts.append('</ul>')
    if current_paragraph:
        para_text = ' '.join(current_paragraph).strip()
        if para_text:
            html_parts.append(f'<p>{para_text}</p>')
    
    result = '\n'.join(html_parts)
    
    # If no HTML was generated, wrap entire text in paragraph
    if not result or ('<' not in result):
        # Split by double newlines for paragraphs
        paragraphs = text.split('\n\n')
        result = '\n'.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
    
    return result


def create_html_document(
    article_data: Dict[str, Any],
    seo_metadata: Dict[str, Any]
) -> str:
    """
    Generate a complete HTML document from article data and SEO metadata.
    
    Args:
        article_data: Article content dictionary
        seo_metadata: SEO metadata dictionary
        
    Returns:
        Complete HTML document as string
    """
    title = article_data.get("title", "Article")
    content = article_data.get("content", "")
    sections = article_data.get("sections", [])
    links = article_data.get("links", [])
    sources = article_data.get("sources", [])
    
    # Build sections HTML
    sections_html = ""
    if sections:
        for section in sections:
            heading = section.get("heading", "")
            section_content = section.get("content", "")
            section_links = section.get("links", [])
            
            sections_html += f'<section class="article-section">\n'
            if heading:
                sections_html += f'  <h2>{heading}</h2>\n'
            if section_content:
                # Convert markdown to HTML
                section_html_content = markdown_to_html(section_content)
                sections_html += f'  <div class="section-content">{section_html_content}</div>\n'
            if section_links:
                # Filter valid links
                valid_section_links = [link for link in section_links if link and isinstance(link, str) and link.strip()]
                if valid_section_links:
                    sections_html += '  <div class="section-links">\n'
                    sections_html += '    <h3>References:</h3>\n'
                    sections_html += '    <ul>\n'
                    for link in valid_section_links:
                        clean_link = link.strip()
                        if clean_link.startswith('http://') or clean_link.startswith('https://'):
                            sections_html += f'      <li><a href="{clean_link}" target="_blank" rel="noopener noreferrer">{clean_link}</a></li>\n'
                        else:
                            if clean_link:
                                sections_html += f'      <li><a href="https://{clean_link}" target="_blank" rel="noopener noreferrer">{clean_link}</a></li>\n'
                    sections_html += '    </ul>\n'
                    sections_html += '  </div>\n'
            sections_html += '</section>\n'
    
    # Build main links HTML - always show if links exist
    links_html = ""
    if links:
        # Filter out empty or invalid links
        valid_links = [link for link in links if link and isinstance(link, str) and link.strip()]
        if valid_links:
            links_html = '<div class="article-links">\n'
            links_html += '  <h3>Related Links:</h3>\n'
            links_html += '  <ul>\n'
            for link in valid_links:
                # Clean and validate link
                clean_link = link.strip()
                if clean_link.startswith('http://') or clean_link.startswith('https://'):
                    links_html += f'    <li><a href="{clean_link}" target="_blank" rel="noopener noreferrer">{clean_link}</a></li>\n'
                else:
                    # If not a full URL, try to make it one
                    if clean_link:
                        links_html += f'    <li><a href="https://{clean_link}" target="_blank" rel="noopener noreferrer">{clean_link}</a></li>\n'
            links_html += '  </ul>\n'
            links_html += '</div>\n'
    
    # Build sources HTML - display actual sources used by LLM
    sources_html = ""
    if sources:
        # Filter valid sources
        valid_sources = []
        for source in sources:
            if isinstance(source, dict):
                source_title = source.get("title", "") or source.get("name", "")
                source_url = source.get("url", "")
                source_desc = source.get("description", "")
                if source_title or source_url:
                    valid_sources.append({
                        "title": source_title,
                        "url": source_url,
                        "description": source_desc
                    })
            elif isinstance(source, str):
                # Handle simple string sources
                valid_sources.append({
                    "title": source,
                    "url": "",
                    "description": ""
                })
        
        if valid_sources:
            sources_html = '<div class="article-sources">\n'
            sources_html += '  <h3>Sources:</h3>\n'
            sources_html += '  <ul class="sources-list">\n'
            for source in valid_sources:
                source_title = source.get("title", "").strip()
                source_url = source.get("url", "").strip()
                source_desc = source.get("description", "").strip()
                
                sources_html += '    <li class="source-item">\n'
                if source_url:
                    if source_url.startswith('http://') or source_url.startswith('https://'):
                        sources_html += f'      <strong><a href="{source_url}" target="_blank" rel="noopener noreferrer">{source_title or source_url}</a></strong>\n'
                    else:
                        sources_html += f'      <strong><a href="https://{source_url}" target="_blank" rel="noopener noreferrer">{source_title or source_url}</a></strong>\n'
                else:
                    sources_html += f'      <strong>{source_title}</strong>\n'
                
                if source_desc:
                    sources_html += f'      <p class="source-description">{source_desc}</p>\n'
                sources_html += '    </li>\n'
            sources_html += '  </ul>\n'
            sources_html += '</div>\n'
    
    # SEO metadata
    meta_title = seo_metadata.get("title", title)
    meta_description = seo_metadata.get("description", "")
    meta_keywords = ", ".join(seo_metadata.get("keywords", []))
    og_title = seo_metadata.get("og_title", title)
    og_description = seo_metadata.get("og_description", meta_description)
    og_type = seo_metadata.get("og_type", "article")
    
    # Generate HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- SEO Meta Tags -->
    <title>{meta_title}</title>
    <meta name="description" content="{meta_description}">
    {f'<meta name="keywords" content="{meta_keywords}">' if meta_keywords else ''}
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_description}">
    <meta property="og:type" content="{og_type}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="{seo_metadata.get("twitter_card", "summary_large_image")}">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_description}">
    
    {f'<link rel="canonical" href="{seo_metadata.get("canonical_url")}">' if seo_metadata.get("canonical_url") else ''}
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h2 {{
            font-size: 1.8em;
            margin-top: 30px;
            margin-bottom: 15px;
            color: #34495e;
        }}
        
        h3 {{
            font-size: 1.3em;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #555;
        }}
        
        .article-section {{
            margin-bottom: 30px;
        }}
        
        .article-section p,
        .section-content p {{
            margin-bottom: 15px;
            text-align: justify;
            font-size: 1.1em;
        }}
        
        .section-content {{
            margin-bottom: 15px;
        }}
        
        .section-content ul {{
            margin-left: 20px;
            margin-bottom: 15px;
            list-style-type: disc;
        }}
        
        .section-content li {{
            margin-bottom: 8px;
            line-height: 1.6;
        }}
        
        .section-content strong {{
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .section-content em {{
            font-style: italic;
        }}
        
        .article-links, .section-links {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }}
        
        .article-links ul, .section-links ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .article-links li, .section-links li {{
            margin-bottom: 8px;
        }}
        
        .article-links a, .section-links a {{
            color: #3498db;
            text-decoration: none;
            word-break: break-all;
        }}
        
        .article-links a:hover, .section-links a:hover {{
            text-decoration: underline;
        }}
        
        .article-sources {{
            margin-top: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-left: 4px solid #27ae60;
            border-radius: 4px;
        }}
        
        .article-sources h3 {{
            color: #27ae60;
            margin-top: 0;
            margin-bottom: 15px;
        }}
        
        .sources-list {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .source-item {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #ddd;
        }}
        
        .source-item:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .source-item strong {{
            display: block;
            margin-bottom: 5px;
            color: #2c3e50;
        }}
        
        .source-item a {{
            color: #27ae60;
            text-decoration: none;
        }}
        
        .source-item a:hover {{
            text-decoration: underline;
        }}
        
        .source-description {{
            margin: 5px 0 0 0;
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }}
        
        .summary {{
            font-style: italic;
            color: #666;
            margin-bottom: 30px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #95a5a6;
        }}
        
        @media (max-width: 600px) {{
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <article>
            <h1>{title}</h1>
            
            {f'<div class="summary">{markdown_to_html(article_data.get("summary", ""))}</div>' if article_data.get("summary") else ''}
            
            {f'<div class="article-content">{markdown_to_html(content)}</div>' if content and not sections else ''}
            
            {sections_html}
            
            {links_html}
            
            {sources_html}
        </article>
    </div>
</body>
</html>"""
    
    return html


def generate_article_with_metadata(
    query: str,
    url: Optional[str] = None
) -> tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Generate a complete article with SEO metadata and HTML.
    
    Args:
        query: Article query/topic
        url: Optional URL for context
        
    Returns:
        Tuple of (article_json, seo_metadata_json, html_content)
    """
    # Generate article
    article_data = generate_article(query, url)
    
    # Generate SEO metadata
    seo_metadata = generate_seo_metadata(article_data)
    
    # Generate HTML
    html_content = create_html_document(article_data, seo_metadata)
    
    return article_data, seo_metadata, html_content


def regenerate_article_with_metadata(
    article_data: Dict[str, Any],
    prompt: str
) -> tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Regenerate an article with new prompt and update metadata/HTML.
    
    Args:
        article_data: Existing article data
        prompt: Modification prompt
        
    Returns:
        Tuple of (updated_article_json, updated_seo_metadata_json, updated_html_content)
    """
    # Regenerate article
    updated_article = regenerate_article(article_data, prompt)
    
    # Generate new SEO metadata
    updated_seo_metadata = generate_seo_metadata(updated_article)
    
    # Generate new HTML
    updated_html = create_html_document(updated_article, updated_seo_metadata)
    
    return updated_article, updated_seo_metadata, updated_html
