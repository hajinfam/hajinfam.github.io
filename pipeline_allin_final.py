# pipeline_allin_final.py
import os
import sys
import time
import subprocess
from glob import glob

import pandas as pd

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# 1) split 생성(기존 정상 코드)
EXCEL_RE_3TYPE = os.path.join(REPO_ROOT, "excel_re_3type.py")
RE_XLSX_DIR = os.path.join(REPO_ROOT, "re_xlsx")

# 2) 메인 엑셀
PRODUCTS_XLSX = os.path.join(REPO_ROOT, "products.xlsx")

# 3) GPT 채움 + MD 생성
GENERATOR = os.path.join(REPO_ROOT, "generate_product_pages_final.py")

# 4) Git 옵션
DO_GIT_PUSH = False  # 필요하면 True로
GIT_COMMIT_MSG = "fix: allin pipeline + md generator"

# split 컬럼
SRC_NAME = "productName"
SRC_IMAGE = "mainImage"
SRC_LINK = "link"

# products.xlsx 컬럼
DST_NO = "no"
DST_NAME = "productName"
DST_URL = "productUrl"     # 규칙: link 값이 들어감
DST_IMAGE = "mainImage"


def log(msg: str):
    print(msg, flush=True)


def run(cmd, check=True):
    log(f"[RUN] {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=REPO_ROOT)
    if check and p.returncode != 0:
        raise RuntimeError(f"[ERROR] command failed (exit={p.returncode}): {' '.join(cmd)}")
    return p.returncode


def ensure_columns(df: pd.DataFrame, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df


def to_int_safe(x) -> int:
    try:
        return int(str(x).strip())
    except Exception:
        return 0


def pick_latest_products_split() -> str:
    candidates = glob(os.path.join(RE_XLSX_DIR, "products_*.xlsx"))
    if not candidates:
        raise RuntimeError("[ERROR] re_xlsx/products_*.xlsx 파일이 없습니다. excel_re_3type.py 출력 확인 필요.")
    return max(candidates, key=os.path.getmtime)


def append_split_into_products(products_xlsx: str, split_xlsx: str) -> int:
    """
    split(products_*.xlsx)에서 3컬럼만 가져와 products.xlsx에 append + no 부여
    - src: productName/mainImage/link
    - dst: no/productName/mainImage/productUrl(link)
    - no: 기존 max(no)+1부터 연속
    - 중복: productUrl 기준
    """
    if not os.path.exists(products_xlsx):
        raise RuntimeError(f"[ERROR] products.xlsx not found: {products_xlsx}")
    if not os.path.exists(split_xlsx):
        raise RuntimeError(f"[ERROR] split file not found: {split_xlsx}")

    dst = pd.read_excel(products_xlsx)
    src = pd.read_excel(split_xlsx)

    # products.xlsx 컬럼 보장(스크린샷 기준)
    dst = ensure_columns(dst, [
        DST_NO, DST_NAME, DST_URL, DST_IMAGE,
        "shortTitle", "productDescription", "seoTitle", "seoDescription",
        "keywords", "category"
    ])

    for c in [SRC_NAME, SRC_IMAGE, SRC_LINK]:
        if c not in src.columns:
            raise RuntimeError(f"[ERROR] split 파일에 '{c}' 컬럼이 없습니다: {split_xlsx}")

    # max no
    max_no = 0
    if len(dst) > 0:
        max_no = max(to_int_safe(v) for v in dst[DST_NO].tolist())
    next_no = max_no + 1

    # 중복 방지(productUrl)
    existing_urls = set(dst[DST_URL].fillna("").astype(str).str.strip().tolist())

    new_rows = []
    for i in range(len(src)):
        name = "" if pd.isna(src.loc[i, SRC_NAME]) else str(src.loc[i, SRC_NAME]).strip()
        img  = "" if pd.isna(src.loc[i, SRC_IMAGE]) else str(src.loc[i, SRC_IMAGE]).strip()
        link = "" if pd.isna(src.loc[i, SRC_LINK]) else str(src.loc[i, SRC_LINK]).strip()

        if not link:
            continue
        if link in existing_urls:
            continue

        row = {col: "" for col in dst.columns}
        row[DST_NO] = next_no
        row[DST_NAME] = name
        row[DST_IMAGE] = img
        row[DST_URL] = link  # 규칙: link -> productUrl

        new_rows.append(row)
        existing_urls.add(link)
        next_no += 1

    if not new_rows:
        log("[WARN] Append할 신규 행이 없습니다(링크 없음/중복만 존재).")
        return 0

    out = pd.concat([dst, pd.DataFrame(new_rows)], ignore_index=True)
    out.to_excel(products_xlsx, index=False)
    return len(new_rows)


def main():
    log("=" * 70)
    log("ALLIN PIPELINE FINAL START")
    log(time.strftime("%Y-%m-%d %H:%M:%S"))
    log("=" * 70)

    # STEP 1) split 생성
    if not os.path.exists(EXCEL_RE_3TYPE):
        raise RuntimeError("[ERROR] excel_re_3type.py 를 찾지 못했습니다.")
    run([sys.executable, EXCEL_RE_3TYPE], check=True)

    # STEP 2) 최신 products split
    latest_split = pick_latest_products_split()
    log(f"[OK] Latest split: {latest_split}")

    # STEP 3) products.xlsx append + no 부여
    added = append_split_into_products(PRODUCTS_XLSX, latest_split)
    log(f"[OK] Appended rows: {added}")

    # STEP 4) GPT 채움 + MD 생성
    if not os.path.exists(GENERATOR):
        raise RuntimeError("[ERROR] generate_product_pages_final.py 를 찾지 못했습니다.")
    run([sys.executable, GENERATOR], check=True)

    # STEP 5) Git (옵션)
    if DO_GIT_PUSH:
        run(["git", "add", "products.xlsx", "site_products"], check=False)
        run(["git", "commit", "-m", GIT_COMMIT_MSG], check=False)
        run(["git", "push"], check=False)

    log("=" * 70)
    log("ALLIN PIPELINE FINAL DONE")
    log(time.strftime("%Y-%m-%d %H:%M:%S"))
    log("=" * 70)


if __name__ == "__main__":
    main()
