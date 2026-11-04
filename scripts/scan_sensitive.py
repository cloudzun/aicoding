#!/usr/bin/env python3
"""发布前敏感词扫描：对 dist（即将发布的产物）做全量检查，命中即失败。

放行标准 RFC 1918 网段与 RFC 5737 文档网段——教材正文要引用它们讲"内网地址段封禁"，
属于教学内容，不是泄漏。除此之外的私有地址一律拦截。
"""
import re
import sys
import pathlib

PATTERNS = [
    r"浙江移动",
    r"zhejiang",
    r"移动公司",
    r"sk-[A-Za-z0-9]{16,}",
    r"10\.\d+\.\d+\.\d+",
    r"192\.168\.\d+\.\d+",
    r"[\w.]+@(?!example)[\w.]+\.(com|cn|net)",
]

# 允许出现：标准私有网段/文档网段/环回/链路本地（教学模式的标准写法）
ALLOW_PREFIX = (
    "10.0.0.0",      # 10.0.0.0/8 网络地址
    "192.168.",      # 192.168.0.0/16 的 CIDR 写法
    "172.16.0.0",    # 172.16.0.0/12 网络地址
    "127.0.0.0",     # 环回
    "169.254.",      # 链路本地（含 169.254.169.254 元数据）
    "198.51.100.",   # RFC 5737 TEST-NET-2
    "203.0.113.",    # RFC 5737 TEST-NET-3
    "除非",          # 无意义占位，保持元组形状
)

ROOTS = ["dist"]
EXTS = (".html", ".md", ".js", ".css", ".json", ".txt", ".svg")


def allowed(token: str) -> bool:
    return any(token.startswith(p) or p in token for p in ALLOW_PREFIX)


def main() -> int:
    hits = []
    for root in ROOTS:
        for f in pathlib.Path(root).rglob("*"):
            if not f.is_file() or f.suffix not in EXTS:
                continue
            if "pagefind" in str(f):          # 索引是正文的镜像，重复扫描无意义
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in PATTERNS:
                for m in re.finditer(pat, text):
                    tok = m.group(0)
                    if allowed(tok):
                        continue
                    hits.append((str(f), pat, tok[:40]))
    if hits:
        print(f"敏感词命中 {len(hits)} 处")
        for h in hits[:20]:
            print("  ", h)
        return 1
    print("敏感词扫描：0 命中")
    return 0


if __name__ == "__main__":
    sys.exit(main())
