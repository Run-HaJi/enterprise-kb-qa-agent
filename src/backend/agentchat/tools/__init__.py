from agentchat.tools.arxiv.action import get_arxiv
from agentchat.tools.docx_to_pdf.action import convert_to_pdf
from agentchat.tools.pdf_to_docx.action import convert_to_docx


AgentTools = [
    get_arxiv,
    convert_to_pdf,
    convert_to_docx,
]


AgentToolsWithName = {
    "get_arxiv": get_arxiv,
    "docx_to_pdf": convert_to_pdf,
    "pdf_to_docx": convert_to_docx,
}

WorkSpacePlugins = AgentToolsWithName
