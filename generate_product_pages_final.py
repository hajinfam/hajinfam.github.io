# generate_product_pages_final.py
import os
import re
import json
import unicodedata
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(REPO_ROOT, "products.xlsx")
OUT_DIR = os.path.join(REPO_ROOT, "site_products")

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SAVE_EVERY_N = 50

# 운영 안전장치
SKIP_IF_MD_EXISTS = True

# products.xlsx 컬럼
COL_NO = "no"
COL_NAME = "productName"
COL_URL = "productUrl"
COL_IMAGE = "mainImage"

COL_SHORT = "shortTitle"
COL_PDESC = "productDescription"
COL_SEO_TITLE = "seoTitle"
COL_SEO_DESC = "seoDescription"
COL_KEYWORDS = "keywords"
COL_CATEGORY = "category"


def norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u200b", "").replace("\ufeff", "")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def safe_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()


def to_int_safe(x) -> int:
    try:
        return int(str(x).strip())
    except Exception:
        return 0


def ensure_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df


def md_filename(no_int: int) -> str:
    if 0 < no_int < 100:
        return f"product_{no_int:03d}.md"
    return f"product_{no_int}.md"


def md_path(no_int: int) -> str:
    return os.path.join(OUT_DIR, md_filename(no_int))


def permalink_for(no_int: int) -> str:
    return f"/site_products/product_{no_int}/"


def build_prompt(no_int: int, product_name: str) -> str:
    return f"""
당신은 한국어 콘텐츠/SEO 에디터입니다.
아래 상품에 대해 "정보 제공" 톤으로 작성하세요.
직접적인 구매 유도 문구(예: 지금 구매, 구매하세요, 초특가, 한정수량, 품절임박 등)는 금지합니다.

[상품]
- no: {no_int}
- 상품명: {product_name}

[출력 형식: JSON만]
{{
  "seoTitle": "40~55자 내외, 정보형 SEO 제목",
  "seoDescription": "80~120자 내외, 요약 설명",
  "category": "1~2단어",
  "keywords": "쉼표로 구분된 키워드 5~10개",
  "h1_name": "H1에 사용할 짧은 상품명(예: 따뜻한 기모 조거팬츠)",
  "core_summary": "## 핵심 요약에 들어갈 한 단락",
  "recommend_bullets": ["추천 포인트 5개(각 1줄)"],
  "specs": [
    {{"k":"소재","v":"..." }},
    {{"k":"색상","v":"..." }},
    {{"k":"사이즈","v":"..." }},
    {{"k":"세탁방법","v":"..." }},
    {{"k":"제조국","v":"..." }}
  ],
  "faq": [
    {{"q":"...","a":"..." }},
    {{"q":"...","a":"..." }},
    {{"q":"...","a":"..." }}
  ],
  "shortTitle": "15~25자 내외",
  "productDescription": "60~120자 내외, 정보형 설명"
}}
""".strip()


def call_gpt_json(client: OpenAI, prompt: str) -> Dict:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )
    text = resp.choices[0].message.content.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()

    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if not m:
            raise ValueError(f"[ERROR] GPT output not JSON:\n{text}")
        return json.loads(m.group(0))


def write_md_like_old(
    no_int: int,
    seo_title: str,
    seo_desc: str,
    h1_name: str,
    category: str,
    keywords_csv: str,
    product_url: str,
    image_url: str,
    core_summary: str,
    bullets: List[str],
    specs: List[Dict[str, str]],
    faq: List[Dict[str, str]],
):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = md_path(no_int)

    if SKIP_IF_MD_EXISTS and os.path.exists(path):
        return

    bullets = [norm(b) for b in bullets if norm(b)]
    while len(bullets) < 5:
        bullets.append("제품 특성과 사용 환경을 고려해 선택 기준을 정리해드립니다.")
    bullets = bullets[:5]

    cleaned_specs = []
    for item in specs:
        k = norm(str(item.get("k", "")))
        v = norm(str(item.get("v", "")))
        if k and v:
            cleaned_specs.append({"k": k, "v": v})

    default_keys = ["소재", "색상", "사이즈", "세탁방법", "제조국"]
    have = {s["k"] for s in cleaned_specs}
    for dk in default_keys:
        if dk not in have and len(cleaned_specs) < 5:
            cleaned_specs.append({"k": dk, "v": "판매 페이지 정보를 확인하세요."})
    cleaned_specs = cleaned_specs[:5]

    cleaned_faq = []
    for item in faq:
        q = norm(str(item.get("q", "")))
        a = norm(str(item.get("a", "")))
        if q and a:
            cleaned_faq.append({"q": q, "a": a})
    while len(cleaned_faq) < 3:
        cleaned_faq.append({"q": "사용/관리 시 주의할 점이 있나요?", "a": "상품 상세의 안내 및 라벨 표기를 확인하는 것을 권장합니다."})
    cleaned_faq = cleaned_faq[:3]

    spec_rows = "\n".join([f"| {s['k']} | {s['v']} |" for s in cleaned_specs])

    md = f"""---
title: "{norm(seo_title)}"
description: "{norm(seo_desc)}"
product_no: {no_int}
product_name: "{norm(h1_name)}"
category: "{norm(category)}"
keywords: "{norm(keywords_csv)}"
product_url: "{norm(product_url)}"
image_url: "{norm(image_url)}"
permalink: "{permalink_for(no_int)}"
sitemap: show
noindex: false
---

# {no_int}번. {norm(h1_name)}

![{norm(h1_name)}]({norm(image_url)})

## 핵심 요약
{norm(core_summary)}

## 이런 분께 추천
- {bullets[0]}
- {bullets[1]}
- {bullets[2]}
- {bullets[3]}
- {bullets[4]}

## 상품 스펙 한눈에 보기
| 구분 | 상세 설명 |
| --- | --- |
{spec_rows}

## 구매 전 체크포인트
- 가격/재고/구성은 판매 페이지 기준으로 수시 변동될 수 있어요.
- 배송/교환/반품 정책를 결제 전 꼭 확인하세요.

## 자주 묻는 질문(FAQ)
**Q. {cleaned_faq[0]['q']}**

A. {cleaned_faq[0]['a']}

**Q. {cleaned_faq[1]['q']}**

A. {cleaned_faq[1]['a']}

**Q. {cleaned_faq[2]['q']}**

A. {cleaned_faq[2]['a']}

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{norm(h1_name)}",
  "image": ["{norm(image_url)}"],
  "description": "{norm(seo_desc)}",
  "brand": {{"@type":"Brand","name":"hajinfam"}},
  "url": "{norm(product_url)}"
}}
</script>

[← 상품 모아보기로 돌아가기](/site_products/)

<div style="margin-top:18px;padding:18px;border:2px solid #10b981;border-radius:14px;background:#ecfdf5;text-align:center;font-weight:700;color:#047857;font-size:15px;line-height:1.6;">
최신 혜택/재고는 판매 페이지에서 확인하세요.<br/>
<a href="{norm(product_url)}" rel="nofollow sponsored" style="color:#065f46;text-decoration:none;font-weight:800;">최대 할인 확인하기 →</a>
</div>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)


def main():
    if not os.path.exists(EXCEL_PATH):
        raise RuntimeError(f"[ERROR] products.xlsx not found: {EXCEL_PATH}")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("[ERROR] OPENAI_API_KEY 환경변수가 없습니다(.env 확인).")

    client = OpenAI(api_key=api_key)

    df = pd.read_excel(EXCEL_PATH)
    df = ensure_columns(df, [
        COL_NO, COL_NAME, COL_URL, COL_IMAGE,
        COL_SHORT, COL_PDESC, COL_SEO_TITLE, COL_SEO_DESC,
        COL_KEYWORDS, COL_CATEGORY
    ])

    # 빈 칼럼 대상만 처리(비용/시간 최적)
    def _s(col):
        return df[col].fillna("").astype(str).str.strip()

    mask_need = (
        (_s(COL_URL) != "") &
        (
            (_s(COL_SEO_TITLE) == "") |
            (_s(COL_SEO_DESC) == "") |
            (_s(COL_KEYWORDS) == "") |
            (_s(COL_CATEGORY) == "") |
            (_s(COL_PDESC) == "") |
            (_s(COL_SHORT) == "")
        )
    )
    targets = df.index[mask_need].tolist()

    print(f"[START] total_rows={len(df)}, need_fill={len(targets)}, model={MODEL}")
    if not targets:
        print("[DONE] 채울 대상이 없습니다.")
        return

    updated = 0
    for idx in targets:
        no_int = to_int_safe(df.loc[idx, COL_NO])
        name = safe_str(df.loc[idx, COL_NAME])
        url = safe_str(df.loc[idx, COL_URL])
        img = safe_str(df.loc[idx, COL_IMAGE])

        if no_int <= 0 or not name or not url:
            continue

        # 기존 md 있으면 건드리지 않음
        if SKIP_IF_MD_EXISTS and os.path.exists(md_path(no_int)):
            continue

        data = call_gpt_json(client, build_prompt(no_int, name))

        df.loc[idx, COL_SEO_TITLE] = safe_str(data.get("seoTitle", ""))
        df.loc[idx, COL_SEO_DESC] = safe_str(data.get("seoDescription", ""))
        df.loc[idx, COL_CATEGORY] = safe_str(data.get("category", ""))
        df.loc[idx, COL_KEYWORDS] = safe_str(data.get("keywords", ""))
        df.loc[idx, COL_SHORT] = safe_str(data.get("shortTitle", ""))
        df.loc[idx, COL_PDESC] = safe_str(data.get("productDescription", ""))

        h1_name = safe_str(data.get("h1_name", "")) or name
        core_summary = safe_str(data.get("core_summary", "")) or safe_str(df.loc[idx, COL_PDESC]) or "핵심 포인트를 정리해드립니다."
        bullets = data.get("recommend_bullets", []) or []
        specs = data.get("specs", []) or []
        faq = data.get("faq", []) or []

        write_md_like_old(
            no_int=no_int,
            seo_title=safe_str(df.loc[idx, COL_SEO_TITLE]),
            seo_desc=safe_str(df.loc[idx, COL_SEO_DESC]),
            h1_name=h1_name,
            category=safe_str(df.loc[idx, COL_CATEGORY]),
            keywords_csv=safe_str(df.loc[idx, COL_KEYWORDS]),
            product_url=url,
            image_url=img,
            core_summary=core_summary,
            bullets=bullets,
            specs=specs,
            faq=faq,
        )

        updated += 1
        if updated % SAVE_EVERY_N == 0:
            df.to_excel(EXCEL_PATH, index=False)
            print(f"[SAVE] {updated}/{len(targets)}")
        if updated % 10 == 0:
            print(f"[PROGRESS] {updated}/{len(targets)}")

    df.to_excel(EXCEL_PATH, index=False)
    print(f"[DONE] md_written={updated}/{len(targets)}")
    print(f"[OK] out_dir={OUT_DIR}")


if __name__ == "__main__":
    main()
