from langchain.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from agentchat.settings import app_settings

try:
    search = SerpAPIWrapper(serpapi_api_key=app_settings.tools.google.get('api_key'))
except Exception:
    # 未配置 SERPAPI_API_KEY 时允许服务正常启动，调用时再返回不可用提示
    search = None

@tool("web_search", parse_docstring=True)
def google_search(query: str):
    """
    根据用户的问题进行网上搜索信息。

    Args:
        query (str): 用户的问题。

    Returns:
        str: 搜索到的信息。
    """
    return _google_search(query)

def _google_search(query: str):
    """使用搜索工具给用户进行搜索"""
    if search is None:
        return "联网搜索不可用：未配置 SerpAPI Key，请在配置文件中填写后重启服务"
    result = search.run(query)
    return result
