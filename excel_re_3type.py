import os
import re
import json
import time
import hashlib
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from zoneinfo import ZoneInfo
import datetime as dt

from openai import OpenAI
from pathlib import Path

# =========================
# 설정(필요시 여기만 수정)
# =========================
XLSX_DIR = "xlsx"
OUT_DIR = "re_xlsx"
CACHE_PATH = "_cache/titlepack_cache.jsonl"

# 입력 엑셀 컬럼명(당신 기존 시트 기준)
COL_PRODUCT_NAME = "productName"
COL_PRODUCT_URL = "productUrl"
COL_DISCOUNT = "discountedRate"

# 있으면 쓰고, 없으면 비어도 됨
COL_BRAND = "brand"
COL_CATEGORY = "category"
COL_DESC = "productDesc"   # 없으면 아래 후보 컬럼에서 자동 탐색
COL_FEATURES = "features"  # 없으면 아래 후보 컬럼에서 자동 탐색
COL_PRICE = "price"

DESC_CANDIDATES = ["productDesc", "description", "desc", "summary", "content"]
FEATURE_CANDIDATES = ["features", "spec", "specs", "keywords", "tags"]

# 출력 파일명 prefix
OUT_PREFIX_INFO = "products"  # blogTitle1(정보형)
OUT_PREFIX_COMPARE = "3600"   # blogTitle2(비교형)
OUT_PREFIX_PROBLEM = "5600"   # blogTitle3(문제해결형)

# 타이틀 길이
TITLE_MAX_LEN = 38

# GPT 호출 설정
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = 0.4
ROW_SLEEP_SEC = 0.8
MAX_RETRIES = 3


# =========================
# Structured Outputs schema
# =========================
class TitlePack(BaseModel):
    info: str = Field(..., description="정보형 타이틀")
    compare: str = Field(..., description="비교형 타이틀")
    problem: str = Field(..., description="문제해결형 타이틀")

    @field_validator("info", "compare", "problem")
    @classmethod
    def clean(cls, v: str) -> str:
        v = re.sub(r"\s+", " ", (v or "").strip())
        return v


# =========================
# 유틸
# =========================
def norm(x: Any) -> str:
    return "" if x is None else str(x).strip()

def pick_first_nonempty(row: pd.Series, candidates: List[str]) -> str:
    for c in candidates:
        if c in row and norm(row[c]):
            return norm(row[c])
    return ""

def sha1_key(*parts: str) -> str:
    joined = "\n".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha1(joined).hexdigest()

def load_cache(path: str) -> Dict[str, Dict[str, str]]:
    if not os.path.exists(path):
        return {}
    data: Dict[str, Dict[str, str]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                k = obj.get("key")
                v = obj.get("value")
                if k and isinstance(v, dict):
                    data[k] = v
            except Exception:
                continue
    return data

def append_cache(path: str, key: str, value: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")

def ensure_dirs() -> None:
    os.makedirs(XLSX_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

def list_xlsx_files() -> List[str]:
    files = []
    for fn in os.listdir(XLSX_DIR):
        if fn.lower().endswith(".xlsx") and not fn.startswith("~$"):
            files.append(fn)
    files.sort()
    return files

def choose_file_interactive(files: List[str]) -> str:
    print("\n[xlsx 폴더 파일 목록]")
    for i, fn in enumerate(files, start=1):
        print(f"{i:>2}. {fn}")
    print()

    while True:
        sel = input("처리할 엑셀 번호를 입력하세요: ").strip()
        if not sel.isdigit():
            print("숫자만 입력하세요.")
            continue
        idx = int(sel)
        if 1 <= idx <= len(files):
            return os.path.join(XLSX_DIR, files[idx - 1])
        print("범위를 벗어났습니다. 다시 입력하세요.")

def today_mmdd_seoul() -> str:
    now = dt.datetime.now(tz=ZoneInfo("Asia/Seoul"))
    return now.strftime("%m%d")

def suffix_from_input_filename_exact(input_path: str) -> str:
    """
    xlsx에 넣은 파일명 그대로(stem) 반환
    예:
      xlsx/0121.xlsx     -> '0121'
      xlsx/0120(1).xlsx  -> '0120(1)'
    """
    return Path(input_path).stem

def trim_title(t: str, max_len: int) -> str:
    t = t.strip()
    # 너무 길면 최후 수단으로 자르되, 가능하면 약간 여유를 둠
    return t if len(t) <= max_len + 6 else t[: max_len + 6].rstrip()

def simple_norm_title(t: str) -> str:
    return re.sub(r"[\s\|\:\-]+", "", t.lower())


# =========================
# GPT 타이틀 생성
# =========================
def generate_titles_3types(
    client: OpenAI,
    model: str,
    product_name: str,
    brand: str,
    category: str,
    desc: str,
    features: str,
    price: str,
    discount: str,
    max_len: int = TITLE_MAX_LEN,
    temperature: float = TEMPERATURE,
    max_retries: int = MAX_RETRIES,
) -> TitlePack:

    instructions = f"""
너는 한국어 커머스/어필리에이트 콘텐츠용 '제목(타이틀)' 생성기다.
아래 제품 정보를 바탕으로 서로 의도가 완전히 다른 제목 3개를 만들어라.

공통 규칙:
- 한국어로 작성.
- 각 제목은 {max_len}자 내외(가능하면 {max_len}자 이하), 너무 길지 않게.
- 과장/허위/단정 표현 금지(예: '무조건', '최고', '완벽', '100%', '의사도 추천' 등).
- '최저가', '대박', '핫딜' 같은 광고 냄새 단어는 가급적 쓰지 말 것.
- 특수문자 남발 금지(!!, ★, ▶ 등). 구분자는 '｜' 또는 ':' 정도만 허용.
- 제품명에서 핵심 키워드(속성/용도/카테고리)를 1~2개는 포함해 검색 적합성 유지.

타입별 규칙:
1) info (정보형):
- "선택 기준", "정리", "가이드", "장단점" 같이 학습/기준 신호를 준다.
- 특정 브랜드 찬양이 아니라 '기준' 중심.

2) compare (비교형):
- "추천", "TOP", "비교", "고르는 법"처럼 선택 압축 신호.
- 경쟁사/경쟁모델 실명은 정보가 없으면 임의로 만들지 말 것.

3) problem (문제해결형):
- 사용자의 불편/문제를 1개 제시하고 해결을 암시.
- 제품/카테고리와 무관한 문제는 만들지 말 것.

출력은 스키마에 맞춰 info/compare/problem 3개만.
""".strip()

    user_content = f"""
[제품 정보]
- 제품명: {product_name}
- 브랜드: {brand}
- 카테고리: {category}
- 설명/요약: {desc}
- 특징/스펙: {features}
- 가격/할인(있으면 참고): 가격={price}, 할인={discount}
""".strip()

    last_err: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.responses.parse(
                model=model,
                instructions=instructions,
                input=[{"role": "user", "content": user_content}],
                text_format=TitlePack,
                temperature=temperature,
            )
            pack: TitlePack = resp.output_parsed

            # 후처리/안정장치
            pack = TitlePack(
                info=trim_title(pack.info, max_len),
                compare=trim_title(pack.compare, max_len),
                problem=trim_title(pack.problem, max_len),
            )

            titles = [pack.info, pack.compare, pack.problem]
            if any(not t for t in titles):
                raise ValueError("빈 제목 생성")

            sn = [simple_norm_title(t) for t in titles]
            if len(set(sn)) < 3:
                raise ValueError("3개 타이틀이 과도하게 유사함")

            return pack

        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
                continue
            raise RuntimeError(f"타이틀 생성 실패({max_retries}회 시도): {e}") from e

    raise RuntimeError(f"타이틀 생성 실패: {last_err}")


# =========================
# 메인 처리
# =========================
def process_excel(input_path: str) -> None:
    df = pd.read_excel(input_path, engine="openpyxl")

    # 필수 컬럼 체크
    if COL_PRODUCT_NAME not in df.columns:
        raise SystemExit(f"필수 컬럼이 없습니다: {COL_PRODUCT_NAME}")

    # blogTitle 컬럼이 없으면 생성
    for c in ["blogTitle1", "blogTitle2", "blogTitle3"]:
        if c not in df.columns:
            df[c] = ""

    cache = load_cache(CACHE_PATH)
    client = OpenAI()
    model = DEFAULT_MODEL

    total = len(df)
    print(f"\n[처리 시작] rows={total}, model={model}")

    for i in range(total):
        row = df.iloc[i]

        name = norm(row.get(COL_PRODUCT_NAME, ""))
        if not name:
            continue

        brand = norm(row.get(COL_BRAND, "")) if COL_BRAND in df.columns else ""
        category = norm(row.get(COL_CATEGORY, "")) if COL_CATEGORY in df.columns else ""
        desc = norm(row.get(COL_DESC, "")) if COL_DESC in df.columns else ""
        features = norm(row.get(COL_FEATURES, "")) if COL_FEATURES in df.columns else ""
        price = norm(row.get(COL_PRICE, "")) if COL_PRICE in df.columns else ""
        discount = norm(row.get(COL_DISCOUNT, "")) if COL_DISCOUNT in df.columns else ""

        if not desc:
            desc = pick_first_nonempty(row, DESC_CANDIDATES)
        if not features:
            features = pick_first_nonempty(row, FEATURE_CANDIDATES)

        key = sha1_key(name, brand, category, desc, features, price, discount)
        if key in cache:
            pack_dict = cache[key]
            df.at[i, "blogTitle1"] = pack_dict.get("info", "")
            df.at[i, "blogTitle2"] = pack_dict.get("compare", "")
            df.at[i, "blogTitle3"] = pack_dict.get("problem", "")
        else:
            pack = generate_titles_3types(
                client=client,
                model=model,
                product_name=name,
                brand=brand,
                category=category,
                desc=desc,
                features=features,
                price=price,
                discount=discount,
            )
            df.at[i, "blogTitle1"] = pack.info
            df.at[i, "blogTitle2"] = pack.compare
            df.at[i, "blogTitle3"] = pack.problem

            cache_value = {"info": pack.info, "compare": pack.compare, "problem": pack.problem}
            append_cache(CACHE_PATH, key, cache_value)
            cache[key] = cache_value

            time.sleep(ROW_SLEEP_SEC)

        if (i + 1) % 10 == 0 or i == total - 1:
            print(f"  - 진행: {i+1}/{total}")

    # 3개 엑셀로 분리 저장 (당신이 기존에 원했던 이동/삭제 방식)
    suffix = suffix_from_input_filename_exact(input_path)

    out_info = os.path.join(OUT_DIR, f"{OUT_PREFIX_INFO}_{suffix}.xlsx")
    out_compare = os.path.join(OUT_DIR, f"{OUT_PREFIX_COMPARE}_{suffix}.xlsx")
    out_problem = os.path.join(OUT_DIR, f"{OUT_PREFIX_PROBLEM}_{suffix}.xlsx")

    def make_variant(title_col: str) -> pd.DataFrame:
        d = df.copy()
        d[COL_PRODUCT_NAME] = d[title_col].astype(str)
        # blogTitle들은 이동했으니 제거(원하셨던 조건)
        for c in ["blogTitle1", "blogTitle2", "blogTitle3"]:
            if c in d.columns:
                d.drop(columns=[c], inplace=True)
        return d

    df_info = make_variant("blogTitle1")
    df_compare = make_variant("blogTitle2")
    df_problem = make_variant("blogTitle3")

    df_info.to_excel(out_info, index=False, engine="openpyxl")
    df_compare.to_excel(out_compare, index=False, engine="openpyxl")
    df_problem.to_excel(out_problem, index=False, engine="openpyxl")

    print("\n[완료] 분리 저장됨:")
    print(f" - {out_info}")
    print(f" - {out_compare}")
    print(f" - {out_problem}")


def main():
    load_dotenv()
    ensure_dirs()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("환경변수 OPENAI_API_KEY가 필요합니다.")

    files = list_xlsx_files()
    if not files:
        raise SystemExit(f"'{XLSX_DIR}' 폴더에 .xlsx 파일이 없습니다.")

    input_path = choose_file_interactive(files)
    process_excel(input_path)


if __name__ == "__main__":
    main()
