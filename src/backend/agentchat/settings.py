import yaml
from typing import Literal, Optional
from loguru import logger
from types import SimpleNamespace
from pydantic.v1 import BaseSettings, Field

from agentchat.schemas.common import MultiModels, ModelConfig, Tools, Rag, StorageConfig, ServerConfig


class Settings(BaseSettings):
    redis: dict = {}
    mysql: dict = {}
    langfuse: dict = {}
    whitelist_paths: list = []
    wechat_config: dict = {}
    default_config: dict = {}

    server: Optional[ServerConfig] = ServerConfig()
    rag: Optional[Rag] = None
    tools: Optional[Tools] = None
    storage: Optional[StorageConfig] = None
    multi_models: Optional[MultiModels] = None


app_settings = Settings()

def _apply_env_secrets(data: dict):
    """从环境变量/.env 注入密钥，密钥永远不落配置文件

    约定：环境变量名 = SECTION__FIELD（双下划线分层），例如
    DEEPSEEK_API_KEY → multi_models.{conversation,tool_call,reasoning}.api_key
    值为空或占位符时才覆盖，保证显式配置优先。
    """
    import os
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.getcwd(), ".env"))
    load_dotenv(os.path.join(os.getcwd(), "agentchat", ".env"))

    placeholders = {"", "sk-local-placeholder", None}

    def _fill(target: dict, env_name: str):
        value = os.getenv(env_name)
        if value:
            for entry in target.values():
                if isinstance(entry, dict) and entry.get("api_key") in placeholders:
                    entry["api_key"] = value

    models = data.get("multi_models") or {}
    if isinstance(models, dict):
        _fill(models, "DEEPSEEK_API_KEY")
        if data.get("tools") and isinstance(data["tools"], dict):
            pass  # 外部工具密钥按需单独配置


async def init_app_settings(file_path: str = None):
    global app_settings

    file_path = file_path or "agentchat/config.yaml"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                logger.error("YAML 文件解析为空")
                return

            _apply_env_secrets(data)

            # 特殊处理multi_models配置
            if "multi_models" in data:
                data["multi_models"] = MultiModels(**data["multi_models"])

            if "tools" in data:
                data["tools"] = Tools(**data["tools"])

            if "rag" in data:
                data["rag"] = Rag(**data["rag"])

            if "storage" in data:
                data["storage"] = StorageConfig(**data["storage"])

            if "server" in data:
                data["server"] = ServerConfig(**data["server"])

            for key, value in data.items():
                setattr(app_settings, key, value)
    except Exception as e:
        logger.error(f"Yaml file loading error: {e}")
