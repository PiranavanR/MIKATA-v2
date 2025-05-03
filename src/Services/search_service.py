import wikipediaapi
from duckduckgo_search import DDGS

class SearchTools:
    def __init__(self):
        """Initialize Wikipedia API and DuckDuckGo Search with proper User-Agent."""
        self.wiki_api = wikipediaapi.Wikipedia(
            user_agent="MIKATA-SearchBot/1.0 (uchiharyuga07@gmail.com)"
        )

    def search_wikipedia(self, query, char_limit=500):
        """Fetch summary from Wikipedia with a character limit, ensuring complete sentences."""
        page = self.wiki_api.page(query)
        if not page.exists():
            return "I couldn't find that on Wikipedia."
        
        summary = page.summary
        if len(summary) > char_limit:
            # Find the last full stop before char_limit
            end_index = summary.rfind(".", 0, char_limit)
            if end_index == -1:
                end_index = char_limit  # Fallback if no full stop is found
            summary = summary[:end_index + 1]  # Include the full stop
        print(summary)
        return summary

    def search_duckduckgo(self, query, max_results=3):
        """Fetch web search results using DuckDuckGo."""
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))  # Convert generator to list
            print(results)
        if not results:
            return ["No relevant search results found."]
        
        return [f"{res['title']}: {res['href']}" for res in results]

    def smart_search(self, query):
        """Decide whether to use Wikipedia or DuckDuckGo based on query type."""
        wiki_result = self.search_wikipedia(query)
        print(wiki_result)
        if "I couldn't find" not in wiki_result:
            return f"📚 **Wikipedia says:**\n{wiki_result}"
        
        # If Wikipedia fails, try DuckDuckGo
        web_results = self.search_duckduckgo(query)
        print(web_results)
        return "🌐 **Web results:**\n" + "\n".join(web_results)

