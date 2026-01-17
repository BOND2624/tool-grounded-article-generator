"""
Ollama local model service for article generation
"""

import httpx
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, Dict, Any, Tuple


class OllamaSettings(BaseSettings):
    """Ollama API settings"""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"  # Default model, can be changed to llama3, mistral, etc.
    
    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = OllamaSettings()


async def check_ollama_connection() -> Tuple[bool, list]:
    """
    Check if Ollama is running and list available models
    
    Returns:
        Tuple of (is_connected, available_models)
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Ollama is running
            try:
                response = await client.get(f"{settings.ollama_base_url}/api/tags")
                response.raise_for_status()
                models_data = response.json()
                available_models = [model["name"] for model in models_data.get("models", [])]
                return True, available_models
            except httpx.HTTPError:
                return False, []
    except Exception:
        return False, []


async def generate_article(
    prompt: str,
    reference_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an article using Ollama local models
    
    Args:
        prompt: Article generation prompt
        reference_url: Optional reference URL for context
    
    Returns:
        Dictionary containing article_json, seo_json, and source_links
    """
    try:
        # Check if Ollama is running and get available models
        is_connected, available_models = await check_ollama_connection()
        if not is_connected:
            raise Exception(
                f"Ollama is not running or not accessible at {settings.ollama_base_url}. "
                f"Please make sure Ollama is installed and running. Start it with: ollama serve"
            )
        
        # Check if the specified model is available
        if available_models and settings.ollama_model not in available_models:
            # Try to find a similar model or use the first available
            model_to_use = settings.ollama_model
            # Check if any model name contains the requested model name
            matching_models = [m for m in available_models if settings.ollama_model in m]
            if matching_models:
                model_to_use = matching_models[0]
            else:
                model_to_use = available_models[0] if available_models else settings.ollama_model
                if model_to_use != settings.ollama_model:
                    print(f"Warning: Model '{settings.ollama_model}' not found. Using '{model_to_use}' instead.")
        else:
            model_to_use = settings.ollama_model
        # Build the system prompt
        system_prompt = """You are an expert article writer. Generate a high-quality, structured article based on the user's prompt.

The article should be well-researched, accurate, and include proper citations from web sources.

Return your response as a JSON object with the following structure:
{
  "title": "Article Title",
  "sections": [
    {
      "heading": "Section Heading",
      "content": "Section content with detailed information...",
      "sources": ["url1", "url2"]
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

IMPORTANT: Make sure to complete the entire article. Do not cut off mid-sentence. Generate complete, well-structured content.

Format your response as:
ARTICLE_JSON:
{article json here}

SEO_JSON:
{seo json here}

SOURCES:
- source_url_1
- source_url_2
"""
        
        # Add reference URL context if provided
        if reference_url:
            user_prompt = f"""Reference URL: {reference_url}

User Prompt: {prompt}

Please generate an article based on the above prompt, using the reference URL as additional context."""
        else:
            user_prompt = prompt
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Call Ollama API
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model_to_use,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.8,
                        "top_k": 40,
                        "num_predict": 4096,  # Increase output length
                    }
                }
            )
            
            if response.status_code == 404:
                raise Exception(
                    f"Model '{model_to_use}' not found. Available models: {', '.join(available_models) if available_models else 'none'}. "
                    f"Pull a model with: ollama pull {model_to_use}"
                )
            
            response.raise_for_status()
            result = response.json()
            content = result.get("response", "")
        
        # Extract JSON from response
        article_json, seo_json, sources = parse_ollama_response(content)
        
        return {
            "article_json": article_json,
            "seo_json": seo_json,
            "sources": sources
        }
        
    except httpx.HTTPError as e:
        raise Exception(f"Error connecting to Ollama: {str(e)}. Make sure Ollama is running on {settings.ollama_base_url}")
    except Exception as e:
        raise Exception(f"Error generating article: {str(e)}")


def parse_ollama_response(content: str) -> tuple:
    """
    Parse Ollama response to extract article JSON, SEO JSON, and sources
    
    Returns:
        Tuple of (article_json, seo_json, sources_list)
    """
    import json
    import re
    
    article_json = {}
    seo_json = {}
    sources = []
    
    try:
        # Extract ARTICLE_JSON section - use balanced brace matching
        article_start = content.find('ARTICLE_JSON:')
        if article_start != -1:
            # Find the opening brace after ARTICLE_JSON:
            json_start = content.find('{', article_start)
            if json_start != -1:
                # Use balanced brace counting to find the matching closing brace
                brace_count = 0
                json_end = json_start
                for i in range(json_start, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                article_str = content[json_start:json_end]
                # Try to fix common JSON issues (trailing commas, etc.)
                article_str = re.sub(r',\s*}', '}', article_str)
                article_str = re.sub(r',\s*]', ']', article_str)
                try:
                    article_json = json.loads(article_str)
                except json.JSONDecodeError as e:
                    # If JSON is still invalid, try to extract what we can
                    print(f"Warning: Failed to parse ARTICLE_JSON: {e}")
        
        # Extract SEO_JSON section - use balanced brace matching
        seo_start = content.find('SEO_JSON:')
        if seo_start != -1:
            json_start = content.find('{', seo_start)
            if json_start != -1:
                brace_count = 0
                json_end = json_start
                for i in range(json_start, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                seo_str = content[json_start:json_end]
                seo_str = re.sub(r',\s*}', '}', seo_str)
                seo_str = re.sub(r',\s*]', ']', seo_str)
                try:
                    seo_json = json.loads(seo_str)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse SEO_JSON: {e}")
        
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
        article_json = {
            "title": "Generated Article",
            "sections": [{
                "heading": "Content",
                "content": content[:1000],  # First 1000 chars
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
    
    return article_json, seo_json, sources
