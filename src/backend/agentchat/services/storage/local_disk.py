import os
import shutil
from urllib.parse import quote
from loguru import logger

from agentchat.settings import app_settings


class LocalDiskClient:
    """本地磁盘存储客户端，接口与原 MinIO/OSS 客户端对齐。

    文件统一落在配置的 root 目录下，object_name 即相对路径；
    通过 FastAPI 挂载的 /api/files 静态目录对外提供访问。
    """

    def __init__(self):
        self.root = app_settings.storage.local.get("root", "./storage_data")
        os.makedirs(self.root, exist_ok=True)

    def _normalize(self, object_name: str) -> str:
        """URL 路径（api/files/X）与存储对象名（files/X）互为前缀映射"""
        name = (object_name or "").lstrip("/")
        if name.startswith("api/files/"):
            name = name[len("api/"):]
        return name

    def _abs(self, object_name: str) -> str:
        path = os.path.abspath(os.path.join(self.root, self._normalize(object_name)))
        root = os.path.abspath(self.root)
        if not path.startswith(root):
            raise ValueError(f"非法的存储路径: {object_name}")
        return path

    def upload_file(self, object_name: str, data: bytes):
        path = self._abs(object_name)
        os.makedirs(os.path.dirname(path) or self.root, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        logger.info(f"[storage] uploaded {object_name} ({len(data)} bytes)")

    def upload_local_file(self, object_name: str, local_file: str):
        path = self._abs(object_name)
        os.makedirs(os.path.dirname(path) or self.root, exist_ok=True)
        shutil.copyfile(local_file, path)
        logger.info(f"[storage] uploaded {object_name} from {local_file}")

    def sign_url_for_get(self, object_name: str, expiration=3600) -> str:
        # 本地静态目录无需签名，直接返回挂载路径
        return f"/api/files/{quote(self._normalize(object_name))}"

    def download_file(self, object_name: str, local_file: str):
        shutil.copyfile(self._abs(object_name), local_file)
        logger.info(f"[storage] downloaded {object_name} -> {local_file}")

    def list_files_in_folder(self, folder_path: str):
        abs_folder = self._abs(folder_path)
        if not os.path.isdir(abs_folder):
            return []
        return [f"{folder_path.rstrip('/')}/{name}" for name in os.listdir(abs_folder)]

    def delete_bucket(self):
        # 本地模式下清空根目录需显式调用，保持接口兼容但危险操作留空实现
        logger.warning("[storage] delete_bucket is a no-op under local storage mode")
