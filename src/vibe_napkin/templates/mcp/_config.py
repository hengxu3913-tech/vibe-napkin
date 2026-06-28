"""配置：从 vibe-napkin config.toml 读取 embedding 配置 + 构建后端。

设计：
- 所有路径以本文件所在目录锚定（.napkin/mcp/），CWD 无关。
- Embedding 配置读自 ../config.toml（.napkin/config.toml），不依赖 .env。
- 后兼容：如果配置缺失，回退到环境变量。
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Callable

THIS_DIR = Path(__file__).resolve().parent

# 尝试从 vibe-napkin config.toml 加载 embedding 配置
_EMBEDDING_CFG = None


def _load_vibe_config() -> dict:
    """从 ../config.toml（.napkin/config.toml）加载 embedding 配置。"""
    config_path = THIS_DIR / ".." / "config.toml"
    if not config_path.exists():
        return {}
    try:
        import tomlkit
        data = tomlkit.parse(config_path.read_text(encoding="utf-8"))
        emb = data.get("embedding", {})
        return {
            "backend": str(emb.get("provider", "aliyun")),
            "model": str(emb.get("model", "text-embedding-v4")),
            "dim": int(emb.get("dim", 1024)),
            "api_key": str(emb.get("api_key", "")),
            "base_url": str(emb.get("base_url",
                "https://dashscope.aliyuncs.com/compatible-mode/v1")),
        }
    except Exception:
        return {}


def docs_dir() -> Path:
    """docs/ 目录的绝对路径（相对 .napkin/mcp/ 往上三层 = 项目根）。"""
    # 默认：../../../docs  → 项目根下的 docs/
    default = str(THIS_DIR / "../../../docs")
    raw = os.environ.get("DOCS_DIR", default)
    # 如果是相对路径，以 THIS_DIR 锚定
    p = Path(raw)
    if not p.is_absolute():
        p = (THIS_DIR / p).resolve()
    return p


def storage_dir() -> Path:
    """zvec_data 存储目录的绝对路径（默认放 .napkin/mcp/zvec_data）。"""
    default = str(THIS_DIR / "zvec_data")
    raw = os.environ.get("STORAGE_DIR", default)
    p = Path(raw)
    if not p.is_absolute():
        p = (THIS_DIR / p).resolve()
    return p


def doc_extensions() -> list[str]:
    """支持的文档扩展名（带点）。"""
    raw = os.environ.get("DOC_EXTENSIONS", ".md,.txt")
    return [e.strip() for e in raw.split(",") if e.strip()]


# ---------------------------------------------------------------------------
# Embedding 配置解析（优先 config.toml，回退环境变量）
# ---------------------------------------------------------------------------

def _resolve_embedding_cfg() -> dict:
    """从 config.toml（优先）或环境变量解析 embedding 配置。"""
    global _EMBEDDING_CFG
    if _EMBEDDING_CFG is None:
        _EMBEDDING_CFG = _load_vibe_config()
    vibe = _EMBEDDING_CFG

    return {
        "backend": vibe.get("backend") or os.environ.get("EMBEDDING_BACKEND", "aliyun"),
        "model": vibe.get("model") or os.environ.get("EMBEDDING_MODEL", "text-embedding-v4"),
        "dim": int(vibe.get("dim") or os.environ.get("EMBEDDING_DIM", "1024")),
        "api_key": vibe.get("api_key") or os.environ.get("EMBEDDING_API_KEY", ""),
        "base_url": vibe.get("base_url") or os.environ.get(
            "EMBEDDING_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
    }


# ---------------------------------------------------------------------------
# 阿里云 DashScope embedding（OpenAI 兼容接口）
# ---------------------------------------------------------------------------

def _build_aliyun_embedding(cfg: dict) -> Callable:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    model = cfg["model"]
    batch_size = 10

    async def embed(texts: list[str]) -> list[list[float]]:
        import asyncio
        all_vecs: list[list[float]] = [None] * len(texts)

        async def _one_batch(start: int):
            chunk = texts[start:start + batch_size]
            r = await client.embeddings.create(model=model, input=chunk)
            for i, d in enumerate(r.data):
                all_vecs[start + i] = d.embedding

        await asyncio.gather(
            *[_one_batch(i) for i in range(0, len(texts), batch_size)]
        )
        return all_vecs

    return embed


# ---------------------------------------------------------------------------
# 本地 BGE embedding（回退方案）
# ---------------------------------------------------------------------------

_BGE_LOCK = threading.Lock()
_BGE_MODEL = None


def _build_local_embedding(cfg: dict) -> Callable:
    global _BGE_MODEL

    async def embed(texts: list[str]) -> list[list[float]]:
        import asyncio
        loop = asyncio.get_event_loop()

        def _encode():
            global _BGE_MODEL
            with _BGE_LOCK:
                if _BGE_MODEL is None:
                    from FlagEmbedding import FlagModel
                    _BGE_MODEL = FlagModel("BAAI/bge-large-zh-v1.5", use_fp16=True)
                return _BGE_MODEL.encode(texts).tolist()

        return await loop.run_in_executor(None, _encode)

    return embed


# ---------------------------------------------------------------------------
# 分发
# ---------------------------------------------------------------------------

def build_embedding() -> Callable:
    """根据配置选择 embedding 后端，返回 async embed 函数。"""
    cfg = _resolve_embedding_cfg()
    if cfg["backend"] == "aliyun":
        return _build_aliyun_embedding(cfg)
    elif cfg["backend"] == "local":
        return _build_local_embedding(cfg)
    elif cfg["backend"] == "openai":
        return _build_aliyun_embedding(cfg)  # OpenAI也是兼容接口
    else:
        raise ValueError(
            f"未知 EMBEDDING_BACKEND: {cfg['backend']}（支持: aliyun / local / openai）"
        )