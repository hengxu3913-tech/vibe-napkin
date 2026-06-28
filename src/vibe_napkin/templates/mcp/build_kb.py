"""zvec 知识库构建脚本（增量更新）。

用法：
  python build_kb.py             # 增量更新（默认）
  python build_kb.py --dry-run   # 预览变化
  python build_kb.py --full      # 全量重建

路径自动从 vibe-napkin config.toml 读取。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import hashlib
import time
from pathlib import Path

from _config import (
    build_embedding,
    docs_dir,
    storage_dir,
    doc_extensions,
    _resolve_embedding_cfg,
)

CHUNK_MAX_CHARS = 500
CHUNK_OVERLAP_PARAS = 1
EMBED_BATCH = 32
COLLECTION_NAME = "docs_kb"
EXCLUDE_DIRS = {"历史快照", "archive", "plan"}


def chunk_id(doc_key: str, idx: int) -> str:
    h = hashlib.sha1(f"{doc_key}#{idx}".encode("utf-8")).hexdigest()[:12]
    return f"c{h}_{idx}"


def manifest_path() -> Path:
    return storage_dir() / "_manifest.json"


def load_manifest() -> dict:
    p = manifest_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_manifest(manifest: dict) -> None:
    storage_dir().mkdir(parents=True, exist_ok=True)
    manifest_path().write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def scan_docs() -> list[Path]:
    root = docs_dir()
    exts = doc_extensions()
    out = []
    for p in root.rglob("*"):
        if not (p.is_file() and p.suffix.lower() in exts):
            continue
        try:
            rel_parts = p.relative_to(root).parts
        except ValueError:
            rel_parts = p.parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        out.append(p)
    return sorted(out)


def doc_key(path: Path) -> str:
    try:
        return str(path.relative_to(docs_dir())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def chunk_text(text: str) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paras:
        return [text.strip()] if text.strip() else []
    chunks = []
    current = []
    current_len = 0
    i = 0
    while i < len(paras):
        para = paras[i]
        if current and current_len + len(para) > CHUNK_MAX_CHARS:
            chunks.append("\n\n".join(current))
            overlap = current[-CHUNK_OVERLAP_PARAS:] if CHUNK_OVERLAP_PARAS > 0 else []
            current = list(overlap)
            current_len = sum(len(p) for p in current)
        current.append(para)
        current_len += len(para)
        i += 1
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def open_collection_rw():
    import zvec
    cfg = _resolve_embedding_cfg()
    schema = zvec.CollectionSchema(
        name=COLLECTION_NAME,
        vectors=zvec.VectorSchema("embedding", zvec.DataType.VECTOR_FP32, cfg["dim"]),
        fields=[
            zvec.FieldSchema("text", zvec.DataType.STRING),
            zvec.FieldSchema("doc_path", zvec.DataType.STRING),
        ],
    )
    zvec_dir = storage_dir() / "_collection"
    zvec_path = str(zvec_dir)
    storage_dir().mkdir(parents=True, exist_ok=True)

    lock_file = zvec_dir / "LOCK"
    if zvec_dir.exists() and not lock_file.exists():
        try:
            lock_file.touch()
        except Exception:
            pass

    if zvec_dir.exists():
        try:
            col = zvec.open(path=zvec_path)
            return col
        except Exception as e:
            print(f"  [warn] open 失败（{e}），删除重建 collection", flush=True)
            shutil.rmtree(zvec_dir)

    zvec_dir.mkdir(parents=True, exist_ok=True)
    zvec_dir.rmdir()
    col = zvec.create_and_open(path=zvec_path, schema=schema)
    return col


def _find_chunk_ids(collection, doc_path_val: str) -> list[str]:
    import zvec
    cfg = _resolve_embedding_cfg()
    try:
        results = collection.query(
            zvec.VectorQuery("embedding", vector=[0.0] * cfg["dim"]),
            topk=100000,
        )
    except Exception:
        return []
    ids = []
    for r in results:
        if isinstance(r, dict):
            if r.get("doc_path") == doc_path_val:
                ids.append(r.get("id", ""))
        else:
            fields = getattr(r, "fields", {}) or {}
            if fields.get("doc_path") == doc_path_val:
                ids.append(getattr(r, "id", "") or "")
    return [i for i in ids if i]


async def build(full: bool = False, dry_run: bool = False) -> None:
    print("=" * 60, flush=True)
    print("zvec 知识库构建", flush=True)
    print(f"  docs 目录 : {docs_dir()}", flush=True)
    print(f"  存储目录  : {storage_dir()}", flush=True)
    print(f"  模式      : {'全量重建' if full else '增量更新'}{'（dry-run）' if dry_run else ''}", flush=True)
    print(f"  块大小    : {CHUNK_MAX_CHARS} 字符，重叠 {CHUNK_OVERLAP_PARAS} 段", flush=True)
    print("-" * 60, flush=True)

    if full:
        zvec_dir = storage_dir() / "_collection"
        if zvec_dir.exists():
            if dry_run:
                print(f"  [dry-run] 会删除 {zvec_dir} 并重建", flush=True)
                return
            shutil.rmtree(zvec_dir)
            print("  已清空旧 collection", flush=True)
        manifest = {}
    else:
        manifest = load_manifest()

    files = scan_docs()
    print(f"  找到 {len(files)} 个文档", flush=True)
    if not files:
        print("  没有文档可处理，退出。", flush=True)
        return

    current_keys = set()
    added, modified, deleted, unchanged = [], [], [], []
    for f in files:
        key = doc_key(f)
        current_keys.add(key)
        stat = f.stat()
        info = manifest.get(key)
        if info is None:
            added.append((key, f))
        elif info["mtime"] != stat.st_mtime or info["size"] != stat.st_size:
            modified.append((key, f))
        else:
            unchanged.append(key)

    for key in list(manifest.keys()):
        if key not in current_keys:
            deleted.append(key)

    print(f"  manifest  : {len(manifest)} 个文件已索引", flush=True)
    print(f"\n>> 变化检测：", flush=True)
    print(f"  新增     : {len(added)}", flush=True)
    print(f"  修改     : {len(modified)}", flush=True)
    print(f"  删除     : {len(deleted)}", flush=True)
    print(f"  未变     : {len(unchanged)}", flush=True)

    if added:
        print(f"\n  新增文件：", flush=True)
        for k, _ in added:
            print(f"    + {k}", flush=True)
    if modified:
        print(f"\n  修改文件：", flush=True)
        for k, _ in modified:
            print(f"    ~ {k}", flush=True)
    if deleted:
        print(f"\n  删除文件：", flush=True)
        for k in deleted:
            print(f"    - {k}", flush=True)

    if not (added or modified or deleted):
        print("\n✓ 无变化，知识库已是最新。", flush=True)
        return

    if dry_run:
        print(f"\n[dry-run] 不实际执行，退出。", flush=True)
        return

    try:
        collection = open_collection_rw()
    except Exception as e:
        print(f"\n✗ 打开 collection 失败：{type(e).__name__}: {e}", flush=True)
        print(f"  可能原因：MCP server 正占用只读锁，请先停掉再重试。", flush=True)
        raise

    embed = build_embedding()

    if deleted:
        print(f"\n>> 处理删除...", flush=True)
        for key in deleted:
            info = manifest.pop(key, None)
            if info:
                for cid in info.get("chunk_ids", []):
                    try:
                        collection.delete([cid])
                    except Exception:
                        pass
                print(f"  - {key}  ({len(info.get('chunk_ids', []))} chunks)", flush=True)

    to_process = added + modified
    if to_process:
        print(f"\n>> 处理 {'新增+修改' if (added and modified) else ('新增' if added else '修改')}...", flush=True)
        embed_start = time.time()
        total_chunks = 0

        for idx, (key, f) in enumerate(to_process, 1):
            if key in manifest:
                old_ids = manifest[key].get("chunk_ids", [])
                for cid in old_ids:
                    try:
                        collection.delete([cid])
                    except Exception:
                        pass
                _find_chunk_ids(collection, key)

            text = f.read_text(encoding="utf-8")
            chunks = chunk_text(text)
            if not chunks:
                continue

            ids = [chunk_id(key, i) for i in range(len(chunks))]
            vecs = await embed(chunks)

            import zvec
            docs_to_upsert = [
                zvec.Doc(
                    id=ids[i],
                    vectors={"embedding": vecs[i]},
                    fields={"text": chunks[i], "doc_path": key},
                )
                for i in range(len(chunks))
            ]
            for start in range(0, len(docs_to_upsert), EMBED_BATCH):
                batch = docs_to_upsert[start:start + EMBED_BATCH]
                collection.upsert(batch)

            stat = f.stat()
            manifest[key] = {
                "mtime": stat.st_mtime,
                "size": stat.st_size,
                "chunk_ids": ids,
                "chunks": len(chunks),
            }
            total_chunks += len(chunks)
            tag = "+" if (key, f) in added else "~"
            print(f"  {tag} {key}  ({len(chunks)} chunks)", flush=True)

        elapsed = time.time() - embed_start
        print(f"\n  处理 {len(to_process)} 个文档 / {total_chunks} chunks，耗时 {elapsed:.1f}s", flush=True)

    save_manifest(manifest)
    total = sum(info.get("chunks", 0) for info in manifest.values())
    print(f"\n✓ 完成。共 {len(manifest)} 份文档 / {total} chunks。", flush=True)


def main():
    parser = argparse.ArgumentParser(description="zvec 知识库构建（增量更新）")
    parser.add_argument("--dry-run", action="store_true", help="只显示变化，不实际建库")
    parser.add_argument("--full", action="store_true", help="全量重建（先清空 zvec_data）")
    args = parser.parse_args()
    asyncio.run(build(full=args.full, dry_run=args.dry_run))


if __name__ == "__main__":
    main()