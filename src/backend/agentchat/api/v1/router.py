from fastapi import APIRouter
from agentchat.api.v1 import (
    completion, dialog, message, agent, history,
    user, llm, tool, knowledge, knowledge_file, workspace, upload, )

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(completion.router)
api_v1_router.include_router(dialog.router)
api_v1_router.include_router(message.router)
api_v1_router.include_router(agent.router)
api_v1_router.include_router(history.router)
api_v1_router.include_router(user.router)
api_v1_router.include_router(tool.router)
api_v1_router.include_router(llm.router)
api_v1_router.include_router(knowledge.router)
api_v1_router.include_router(knowledge_file.router)
api_v1_router.include_router(workspace.router)
api_v1_router.include_router(upload.router)
