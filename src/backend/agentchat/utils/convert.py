import json
from typing import List

from langchain_core.messages import ToolCall
from openai.types.chat import ChatCompletionMessageToolCall


def convert_langchain_tool_calls(tool_calls: List[ChatCompletionMessageToolCall]):
    if not tool_calls:
        return []

    langchain_tool_calls: List[ToolCall] = []
    for tool_call in tool_calls:
        langchain_tool_calls.append(
            ToolCall(id=tool_call.id, args=json.loads(tool_call.function.arguments), name=tool_call.function.name))

    return langchain_tool_calls