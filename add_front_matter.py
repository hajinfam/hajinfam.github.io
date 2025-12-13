import os
import re

TARGET_DIR = "site_products"

def has_front_matter(text: str) -> bool:
    return text.lstrip().startswith("---")

def infer_title(filename: str, body: str) -> str:
    # 1) 본문 첫 줄에서 제목 추출 시도
    for line in body.splitlines():
        line = line.strip()
        if line and len(line) < 60:
            return line

    # 2) 실패 시 파일명 기반
    m = re.search(r"product[_\- ]*(\d+)", filename)
    if m:
        return f"{int(m.group(1))}번 상품"
    return filename.replace(".md", "")

for fname in os.listdir(TARGET_DIR):
    if not fname.endswith(".md"):
        continue
    if fname == "index.md":
        continue

    path = os.path.join(TARGET_DIR, fname)

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if has_front_matter(content):
        print(f"[SKIP] 이미 Front Matter 존재: {fname}")
        continue

    title = infer_title(fname, content)
    description = f"{title} 상세 정보 및 구매 링크를 확인하세요."

    front_matter = f"""---
title: "{title}"
description: "{description}"
sitemap: true
noindex: false
---

"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(front_matter + content)

    print(f"[OK] Front Matter 추가됨: {fname}")