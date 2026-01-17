"""
Gemini API service for article generation with Google Search grounding
"""

from google import genai
from google.genai import types
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, Dict, Any
import httpx


class GeminiSettings(BaseSettings):
    """Gemini API settings"""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"  # Free tier model: gemini-2.5-flash or gemini-2.5-flash-lite
    openrouter_api_key: str = ""  # OpenRouter API key
    openrouter_model: str = "xiaomi/mimo-v2-flash:free"  # OpenRouter model for fallback
    
    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = GeminiSettings()

# Initialize Gemini client
client = None
if settings.gemini_api_key:
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        print(f"Gemini client initialized with model: {settings.gemini_model}")
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini client: {e}")
else:
    print("Warning: GEMINI_API_KEY not set in environment variables")

# Log OpenRouter configuration status
if settings.openrouter_api_key:
    print(f"OpenRouter fallback configured with model: {settings.openrouter_model}")
else:
    print("Warning: OPENROUTER_API_KEY not set in environment variables (fallback will fail if Gemini quota is exhausted)")


def strip_html_tags(text: str) -> str:
    """
    Remove HTML tags from text, preserving the text content
    """
    if not text:
        return ""
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def repair_json_missing_commas(json_str: str) -> str:
    """
    Repair JSON by adding missing commas between array elements and object properties.
    Fast, targeted fix for common JSON errors.
    """
    import re
    # Fix missing commas between closing and opening brackets/braces
    json_str = re.sub(r'\]\s*\[', '], [', json_str)
    json_str = re.sub(r'}\s*\{', '}, {', json_str)
    
    # Fix missing commas between string values and object keys
    # Pattern: "value" "key": -> "value", "key":
    json_str = re.sub(r'"\s*"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:', r'", "\1":', json_str)
    
    # Fix missing commas between closing brackets/braces and values
    # Pattern: ] "value" or } "value" -> ], "value" or }, "value"
    json_str = re.sub(r'([\]}])\s*"', r'\1, "', json_str)
    json_str = re.sub(r'([\]}])\s*\{', r'\1, {', json_str)
    json_str = re.sub(r'([\]}])\s*\[', r'\1, [', json_str)
    
    # Remove trailing commas (standard fix)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Remove double commas
    json_str = re.sub(r',\s*,', ',', json_str)
    
    return json_str


async def resolve_redirect_url(url: str) -> str:
    """
    Resolve redirect URLs to their final destination
    Returns the final URL or the original URL if resolution fails
    """
    if not url or 'vertexaisearch.cloud.google.com/grounding-api-redirect' not in url:
        return url
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as http_client:
            # Use GET request with redirect following
            response = await http_client.get(url, follow_redirects=True)
            final_url = str(response.url)
            
            # If we got a different URL and it's not another redirect, return it
            if final_url != url and 'grounding-api-redirect' not in final_url:
                return final_url
            elif final_url == url:
                # If URL didn't change, the redirect might be in the Location header
                if 'location' in response.headers:
                    location = response.headers['location']
                    if location and 'grounding-api-redirect' not in location:
                        return location
    except (httpx.TimeoutException, Exception):
        # Silently fail - return original URL
        pass
    
    return url


async def generate_article_with_openrouter(
    prompt: str,
    reference_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an article using OpenRouter API as fallback
    """
    if not settings.openrouter_api_key:
        raise Exception(
            "OpenRouter API key not configured. Please set OPENROUTER_API_KEY in backend/.env file."
        )
    
    # Build the system prompt (same as Gemini)
    system_prompt = """You are an expert article writer. Generate a high-quality, structured article based on the user's prompt.

The article should be well-researched, accurate, and include proper citations from web sources.

CRITICAL FORMATTING RULES:
- Write content in PLAIN TEXT only. Do NOT use HTML tags like <ul>, <li>, <p>, <div>, <strong>, <em>, etc.
- Use plain text formatting: use line breaks for paragraphs, use bullet points with "-" or "*" for lists.
- For emphasis, use markdown-style formatting: **bold** for bold text and *italic* for italic text.
- NEVER include HTML tags in the content field. Only plain text is allowed.

CRITICAL: When listing sources, you MUST include the actual, direct URLs to the web pages you found. Do NOT include redirect URLs or tracking URLs. Only include the final destination URLs (e.g., https://example.com/article, not redirect URLs).

Return your response as a JSON object with the following structure:
{
  "title": "Article Title",
  "sections": [
    {
      "heading": "Section Heading",
      "content": "Section content with detailed information in plain text. Use line breaks for paragraphs. Use - or * for bullet points. Use **text** for bold and *text* for italic.",
      "sources": ["https://actual-website.com/article", "https://another-site.com/page"]
    }
  ],
  "summary": "Brief summary of the article"
}

Also generate SEO metadata as a separate JSON object with these exact fields:
{
  "meta_title": "SEO optimized title (max 60 characters)",
  "meta_description": "SEO optimized description (max 160 characters)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "canonical_url": "https://example.com/article"
}

IMPORTANT: 
- Make sure to complete the entire article. Do not cut off mid-sentence. Generate complete, well-structured content.
- Write ALL content in PLAIN TEXT format. NO HTML tags allowed in the content field.
- In the SOURCES section, list the actual, direct URLs to the web pages you found. These should be the final destination URLs, not redirect or tracking URLs.

Format your response as:
ARTICLE_JSON:
{article json here}

SEO_JSON:
{seo json here}

SOURCES:
- https://actual-website.com/article
- https://another-site.com/page
"""
    
    # Build the user prompt
    if reference_url:
        user_prompt = f"""Reference URL: {reference_url}

User Prompt: {prompt}

Please generate an article based on the above prompt, using the reference URL as additional context."""
    else:
        user_prompt = prompt
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            response = await http_client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/your-repo",  # Optional: for tracking
                },
                json={
                    "model": settings.openrouter_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "max_tokens": 8192
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract content from OpenRouter response
            choices = result.get("choices", [])
            if not choices:
                raise Exception("OpenRouter returned no choices")
            
            content = choices[0].get("message", {}).get("content", "")
            
            if not content:
                raise Exception("OpenRouter returned empty response")
            
            print(f"OpenRouter API call successful, response length: {len(content)} characters")
            
            # Parse the response (same as Gemini)
            article_json, seo_json, extracted_sources = parse_gemini_response(content)
            
            # Extract URLs from content
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
            found_urls = re.findall(url_pattern, content)
            actual_urls_from_content = []
            for url in found_urls:
                if 'grounding-api-redirect' not in url and url not in actual_urls_from_content:
                    if len(url) < 200 and '.' in url.split('//')[-1].split('/')[0]:
                        actual_urls_from_content.append(url)
            
            # Combine sources
            all_sources = list(set(extracted_sources + actual_urls_from_content))
            all_sources = [url for url in all_sources if 'grounding-api-redirect' not in url]
            
            # Update sections' sources
            for section in article_json.get("sections", []):
                section_sources = section.get("sources", [])
                updated_sources = []
                for src in section_sources:
                    if 'grounding-api-redirect' not in src:
                        if src not in updated_sources:
                            updated_sources.append(src)
                section["sources"] = updated_sources
            
            return {
                "article_json": article_json,
                "seo_json": seo_json,
                "sources": all_sources
            }
            
    except httpx.TimeoutException:
        raise Exception("OpenRouter request timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        error_text = e.response.text if hasattr(e.response, 'text') else str(e)
        if e.response.status_code == 401:
            raise Exception("OpenRouter API key is invalid. Please check your OPENROUTER_API_KEY in .env file.")
        elif e.response.status_code == 429:
            raise Exception("OpenRouter rate limit exceeded. Please try again later.")
        raise Exception(f"OpenRouter API error: {e.response.status_code} - {error_text}")
    except Exception as e:
        raise Exception(f"Error generating article with OpenRouter: {str(e)}")


async def generate_article(
    prompt: str,
    reference_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an article using Gemini API with Google Search grounding
    Falls back to OpenRouter if Gemini quota is exhausted
    
    Args:
        prompt: Article generation prompt
        reference_url: Optional reference URL for context
    
    Returns:
        Dictionary containing article_json, seo_json, and source_links
    """
    if not client:
        raise Exception(
            "Gemini API key not configured. Please set GEMINI_API_KEY in backend/.env file. "
            "Get your API key from: https://makersuite.google.com/app/apikey"
        )
    
    try:
        # Build tools list - always include Google Search grounding
        tools = [
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ]
        
        # Build the system prompt
        system_prompt = """You are an expert article writer. Generate a high-quality, structured article based on the user's prompt.

The article should be well-researched, accurate, and include proper citations from web sources. Use Google Search to find current, accurate information.

CRITICAL FORMATTING RULES:
- Write content in PLAIN TEXT only. Do NOT use HTML tags like <ul>, <li>, <p>, <div>, <strong>, <em>, etc.
- Use plain text formatting: use line breaks for paragraphs, use bullet points with "-" or "*" for lists.
- For emphasis, use markdown-style formatting: **bold** for bold text and *italic* for italic text.
- NEVER include HTML tags in the content field. Only plain text is allowed.

CRITICAL: When listing sources, you MUST include the actual, direct URLs to the web pages you found. Do NOT include redirect URLs or tracking URLs. Only include the final destination URLs (e.g., https://example.com/article, not redirect URLs).

Return your response as a JSON object with the following structure:
{
  "title": "Article Title",
  "sections": [
    {
      "heading": "Section Heading",
      "content": "Section content with detailed information in plain text. Use line breaks for paragraphs. Use - or * for bullet points. Use **text** for bold and *text* for italic.",
      "sources": ["https://actual-website.com/article", "https://another-site.com/page"]
    }
  ],
  "summary": "Brief summary of the article"
}

Also generate SEO metadata as a separate JSON object with these exact fields:
{
  "meta_title": "SEO optimized title (max 60 characters)",
  "meta_description": "SEO optimized description (max 160 characters)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "canonical_url": "https://example.com/article"
}

IMPORTANT: 
- Make sure to complete the entire article. Do not cut off mid-sentence. Generate complete, well-structured content.
- Write ALL content in PLAIN TEXT format. NO HTML tags allowed in the content field.
- In the SOURCES section, list the actual, direct URLs to the web pages you found through Google Search. These should be the final destination URLs, not redirect or tracking URLs.

Format your response as:
ARTICLE_JSON:
{article json here}

SEO_JSON:
{seo json here}

SOURCES:
- https://actual-website.com/article
- https://another-site.com/page
"""
        
        # Build the user prompt
        if reference_url:
            user_prompt = f"""Reference URL: {reference_url}

User Prompt: {prompt}

Please generate an article based on the above prompt, using the reference URL as additional context. Also use Google Search to find additional relevant information."""
        else:
            user_prompt = prompt
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Configure generation settings
        config = types.GenerateContentConfig(
            tools=tools,
            temperature=0.7,
            top_p=0.8,
            top_k=40,
        )
        
        # Generate content with Google Search grounding
        print(f"Calling Gemini API with model: {settings.gemini_model}")
        print(f"Prompt length: {len(full_prompt)} characters")
        
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=full_prompt,
                config=config
            )
            print("Gemini API call successful")
        except Exception as api_error:
            error_str = str(api_error)
            print(f"Gemini API error: {error_str}")
            
            # Check if it's a quota/rate limit error (429)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                print("Gemini quota exhausted. Falling back to OpenRouter...")
                try:
                    return await generate_article_with_openrouter(prompt, reference_url)
                except Exception as openrouter_error:
                    raise Exception(
                        f"Gemini quota exhausted and OpenRouter fallback failed: {str(openrouter_error)}\n"
                        f"Original Gemini error: {error_str}"
                    )
            else:
                raise Exception(f"Gemini API call failed: {error_str}")
        
        # Extract text from response
        if not hasattr(response, 'text') or not response.text:
            raise Exception("Gemini API returned empty response")
        
        content = response.text
        print(f"Response length: {len(content)} characters")
        
        # Extract grounding metadata (sources from Google Search)
        sources = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                if hasattr(candidate.grounding_metadata, 'grounding_chunks'):
                    for chunk in candidate.grounding_metadata.grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web:
                            # Try to get the actual URL from different possible fields
                            uri = None
                            if hasattr(chunk.web, 'uri'):
                                uri = chunk.web.uri
                            elif hasattr(chunk.web, 'url'):
                                uri = chunk.web.url
                            elif hasattr(chunk.web, 'link'):
                                uri = chunk.web.link
                            
                            if uri:
                                sources.append(uri)
        
        # Extract JSON from response
        article_json, seo_json, extracted_sources = parse_gemini_response(content)
        
        # Extract actual URLs from article content (LLM often includes real URLs in the text)
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        found_urls = re.findall(url_pattern, content)
        actual_urls_from_content = []
        for url in found_urls:
            # Filter out redirect URLs and keep only real URLs
            if 'grounding-api-redirect' not in url and url not in actual_urls_from_content:
                # Basic validation - real URLs are usually shorter and have proper domains
                if len(url) < 200 and '.' in url.split('//')[-1].split('/')[0]:
                    actual_urls_from_content.append(url)
        
        # Combine all sources
        all_sources = list(set(sources + extracted_sources + actual_urls_from_content))
        
        # Separate redirect URLs from actual URLs
        redirect_urls = [url for url in all_sources if 'grounding-api-redirect' in url]
        non_redirect_urls = [url for url in all_sources if 'grounding-api-redirect' not in url]
        
        # Start with non-redirect URLs and URLs extracted from content
        final_sources = list(set(non_redirect_urls + actual_urls_from_content))
        
        # Build a mapping of redirect URLs to resolved URLs (resolve once)
        redirect_to_resolved = {}
        if redirect_urls:
            import asyncio
            tasks = [resolve_redirect_url(url) for url in redirect_urls]
            resolved_sources = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(resolved_sources):
                if not isinstance(result, Exception):
                    # Only map if it's a real URL (not a redirect)
                    if 'grounding-api-redirect' not in result:
                        redirect_to_resolved[redirect_urls[i]] = result
                        if result not in final_sources:
                            final_sources.append(result)
        
        # Final cleanup: remove duplicates and filter out any remaining redirect URLs
        all_sources = [url for url in list(set(final_sources)) if 'grounding-api-redirect' not in url]
        
        # Update sources in each section - replace redirect URLs with resolved ones
        for section in article_json.get("sections", []):
            section_sources = section.get("sources", [])
            updated_sources = []
            for src in section_sources:
                if src in redirect_to_resolved:
                    # Replace redirect URL with resolved URL
                    resolved = redirect_to_resolved[src]
                    if resolved not in updated_sources:
                        updated_sources.append(resolved)
                elif 'grounding-api-redirect' not in src:
                    # Keep non-redirect URLs
                    if src not in updated_sources:
                        updated_sources.append(src)
            # Update section sources (remove any remaining redirects)
            section["sources"] = [url for url in updated_sources if 'grounding-api-redirect' not in url]
        
        return {
            "article_json": article_json,
            "seo_json": seo_json,
            "sources": all_sources
        }
        
    except Exception as e:
        raise Exception(f"Error generating article: {str(e)}")


def parse_gemini_response(content: str) -> tuple:
    """
    Parse Gemini response to extract article JSON, SEO JSON, and sources
    
    Returns:
        Tuple of (article_json, seo_json, sources_list)
    """
    import json
    import re
    
    article_json = {}
    seo_json = {}
    sources = []
    
    try:
        # Extract ARTICLE_JSON section - use balanced brace matching with string awareness
        article_start = content.find('ARTICLE_JSON:')
        if article_start != -1:
            # Find the opening brace after ARTICLE_JSON:
            json_start = content.find('{', article_start)
            if json_start != -1:
                # Use balanced brace counting that respects strings
                brace_count = 0
                json_end = json_start
                in_string = False
                escape_next = False
                
                for i in range(json_start, len(content)):
                    char = content[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                
                if json_end > json_start:
                    article_str = content[json_start:json_end]
                    # Try to fix common JSON issues (trailing commas, etc.)
                    article_str = re.sub(r',\s*}', '}', article_str)
                    article_str = re.sub(r',\s*]', ']', article_str)
                    try:
                        article_json = json.loads(article_str)
                    except json.JSONDecodeError as e:
                        # Try repairing missing commas (fast fix)
                        try:
                            article_str = repair_json_missing_commas(article_str)
                            article_json = json.loads(article_str)
                        except json.JSONDecodeError as e2:
                            # Quick regex-based extraction (faster than complex parsing)
                            print(f"Warning: JSON parsing failed, using quick extraction: {e2}")
                            try:
                                # Fast extraction: get title and sections
                                title_match = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', article_str)
                                
                                # Extract sections - look for heading and content pairs
                                sections = []
                                # Find all "heading" and "content" pairs
                                heading_matches = list(re.finditer(r'"heading"\s*:\s*"((?:[^"\\]|\\.)*)"', article_str))
                                content_matches = list(re.finditer(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', article_str))
                                
                                # Match headings with their corresponding content
                                for i, heading_match in enumerate(heading_matches):
                                    heading = heading_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                                    # Find the next content after this heading
                                    content_text = ""
                                    for content_match in content_matches:
                                        if content_match.start() > heading_match.end():
                                            content_text = content_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                                            break
                                    
                                    if content_text or heading:
                                        sections.append({
                                            "heading": heading,
                                            "content": content_text,
                                            "sources": []
                                        })
                                
                                # Build article structure
                                if title_match or sections:
                                    article_json = {
                                        "title": title_match.group(1).replace('\\"', '"') if title_match else "Generated Article",
                                        "sections": sections if sections else [{
                                            "heading": "Content",
                                            "content": article_str[:5000] if len(article_str) > 5000 else article_str,
                                            "sources": []
                                        }],
                                        "summary": title_match.group(1).replace('\\"', '"') if title_match else "Article summary"
                                    }
                                else:
                                    raise Exception("Could not extract article structure")
                            except Exception as parse_error:
                                print(f"Quick extraction failed: {parse_error}")
                                # Will fall through to create default structure
        
        # Extract SEO_JSON section - use balanced brace matching with string awareness
        seo_start = content.find('SEO_JSON:')
        if seo_start != -1:
            json_start = content.find('{', seo_start)
            if json_start != -1:
                brace_count = 0
                json_end = json_start
                in_string = False
                escape_next = False
                
                for i in range(json_start, len(content)):
                    char = content[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                
                if json_end > json_start:
                    seo_str = content[json_start:json_end]
                    seo_str = re.sub(r',\s*}', '}', seo_str)
                    seo_str = re.sub(r',\s*]', ']', seo_str)
                    try:
                        seo_json = json.loads(seo_str)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse SEO_JSON: {e}")
                        # Try to fix and retry
                        try:
                            seo_str = re.sub(r',(\s*[}\]])', r'\1', seo_str)
                            seo_json = json.loads(seo_str)
                        except:
                            pass
        
        # Extract SOURCES section
        sources_match = re.search(r'SOURCES:\s*(.*?)(?=\n\n|\Z)', content, re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1)
            sources = [line.strip('- ').strip() for line in sources_text.split('\n') if line.strip()]
        
        # Fallback: try to parse as single JSON if structured format fails
        if not article_json:
            try:
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    if "title" in parsed:
                        article_json = parsed
            except:
                pass
        
    except Exception as e:
        # If parsing fails, create a basic structure
        print(f"Error parsing response: {e}")
        article_json = {
            "title": "Generated Article",
            "sections": [{
                "heading": "Content",
                "content": content[:1000] if content else "Content generation failed",  # First 1000 chars
                "sources": []
            }],
            "summary": "Article generated successfully"
        }
        seo_json = {
            "meta_title": "Generated Article",
            "meta_description": "AI-generated article",
            "keywords": [],
            "canonical_url": ""
        }
    
    # Ensure article_json always has required structure
    if not article_json.get("sections"):
        article_json["sections"] = [{
            "heading": "Content",
            "content": content[:1000] if content else "No content available",
            "sources": []
        }]
    
    if not article_json.get("title"):
        article_json["title"] = "Generated Article"
    
    if not article_json.get("summary"):
        article_json["summary"] = "Article summary"
    
    # Clean HTML tags from all content fields
    article_json["title"] = strip_html_tags(article_json.get("title", ""))
    article_json["summary"] = strip_html_tags(article_json.get("summary", ""))
    
    # Clean HTML tags from sections
    for section in article_json.get("sections", []):
        section["heading"] = strip_html_tags(section.get("heading", ""))
        section["content"] = strip_html_tags(section.get("content", ""))
    
    # Clean HTML tags from SEO fields
    if seo_json:
        seo_json["meta_title"] = strip_html_tags(seo_json.get("meta_title", ""))
        seo_json["meta_description"] = strip_html_tags(seo_json.get("meta_description", ""))
    
    # Ensure seo_json always has required structure
    if not seo_json:
        seo_json = {
            "meta_title": article_json.get("title", "Generated Article"),
            "meta_description": article_json.get("summary", "AI-generated article"),
            "keywords": [],
            "canonical_url": ""
        }
    
    return article_json, seo_json, sources
