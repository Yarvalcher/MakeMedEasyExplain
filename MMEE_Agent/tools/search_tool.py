import urllib.request
import urllib.parse
import re

def web_search(query: str, max_results: int = 4) -> str:
    """Queries the web (via DuckDuckGo Lite) for general medical topics, definitions, or comparisons.
    
    This acts as a fallback search when local files and PubMed do not yield results.
    
    Args:
        query: Keywords or questions to search for.
        max_results: Maximum number of search snippets to return.
        
    Returns:
        A combined string of top search snippets.
    """
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
            
            # Find result snippets matching class='result-snippet' or class="result-snippet"
            snippets = re.findall(r"<td[^>]*class=['\"]result-snippet['\"][^>]*>(.*?)</td>", html, re.DOTALL)
            
            cleaned_snippets = []
            for snip in snippets[:max_results]:
                cleaned = re.sub(r'<[^>]+>', '', snip)
                cleaned = cleaned.replace('\n', ' ').replace('&nbsp;', ' ').strip()
                # Unescape standard HTML entities
                cleaned = (
                    cleaned.replace('&quot;', '"')
                    .replace('&amp;', '&')
                    .replace('&lt;', '<')
                    .replace('&gt;', '>')
                    .replace('&#x27;', "'")
                    .replace('&#x27;s', "'s")
                )
                if cleaned:
                    cleaned_snippets.append(cleaned)
                    
            if not cleaned_snippets:
                return f"No search results found on the web for query: '{query}'"
                
            return "\n\n".join([f"- {s}" for s in cleaned_snippets])
    except Exception as e:
        return f"Web search tool error: {e}"
