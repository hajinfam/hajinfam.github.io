import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY 가 설정되어 있지 않습니다. .env 를 확인하세요.")

client = OpenAI(api_key=OPENAI_API_KEY)

EXCEL_PATH = "products.xlsx"
OUTPUT_DIR = "site_products"

REQUIRED_COLUMNS = [
    "no",
    "productName",
    "productUrl",
    "mainImage",
    "shortTitle",
    "productDescription",
]

# 있으면 쓰고, 없어도 동작하도록 설계
OPTIONAL_COLUMNS = [
    "seoTitle",
    "seoDescription",
    "keywords",
    "category",
    "brand",
    "price",
    "currency",
    "sku",
    "relatedNos",
]

# ---------------------------------------
# Front Matter 파싱
# ---------------------------------------
FM_RE = re.compile(r"^---\s*(.*?)\s*---\s*", re.DOTALL)

def parse_front_matter(md_text: str) -> dict:
    m = FM_RE.match(md_text)
    if not m:
        return {}
    block = m.group(1)
    data = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip().strip('"')
    return data

def html_escape(s: str) -> str:
    return (
        str(s).replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;")
    )

def shorten(s: str, n: int) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"

def is_md_good_enough(existing_md: str, expected_no: int, expected_url: str) -> bool:
    """
    재호출 방지 기준(SEO 구조 반영):
    - product_no / product_url 일치
    - front matter description 존재
    - 본문에 네이버 친화 섹션(핵심 요약/스펙/FAQ) 중 2개 이상 존재
    """
    fm = parse_front_matter(existing_md)
    if not fm:
        return False

    try:
        no_ok = int(fm.get("product_no", "-1")) == int(expected_no)
    except Exception:
        no_ok = False

    url_ok = (fm.get("product_url", "").strip() == expected_url.strip())
    if not (no_ok and url_ok):
        return False

    has_desc = bool(fm.get("description", "").strip())
    h2_score = 0
    for marker in ["## 핵심 요약", "## 상품 스펙 한눈에 보기", "## 자주 묻는 질문", "## 구매 전 체크포인트"]:
        if marker in existing_md:
            h2_score += 1

    return has_desc and (h2_score >= 2)

# ---------------------------------------
# GPT: SEO Pack 생성
# --------------
