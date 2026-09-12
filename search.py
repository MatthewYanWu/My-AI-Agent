from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()


client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def search_web(query):

    result = client.search(
        query=query,
        max_results=3
    )

    web_content = ""

    for item in result["results"]:

        web_content += f"""
标题：
{item['title']}

网址：
{item['url']}

内容：
{item['content']}

----------------
"""

    return web_content