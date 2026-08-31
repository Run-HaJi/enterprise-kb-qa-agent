import os

from dotenv import load_dotenv
from pydantic.v1 import BaseSettings

# 提前加载 .env：Settings 在模块导入期实例化（早于 lifespan 的 settings 加载）
load_dotenv(os.path.join(os.getcwd(), ".env"))

def _jwt_secret_key() -> str:
    """JWT 签名密钥，优先环境变量 JWT_SECRET_KEY（生产必设）。

    默认 'secret' 仅为开发兜底——任何持有默认值的人都能伪造 token。
    """
    return os.getenv("JWT_SECRET_KEY") or "secret"


# 定义 Pydantic 的 BaseSettings 类
class Settings(BaseSettings):
    authjwt_secret_key: str = _jwt_secret_key()
    authjwt_token_location: list = ['cookies', 'headers']
    authjwt_cookie_csrf_protect: bool = False