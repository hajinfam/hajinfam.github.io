import os
import time
import json
import re
from typing import Dict, Any, Optional

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

import requests
from bs4 import BeautifulSoup


# =========================
# 사용자 설정
# =========================
INPUT_XLSX = "0118.xlsx"
OUTPUT_XLSX = "rename0118.xlsx"

DISCOUNT_COL = "discountedRate"
PRODUCTNAME_COL = "productName"

BLOGTITLE_COLS = ["blogTitle1", "blogTitle2", "blogTitle3"]

URL_COL = "productUrl"     # 없으면 URL 힌트 기능 자동 스킵
STORE_COL = "storeName"    # 없으면 자동 스킵

DISCOUNT_THRESHOLD = 30

MODEL = "gpt-4.1-mini"     # 사용 환경에 맞게 변경 가능
API_SLEEP_SEC = 0.25       # 과호출 방지 (상황에 맞게 조절)

FETCH_URL_HINTS = True     # URL 접근 차단 많으면 False 권장
URL_TIMEOUT_SEC = 7


# =========================
# 공통 유틸
# =========================
BANNED_HINTS = ["최저가", "무조건", "대박", "충격", "1위", "공짜", "무료증정", "100%", "환불"]

def post_clean(text: str) -> str:
    if not isinstance(text, str):
        return ""
    out = text.strip()
    out = re.sub(r'^[\'"\s]+|[\'"\s]+$', "", out)
    for w in BANNED_HINTS:
        out = out.replace(w, "").strip()
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def safe_clip(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s[:n]


# =========================
# URL 힌트(토큰 절감형)
# - og:title, title 정도만 (설명까지 넣으면 토큰 증가)
# =========================
def fetch_url_hints_min(url: str, timeout: int = URL_TIMEOUT_SEC) -> Dict[str, str]:
    if not isinstance(url, str) or not url.strip():
        return {}
    url = url.strip()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code != 200 or not r.text:
            return {}

        soup = BeautifulSoup(r.text, "lxml")

        og_title = ""
        tag = soup.find("meta", attrs={"property": "og:title"})
        if tag and tag.get("content"):
            og_title = tag["content"].strip()

        title = soup.title.get_text(strip=True) if soup.title else ""

        og_title = safe_clip(og_title, 90)
        title = safe_clip(title, 90)

        # 둘 다 없으면 빈 dict
        hints = {}
        if og_title:
            hints["og_title"] = og_title
        if title and title != og_title:
            hints["title"] = title

        return hints

    except Exception:
        return {}


# =========================
# OpenAI (구버전 SDK: chat.completions)
# - 1회 호출: keywords + title3개
# - JSON only 강제 + 깨질 경우 최소 복구
# =========================
def kw_and_3titles_one_call(
    client: OpenAI,
    original_name: str,
    store_name: str = "",
    url_hints: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    original_name = (original_name or "").strip()
    store_name = (store_name or "").strip()
    url_hints = url_hints or {}

    # ✅ 토큰 절감: 힌트가 없으면 프롬프트에 섹션 자체를 넣지 않음
    hint_line = ""
    if url_hints:
        # 아주 짧게
        # 예: "URL힌트: og_title=..., title=..."
        parts = []
        if url_hints.get("og_title"):
            parts.append(f"og_title={url_hints['og_title']}")
        if url_hints.get("title"):
            parts.append(f"title={url_hints['title']}")
        if parts:
            hint_line = "URL힌트: " + " | ".join(parts)

    # ✅ 토큰 절감: 규칙은 짧고 강하게(핵심만)
    # - keywords 3개 추출 후, 각 제목에 1~2개 포함 강제
    # - 제목은 소개형 문장, 나열 금지
    # - JSON only
    prompt = (
        "원본 상품명에서 구매결정에 중요한 핵심 키워드 3개를 뽑고,\n"
        "그 키워드 중 1~2개를 각 제목에 자연스럽게 포함해 블로그 제목 3개를 만들어라.\n"
        "제목은 쇼핑몰처럼 나열하지 말고 사람이 소개하는 문장 1줄.\n"
        "과장/낚시(최저가/대박/무조건/1위/공짜/100%) 금지.\n"
        "제목 3개는 관점을 다르게(착용/통화/출퇴근/운동/휴대 등).\n"
        "길이 18~32자 권장(최대 38자).\n"
        "출력은 JSON만:\n"
        '{"keywords":["...","...","..."],"blogTitle1":"...","blogTitle2":"...","blogTitle3":"..."}\n'
        f"\n원본: {original_name}\n"
    )

    # store/url 힌트도 “있을 때만” 붙임
    if store_name:
        prompt += f"스토어명: {store_name}\n"
    if hint_line:
        prompt += hint_line + "\n"

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Return only valid JSON. No extra text."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    text = (resp.choices[0].message.content or "").strip()

    # JSON 복구 파싱
    data = None
    try:
        data = json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            data = json.loads(m.group(0))
        else:
            data = {}

    keywords = data.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []
    keywords = [str(k).strip() for k in keywords if str(k).strip()][:3]

    out = {
        "keywords": keywords,
        "blogTitle1": post_clean(str(data.get("blogTitle1", ""))),
        "blogTitle2": post_clean(str(data.get("blogTitle2", ""))),
        "blogTitle3": post_clean(str(data.get("blogTitle3", ""))),
    }

    # 원본 그대로 복사 방지 + 빈값 방지 최소 안전망
    for k in ["blogTitle1", "blogTitle2", "blogTitle3"]:
        if out[k] == original_name:
            out[k] = ""

    return out


# =========================
# 메인
# =========================
def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 없습니다. .env를 확인하세요.")

    client = OpenAI(api_key=api_key)

    if not os.path.exists(INPUT_XLSX):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {INPUT_XLSX}")

    df = pd.read_excel(INPUT_XLSX)

    # 필수 컬럼 확인
    for col in [DISCOUNT_COL, PRODUCTNAME_COL]:
        if col not in df.columns:
            raise KeyError(f"'{col}' 컬럼이 없습니다. 현재 컬럼: {list(df.columns)}")

    # blogTitle1~3 컬럼 생성
    for col in BLOGTITLE_COLS:
        if col not in df.columns:
            df[col] = ""

    # discountedRate 숫자화 후 필터링(행 삭제)
    df[DISCOUNT_COL] = pd.to_numeric(df[DISCOUNT_COL], errors="coerce").fillna(0)
    before = len(df)
    df = df[df[DISCOUNT_COL] >= DISCOUNT_THRESHOLD].copy()
    after = len(df)

    print(f"[INFO] 원본 {before}행 → 유지 {after}행 (할인율 {DISCOUNT_THRESHOLD}% 이상)")

    # ✅ 토큰 절감: productName 중복 캐시
    cache: Dict[str, Dict[str, Any]] = {}

    # 처리
    processed = 0
    for idx in df.index:
        original_name = str(df.at[idx, PRODUCTNAME_COL]).strip()
        if not original_name:
            continue

        # 이미 3개 타이틀이 모두 채워져 있으면 스킵하고 싶다면(선택)
        existing = [str(df.at[idx, c]).strip() for c in BLOGTITLE_COLS]
        if all(existing):
            continue

        store_name = str(df.at[idx, STORE_COL]).strip() if STORE_COL in df.columns else ""

        # URL 힌트(있을 때만)
        url_hints = {}
        if FETCH_URL_HINTS and (URL_COL in df.columns):
            url = str(df.at[idx, URL_COL]).strip()
            if url:
                url_hints = fetch_url_hints_min(url)

        # 캐시 사용
        cache_key = f"{original_name}||{store_name}||{url_hints.get('og_title','')}||{url_hints.get('title','')}"
        if cache_key in cache:
            result = cache[cache_key]
        else:
            result = kw_and_3titles_one_call(
                client=client,
                original_name=original_name,
                store_name=store_name,
                url_hints=url_hints,
            )
            cache[cache_key] = result
            time.sleep(API_SLEEP_SEC)

        # 반영(기존 값이 비어있을 때만 채우게 하려면 where로 바꿔도 됨)
        df.at[idx, "blogTitle1"] = result.get("blogTitle1", "")
        df.at[idx, "blogTitle2"] = result.get("blogTitle2", "")
        df.at[idx, "blogTitle3"] = result.get("blogTitle3", "")

        processed += 1
        if processed % 20 == 0:
            print(f"[INFO] 처리 진행: {processed}개 완료")

    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"[DONE] 저장 완료: {OUTPUT_XLSX}")
    print(f"[DONE] 처리된 상품 수: {processed}")
    print(f"[DONE] 캐시 적중 포함, 총 캐시 키 수: {len(cache)}")


if __name__ == "__main__":
    main()
