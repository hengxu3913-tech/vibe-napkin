"""MCP server：zvec 向量检索服务。

启动后供 AI 通过 query_kb 工具查询知识库。
"""
from __future__ import annotations

import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from _config import (
    build_embedding,
    docs_dir,
    storage_dir,
    _resolve_embedding_cfg,
)

mcp = FastMCP("docs-kb")

_COLLECTION = None
_EMBED = None


def _get_collection():
    global _COLLECTION
    if _COLLECTION is None:
        import zvec
        zvec_dir = storage_dir() / "_collection"
        zvec_path = str(zvec_dir)
        if not zvec_dir.exists():
            raise FileNotFoundError(
                f"知识库尚未构建：{zvec_path} 不存在。\n"
                f"  请执行：python {Path(__file__).parent / 'build_kb.py'}"
            )
        lock_file = zvec_dir / "LOCK"
        if not lock_file.exists():
            try:
                lock_file.touch()
            except Exception:
                pass
        opt = zvec.CollectionOption(enable_mmap=True, read_only=True)
        _COLLECTION = zvec.open(path=zvec_path, option=opt)
    return _COLLECTION


def _get_embed():
    global _EMBED
    if _EMBED is None:
        _EMBED = build_embedding()
    return _EMBED


def _format_chunks(hits: list) -> str:
    parts = []
    for rank, h in enumerate(hits, 1):
        parts.append(
            f"### [{rank}] {h.get('doc_path', '?')}  "
            f"(相关度 {h.get('score', 0):.3f})\n\n"
            f"{h.get('text', '')}"
        )
    return "\n\n---\n\n".join(parts)


def _extract_hits(results, collection) -> list[dict]:
    out = []
    if not isinstance(results, list):
        return out
    for r in results:
        if isinstance(r, dict):
            hit = {
                "id": r.get("id", ""),
                "score": float(r.get("score", 0.0) or 0.0),
                "text": r.get("text", ""),
                "doc_path": r.get("doc_path", ""),
            }
        else:
            fields = getattr(r, "fields", {}) or {}
            hit = {
                "id": getattr(r, "id", "") or "",
                "score": float(getattr(r, "score", 0.0) or 0.0),
                "text": fields.get("text", ""),
                "doc_path": fields.get("doc_path", ""),
            }
        if not hit["text"] and hit["id"]:
            try:
                doc = collection.get(hit["id"])
                if doc:
                    if isinstance(doc, dict):
                        hit["text"] = doc.get("text", "")
                        hit["doc_path"] = doc.get("doc_path", "")
                    else:
                        fields = getattr(doc, "fields", {}) or {}
                        hit["text"] = fields.get("text", "")
                        hit["doc_path"] = fields.get("doc_path", "")
            except Exception:
                pass
        out.append(hit)
    return out


@mcp.tool()
async def query_kb(question: str, top_k: int = 5) -> str:
    """从知识库检索与问题相关的文档片段。"""
    import zvec
    try:
        collection = _get_collection()
    except Exception as e:
        return (
            "⚠️ 知识库尚未构建。\n"
            "  请先执行：python .napkin/mcp/build_kb.py\n"
            f"  错误：{type(e).__name__}: {e}"
        )

    embed = _get_embed()
    q_vec = await embed([question])
    q_vec = q_vec[0]
    q_vec = list(q_vec) if hasattr(q_vec, "tolist") else q_vec

    try:
        results = collection.query(
            zvec.VectorQuery("embedding", vector=q_vec),
            topk=top_k,
        )
    except Exception as e:
        return f"✗ zvec 查询失败: {type(e).__name__}: {e}"

    hits = _extract_hits(results, collection)
    if not hits:
        return "知识库中没有匹配结果。"

    return _format_chunks(hits)


@mcp.tool()
async def list_documents() -> str:
    """列出已索引的文档清单 + chunk 数。"""
    import json
    manifest_path = storage_dir() / "_manifest.json"
    if not manifest_path.exists():
        return "知识库尚未构建（请先执行 python .napkin/mcp/build_kb.py）"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"无法读取清单：{type(e).__name__}: {e}"
    if not manifest:
        return "知识库为空"
    total = sum(info.get("chunks", 0) for info in manifest.values())
    lines = [f"共 {len(manifest)} 份文档 / {total} chunks："]
    for doc, info in sorted(manifest.items()):
        lines.append(f"  · {doc}  ({info.get('chunks', 0)} chunks)")
    return "\n".join(lines)


@mcp.tool()
async def get_server_info() -> str:
    """查看当前服务配置。"""
    emb_cfg = _resolve_embedding_cfg()
    zvec_path = storage_dir() / "_collection"
    built = zvec_path.exists()
    lines = [
        "zvec MCP Server",
        f"  Embedding : {emb_cfg['model']} (dim={emb_cfg['dim']})",
        f"  Docs 目录 : {docs_dir()}",
        f"  存储目录  : {storage_dir()}",
        f"  已建库    : {'是' if built else '否（需先跑 build_kb.py）'}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(f"[docs-kb] starting, storage={storage_dir()}", flush=True)
    mcp.run(transport="stdio")