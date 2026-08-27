from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class ModelConfig(BaseModel):
    model_name: str = ""
    api_key: str = ""
    base_url: str = ""

class MultiModels(BaseModel):
    class Config:
        # 允许从dict额外属性创建模型
        extra = "allow"

    reasoning_model: ModelConfig = Field(default_factory=ModelConfig)
    conversation_model: ModelConfig = Field(default_factory=ModelConfig)
    tool_call_model: ModelConfig = Field(default_factory=ModelConfig)
    qwen3_coder: ModelConfig = Field(default_factory=ModelConfig)
    qwen_vl: ModelConfig = Field(default_factory=ModelConfig)
    text2image: ModelConfig = Field(default_factory=ModelConfig)
    embedding: ModelConfig = Field(default_factory=ModelConfig)
    rerank: ModelConfig = Field(default_factory=ModelConfig)

class Tools(BaseModel):
    class Config:
        extra = "allow"

    weather: dict = Field(default_factory=dict)
    tavily: dict = Field(default_factory=dict)
    google: dict = Field(default_factory=dict)
    delivery: dict = Field(default_factory=dict)
    bocha: dict = Field(default_factory=dict)


class Rag(BaseModel):
    class Config:
        extra = "allow"
    enable_summary: bool = Field(default=False)
    enable_ik_analyzer: bool = Field(default=False)
    retrival: dict = Field(default_factory=dict)
    split: dict = Field(default_factory=dict)
    vector_db: dict = Field(default_factory=dict)



class OSSConfig(BaseModel):
    access_key_id: str
    access_key_secret: str
    endpoint: str
    bucket_name: str
    base_url: str


class MinioConfig(BaseModel):
    access_key_id: str
    access_key_secret: str
    endpoint: str
    bucket_name: str
    base_url: str

class StorageConfig(BaseModel):
    mode: str = "local"
    local: dict = Field(default_factory=dict)
    oss: Optional[OSSConfig] = None
    minio: Optional[MinioConfig] = None


class ServerConfig(BaseModel):
    name: str = "AgentChat"
    version: str = "2.5.0"
    host: str = "127.0.0.1"
    port: int = 7860
    env: str = "dev"