import copy
import asyncio
from loguru import logger
from typing import List
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

from agentchat.core.callbacks import usage_metadata_callback
from agentchat.tools import WorkSpacePlugins
from agentchat.schemas.usage_stats import UsageStatsAgentType
from agentchat.schemas.workspace import WorkSpaceAgents
from agentchat.api.services.tool import ToolService
from agentchat.prompts.completion import GenerateTitlePrompt
from agentchat.core.models.manager import ModelManager
from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.database.models.workspace_session import WorkSpaceSessionCreate, WorkSpaceSessionContext


class WorkSpaceSimpleAgent:
    """
    工作台子 Agent：根据对话上下文选择并异步执行用户绑定的插件工具，
    把工具结果回传主模型；自身不生成最终回答。
    """

    def __init__(self,
                 model_config,
                 user_id: str,
                 session_id: str,
                 plugins: List[str] = []):

        # Simple-agent only needs tool calling model, not conversation model
        self.model = ModelManager.get_user_model(**model_config)
        self.plugin_tools = []
        self.tools = []
        self.plugins = plugins
        self.session_id = session_id

        self.user_id = user_id

        # Initialize state management
        self._initialized = False


    async def init_simple_agent(self):
        """Initialize sub-agent - with resource management"""
        try:
            if self._initialized:
                logger.info("Simple Agent already initialized")
                return
            await self.setup_plugin_tools()

            self.tools = self.plugin_tools
            self._initialized = True
            self.react_agent = self.setup_react_agent()

            logger.info("Simple Agent initialized successfully")
        except Exception as err:
            logger.error(f"Failed to initialize Simple Agent: {err}")
            raise

    def setup_react_agent(self):
        return create_agent(
            model=self.model,
            tools=self.tools
        )

    async def setup_plugin_tools(self):
        """Initialize plugin tools - with error handling

        仅注册 WorkSpacePlugins 白名单内的内置工具；未注册的工具（如 OpenAPI
        自定义工具）明确跳过并告警，避免一个未知工具名把整批插件拖垮。
        """
        try:
            tools_name = await ToolService.get_tool_name_by_id(self.plugins)
            for name in tools_name:
                if name in WorkSpacePlugins:
                    self.plugin_tools.append(WorkSpacePlugins[name])
                else:
                    logger.warning(f"插件 {name} 未注册为工作台插件，已跳过")

            logger.info(f"Loaded {len(self.plugin_tools)} plugin tools")

        except Exception as err:
            logger.error(f"Failed to initialize plugin tools: {err}")
            self.plugin_tools = []

    async def ainvoke(self, messages: List[BaseMessage]):
        """Sub-agent tool execution - only return tool execution results, no model reply"""
        if not self._initialized:
            await self.init_simple_agent()

        try:
            react_agent_task = None
            if self.tools and len(self.tools) != 0:
                react_agent_task = asyncio.create_task(self.react_agent.ainvoke({"messages": messages}))

            # Wait for tool execution to complete
            if react_agent_task:
                results = await react_agent_task
                messages = results["messages"][:-1]  # Remove messages that didn't hit tools

                messages = [msg for msg in messages if
                            isinstance(msg, ToolMessage) or (isinstance(msg, AIMessage) and msg.tool_calls)]

                return messages
            else:
                return []

        except Exception as err:
            return []

    async def _generate_title(self, query):
        session = await WorkSpaceSessionService.get_workspace_session_from_id(self.session_id, self.user_id)
        if session:
            return session.get("title")
        title_prompt = GenerateTitlePrompt.format(query=query)
        response = await self.model.ainvoke(title_prompt, config={"callbacks": [usage_metadata_callback]})
        return response.content

    async def _add_workspace_session(self, title, contexts: WorkSpaceSessionContext):
        session = await WorkSpaceSessionService.get_workspace_session_from_id(self.session_id, self.user_id)
        if session:
            await WorkSpaceSessionService.update_workspace_session_contexts(
                session_id=self.session_id,
                session_context=contexts.model_dump()
            )
        else:
            await WorkSpaceSessionService.create_workspace_session(
                WorkSpaceSessionCreate(
                    title=title,
                    user_id=self.user_id,
                    session_id=self.session_id,
                    contexts=[contexts.model_dump()],
                    agent=WorkSpaceAgents.SimpleAgent.value))


    async def astream(self, messages: List[BaseMessage]):
        if not self._initialized:
            await self.init_simple_agent()
        user_messages = copy.deepcopy(messages)

        generate_title_task = asyncio.create_task(self._generate_title(user_messages[-1].content))
        try:
            react_agent_task = None
            if self.tools and len(self.tools) != 0:
                react_agent_task = asyncio.create_task(self.react_agent.ainvoke(input={"messages": messages}, config={"callbacks": [usage_metadata_callback]}))

            # Wait for tool execution to complete
            if react_agent_task:
                results = await react_agent_task
                messages = results["messages"][:-1]  # Remove messages that didn't hit tools

                messages = [msg for msg in messages if
                            isinstance(msg, ToolMessage) or (isinstance(msg, AIMessage) and msg.tool_calls)]
        except Exception as err:
            raise ValueError from err
        messages = user_messages + messages

        final_answer = ""
        async for chunk in self.model.astream(input=messages, config={"callbacks": [usage_metadata_callback]}):
            yield {
                "event": "task_result",
                "data":{
                    "message": chunk.content
                }
            }
            final_answer += chunk.content

        await generate_title_task
        title = generate_title_task.result() if generate_title_task.done() else None

        await self._add_workspace_session(
            title=title,
            contexts=WorkSpaceSessionContext(
                query=user_messages[-1].content,
                answer=final_answer
            ))
