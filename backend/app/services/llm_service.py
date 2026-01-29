"""Gemini API integration service."""
import json
import re
import google.generativeai as genai
from typing import Optional, Dict, Any
from app.config import settings

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Google Search tool for grounding
# Using dictionary format that should work with SDK
# If this fails, the code will fall back to generating without grounding
GOOGLE_SEARCH_TOOL = {"google_search": {}}


def generate_article(
    query: str,
    url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an article using Gemini API with Google Search grounding.
    
    Args:
        query: The article query/topic
        url: Optional URL for context
        
    Returns:
        Dictionary containing article structure (title, content, sections, links)
    """
    # Initialize the model - using gemini-2.5-flash which supports Search grounding
    # See: https://ai.google.dev/gemini-api/docs/models
    # gemini-2.5-flash supports Search grounding and is cost-effective
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    
    # Build the prompt - natural handling of year context
    # Check if query mentions a specific year
    year_match = re.search(r'\b(20[0-9][0-9])\b', query)
    year_context = ""
    if year_match:
        year = year_match.group(1)
        year_context = f"\n\nFocus on events and information from {year}."
    
    prompt = f"""Write a comprehensive, well-structured article about: {query}
{year_context}

IMPORTANT INSTRUCTIONS:
- If a specific year is mentioned in the query, focus on events from that time period
- If no year is specified, prioritize the most recent information available, but if only historical information exists, use that
- Use factual information from your knowledge base
- Ensure accuracy and clarity in all dates and events mentioned

Requirements:
1. Create a clear, engaging title
2. Write informative content in 3-5 logical sections
3. Use factual information from your knowledge base, prioritizing the most recent
4. Format with headings and paragraphs
5. Use markdown formatting: **bold** for key terms, names, and important concepts
6. For lists, use proper markdown format with each item on a new line starting with *
7. Ensure all dates and events are accurate and correspond to the time period mentioned

Return the article in this JSON format:
{{
    "title": "Article Title",
    "content": "Brief introduction paragraph",
    "sections": [
        {{
            "heading": "Section Heading",
            "content": "Section content with **bold** for important terms. For lists, format like this:\n* First bullet point\n* Second bullet point\n* Third bullet point",
            "links": []
        }}
    ],
    "links": [],
    "sources": [
        {{
            "title": "Source Title or Publication Name",
            "url": "https://example.com/article",
            "description": "Brief description of what information was gathered from this source"
        }}
    ],
    "summary": "Brief summary"
}}

IMPORTANT: Include actual sources in the "sources" array. These should be real sources from your knowledge base that you used to gather information for this article. Include:
- News articles, publications, or websites
- Official statements or documents
- Research papers or reports
- Any credible sources that informed your article content
- If you don't have specific URLs, provide the publication name and description"""

    # Add URL context if provided
    if url:
        prompt += f"\n\nUse this URL as additional context: {url}"
    
    try:
        # Generate content - temporarily disable Google Search grounding to avoid timeouts
        # Google Search grounding can cause timeouts, so we'll generate without it for now
        # To enable: upgrade SDK and uncomment the tools parameter
        # See: https://ai.google.dev/gemini-api/docs/google-search
        response = model.generate_content(prompt)
        
        # Note: Google Search grounding disabled to prevent timeouts
        # Uncomment below to enable (requires SDK upgrade):
        # try:
        #     response = model.generate_content(
        #         prompt,
        #         tools=[GOOGLE_SEARCH_TOOL],
        #         request_options={"timeout": 120}  # 2 minute timeout
        #     )
        # except (TypeError, ValueError, AttributeError) as e:
        #     response = model.generate_content(prompt)
        
        # Extract text from response
        response_text = response.text
        
        # Extract grounding metadata (citations and sources) if available
        # Currently disabled since Google Search grounding is disabled
        grounding_links = []
        # Uncomment when Google Search grounding is enabled:
        # try:
        #     if hasattr(response, 'candidates') and response.candidates:
        #         candidate = response.candidates[0]
        #         if hasattr(candidate, 'grounding_metadata'):
        #             metadata = candidate.grounding_metadata
        #             if hasattr(metadata, 'grounding_chunks'):
        #                 for chunk in metadata.grounding_chunks:
        #                     if hasattr(chunk, 'web') and hasattr(chunk.web, 'uri'):
        #                         grounding_links.append(chunk.web.uri)
        # except Exception:
        #     pass
        
        # Try to parse JSON from the response
        # The response might have markdown code blocks, so we need to extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            json_str = response_text.strip()
        
        # Parse JSON
        article_data = json.loads(json_str)
        
        # Add grounding links if available
        if grounding_links:
            # Merge grounding links with any existing links
            existing_links = article_data.get('links', [])
            # Combine and deduplicate
            all_links = list(set(existing_links + grounding_links))
            article_data['links'] = all_links
            # Also add to sections if they exist
            if 'sections' in article_data:
                for section in article_data['sections']:
                    section_links = section.get('links', [])
                    section['links'] = list(set(section_links + grounding_links))
        
        return article_data
        
    except json.JSONDecodeError as e:
        # If JSON parsing fails, create a structured response from text
        return {
            "title": query,
            "content": response_text if 'response_text' in locals() else "Error generating article",
            "sections": [],
            "links": [],
            "summary": "Article generated but could not parse structured format"
        }
    except Exception as e:
        raise Exception(f"Error generating article: {str(e)}")


def generate_seo_metadata(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate SEO metadata for an article.
    
    Args:
        article_data: The article data dictionary
        
    Returns:
        Dictionary containing SEO metadata
    """
    # Use gemini-2.5-flash which supports Search grounding
    # See: https://ai.google.dev/gemini-api/docs/models
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    
    prompt = f"""Based on this article, generate comprehensive SEO metadata:

Title: {article_data.get('title', '')}
Content: {article_data.get('content', '')[:1000]}...

Generate SEO metadata in the following JSON format:
{{
    "title": "SEO optimized title (max 60 characters)",
    "description": "Meta description (max 160 characters)",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "og_title": "Open Graph title",
    "og_description": "Open Graph description",
    "og_type": "article",
    "twitter_card": "summary_large_image",
    "canonical_url": "",
    "author": ""
}}"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            json_str = response_text.strip()
        
        seo_data = json.loads(json_str)
        return seo_data
        
    except json.JSONDecodeError:
        # Fallback SEO metadata
        title = article_data.get('title', 'Article')
        content = article_data.get('content', '')
        summary = article_data.get('summary', content[:150])
        
        return {
            "title": title[:60],
            "description": summary[:160],
            "keywords": [],
            "og_title": title,
            "og_description": summary[:200],
            "og_type": "article",
            "twitter_card": "summary_large_image",
            "canonical_url": "",
            "author": ""
        }
    except Exception as e:
        raise Exception(f"Error generating SEO metadata: {str(e)}")


def regenerate_article(
    article_data: Dict[str, Any],
    prompt: str
) -> Dict[str, Any]:
    """
    Regenerate/modify an existing article based on a prompt.
    
    Args:
        article_data: The existing article data
        prompt: The modification prompt (e.g., "Make this more appealing to Gen Z")
        
    Returns:
        Updated article data dictionary
    """
    # Use gemini-2.5-flash which supports Search grounding
    # See: https://ai.google.dev/gemini-api/docs/models
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    
    existing_article = json.dumps(article_data, indent=2)
    
    regeneration_prompt = f"""Modify this existing article based on the following instruction:

Instruction: {prompt}

Existing Article:
{existing_article}

Please modify the article according to the instruction while maintaining its core information and structure. Return the updated article in the same JSON format as the original."""
    
    try:
        response = model.generate_content(regeneration_prompt)
        response_text = response.text
        
        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            json_str = response_text.strip()
        
        updated_article = json.loads(json_str)
        return updated_article
        
    except json.JSONDecodeError:
        # If parsing fails, return original with note
        article_data["regeneration_note"] = "Regeneration attempted but could not parse response"
        return article_data
    except Exception as e:
        raise Exception(f"Error regenerating article: {str(e)}")
