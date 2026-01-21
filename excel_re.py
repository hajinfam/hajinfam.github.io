import os
import time
import json
import re
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

import requests
from bs4 import BeautifulSoup


# =========================
# 사용자 설정
# =========================
XLSX_DIR = "xlsx"
OUTPUT_DIR = "re_xlsx"

DISCOUNT_COL = "discountedRate"
PRODUCTNAME_COL = "productName"

BLOGTITLE_COLS = ["blogTitle1", "blogTitle2", "blogTitle3"]

URL_COL = "productUrl"     # 없으면 URL 힌트 기능 자동 스킵
STORE_COL = "storeName"    # 없으면 자동 스킵

DISCOUNT_THRESHOLD = 30

MODEL = "gpt-4.1-mini"
API_SLEEP_SEC = 0.25

FETCH_URL_HINTS = True
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
# 파일 선택 UI
# =========================
def list_xlsx_files(xlsx_dir: str) -> List[str]:
    if not os.path.isdir(xlsx_dir):
        return []
    files = []
    for f in os.listdir(xlsx_dir):
        if f.lower().endswith(".xlsx") and not f.startswith("~$"):
            files.append(f)

    def sort_key(name: str) -> Tuple[int, int, str]:
        m = re.match(r"^(\d+)\.xlsx$", name)
        if m:
            return (0, int(m.group(1)), "")
        return (1, 0, name.lower())

    files.sort(key=sort_key)
    return files


def choose_file_interactive(files: List[str]) -> str:
    if not files:
        raise FileNotFoundError("xlsx 폴더에 .xlsx 파일이 없습니다.")

    print("\n[xlsx 파일 선택]")
    for i, f in enumerate(files, start=1):
        print(f"{i}. {f}")

    while True:
        sel = input("번호를 입력하세요 (예: 1): ").strip()
        if not sel.isdigit():
            print("숫자만 입력하세요.")
            continue
        idx = int(sel)
        if 1 <= idx <= len(files):
            return files[idx - 1]
        print("범위를 벗어났습니다. 다시 입력하세요.")


def extract_date_token(filename: str) -> str:
    """
    파일명에서 날짜 토큰 추출
    - '0119.xlsx' -> '0119'
    - 'products_0119.xlsx' -> '0119'
    - 'rename0119.xlsx' -> '0119' (숫자 4자리 우선)
    못 찾으면 확장자 제외 basename 반환
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    m = re.search(r"(\d{4})", base)
    if m:
        return m.group(1)
    return base


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# =========================
# URL 힌트(토큰 절감형)
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

        hints = {}
        if og_title:
            hints["og_title"] = og_title
        if title and title != og_title:
            hints["title"] = title

        return hints

    except Exception:
        return {}


# =========================
# OpenAI 호출 (1회)
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

    hint_line = ""
    if url_hints:
        parts = []
        if url_hints.get("og_title"):
            parts.append(f"og_title={url_hints['og_title']}")
        if url_hints.get("title"):
            parts.append(f"title={url_hints['title']}")
        if parts:
            hint_line = "URL힌트: " + " | ".join(parts)

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

    try:
        data = json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        data = json.loads(m.group(0)) if m else {}

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

    for k in ["blogTitle1", "blogTitle2", "blogTitle3"]:
        if out[k] == original_name:
            out[k] = ""

    return out


# =========================
# ✅ 안정장치 포함 저장
# =========================
def save_split_excels_safe(df: pd.DataFrame, date_token: str, out_dir: str) -> None:
    """
    1) productName=blogTitle1 (빈 값이면 원본 productName 유지) -> products_<date>.xlsx
    2) productName=blogTitle2 (빈 값이면 원본 productName 유지) -> 3600_<date>.xlsx
    3) productName=blogTitle3 (빈 값이면 원본 productName 유지) -> 5600_<date>.xlsx
    그리고 blogTitle1~3 컬럼은 삭제
    """
    ensure_dir(out_dir)

    # 원본 productName 백업 (치환 전에 반드시 확보)
    if PRODUCTNAME_COL not in df.columns:
        raise KeyError(f"{PRODUCTNAME_COL} 컬럼이 없습니다.")
    original_productname = df[PRODUCTNAME_COL].fillna("").astype(str)

    mapping = [
        ("blogTitle1", f"products_{date_token}.xlsx"),
        ("blogTitle2", f"3600_{date_token}.xlsx"),
        ("blogTitle3", f"5600_{date_token}.xlsx"),
    ]

    for src_col, filename in mapping:
        if src_col not in df.columns:
            raise KeyError(f"{src_col} 컬럼이 없습니다. 저장 분기 불가.")

        out_df = df.copy()

        # blogTitleN을 productName으로 치환하되, 빈 값이면 원본 유지
        candidate = out_df[src_col].fillna("").astype(str).str.strip()
        out_df[PRODUCTNAME_COL] = candidate.where(candidate != "", original_productname)

        # blogTitle1~3 삭제
        out_df = out_df.drop(columns=[c for c in BLOGTITLE_COLS if c in out_df.columns], errors="ignore")

        out_path = os.path.join(out_dir, filename)
        out_df.to_excel(out_path, index=False)
        print(f"[DONE] 분리 저장 완료: {out_path} (빈 타이틀은 원본 productName 유지)")


# =========================
# 메인
# =========================
def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 없습니다. .env를 확인하세요.")

    files = list_xlsx_files(XLSX_DIR)
    chosen = choose_file_interactive(files)
    input_path = os.path.join(XLSX_DIR, chosen)

    date_token = extract_date_token(chosen)

    print(f"\n[INFO] 입력 파일: {input_path}")
    print(f"[INFO] 날짜 토큰: {date_token}")
    print(f"[INFO] 출력 폴더: {OUTPUT_DIR}\n")

    client = OpenAI(api_key=api_key)

    df = pd.read_excel(input_path)

    for col in [DISCOUNT_COL, PRODUCTNAME_COL]:
        if col not in df.columns:
            raise KeyError(f"'{col}' 컬럼이 없습니다. 현재 컬럼: {list(df.columns)}")

    for col in BLOGTITLE_COLS:
        if col not in df.columns:
            df[col] = ""

    df[DISCOUNT_COL] = pd.to_numeric(df[DISCOUNT_COL], errors="coerce").fillna(0)
    before = len(df)
    df = df[df[DISCOUNT_COL] >= DISCOUNT_THRESHOLD].copy()
    after = len(df)
    print(f"[INFO] 원본 {before}행 → 유지 {after}행 (할인율 {DISCOUNT_THRESHOLD}% 이상)")

    cache: Dict[str, Dict[str, Any]] = {}

    processed = 0
    for idx in df.index:
        original_name = str(df.at[idx, PRODUCTNAME_COL]).strip()
        if not original_name:
            continue

        existing = [str(df.at[idx, c]).strip() for c in BLOGTITLE_COLS]
        if all(existing):
            continue

        store_name = str(df.at[idx, STORE_COL]).strip() if STORE_COL in df.columns else ""

        url_hints = {}
        if FETCH_URL_HINTS and (URL_COL in df.columns):
            url = str(df.at[idx, URL_COL]).strip()
            if url:
                url_hints = fetch_url_hints_min(url)

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

        df.at[idx, "blogTitle1"] = result.get("blogTitle1", "")
        df.at[idx, "blogTitle2"] = result.get("blogTitle2", "")
        df.at[idx, "blogTitle3"] = result.get("blogTitle3", "")

        processed += 1
        if processed % 20 == 0:
            print(f"[INFO] 처리 진행: {processed}개 완료")

    print(f"[DONE] 타이틀 생성 완료. 처리된 상품 수: {processed}")
    print(f"[DONE] 캐시 적중 포함, 총 캐시 키 수: {len(cache)}")

    # ✅ 안정장치 포함: 3개 파일로 분리 저장
    save_split_excels_safe(df=df, date_token=date_token, out_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
