from agentchat.tools.arxiv.action import get_arxiv
from agentchat.tools.pdf_to_docx.action import convert_to_docx


AgentTools = [
    get_arxiv,
    convert_to_docx,
]


AgentToolsWithName = {
    "get_arxiv": get_arxiv,
    "pdf_to_docx": convert_to_docx,
}

WorkSpacePlugins = AgentToolsWithName
