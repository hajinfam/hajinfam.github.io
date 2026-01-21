import os
import sys
import shutil
import subprocess
import datetime as dt
from typing import Dict, List, Optional

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv


# =========================================================
# 공통 설정
# =========================================================
load_dotenv()

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

EXCEL_PATH = os.path.join(REPO_ROOT, "products.xlsx")
BACKUP_DIR = os.path.join(REPO_ROOT, "_backup")

# 생성물 경로(커밋 대상)
GEN_HTML_PATH = os.path.join(REPO_ROOT, "insta", "index.html")
GEN_MD_DIR = os.path.join(REPO_ROOT, "site_products")

# 실행할 스크립트
SCRIPT_UPDATE_INSTA = os.path.join(REPO_ROOT, "update_insta_products.py")
SCRIPT_GENERATE_PAGES = os.path.join(REPO_ROOT, "generate_product_pages.py")

# --- Google Sheets 설정(선택) ---
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "insta").strip()
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "google-service-account.json").strip()

# 동기화 옵션
# 1이면 GoogleSheet -> Excel (MERGE) 수행, 0이면 건너뜀
SYNC_SHEET_TO_EXCEL = os.getenv("SYNC_SHEET_TO_EXCEL", "0").strip() == "1"

# products.xlsx 기준 컬럼
COL_NO = "no"
COL_NAME = "productName"
COL_URL = "productUrl"
COL_IMG = "mainImage"
COL_SHORT = "shortTitle"
COL_DESC = "productDescription"

# SEO 컬럼(엑셀 값을 보존)
SEO_COLS = ["seoTitle", "seoDescription", "keywords", "category"]

# 구글시트에서 가져올 컬럼(엑셀에 반영할 “기본상품정보”)
BASE_COLS = [COL_NO, COL_NAME, COL_URL, COL_IMG, COL_SHORT, COL_DESC]


# =========================================================
# 유틸
# =========================================================
def to_str(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()


def to_int_safe(x) -> Optional[int]:
    try:
        s = str(x).strip()
        if s == "":
            return None
        return int(float(s))  # "1.0" 같은 케이스 대응
    except Exception:
        return None


def ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def backup_excel() -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(EXCEL_PATH):
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"products_{ts}.xlsx")
        shutil.copy2(EXCEL_PATH, backup_path)
        print(f"[BACKUP] {backup_path} 로 products.xlsx 백업 완료")
    else:
        print("[BACKUP] products.xlsx 가 없어 백업을 건너뜁니다.")


def run_script(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"스크립트를 찾을 수 없습니다: {path}")

    # -u: 버퍼링 제거 (진행 로그가 즉시 보임)
    r = subprocess.run([sys.executable, "-u", path], cwd=REPO_ROOT, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{os.path.basename(path)} 실패 (code={r.returncode})")


# =========================================================
# 1) Google Sheet -> Excel (MERGE, SEO 보존)
# =========================================================
def connect_gsheets():
    key_path = os.path.join(REPO_ROOT, GOOGLE_SERVICE_ACCOUNT_FILE)
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"서비스계정 키 파일이 없습니다: {key_path}")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    ws = sh.worksheet(GOOGLE_SHEET_NAME)
    return ws


def read_google_sheet_df() -> pd.DataFrame:
    ws = connect_gsheets()
    data = ws.get_all_values()
    if not data or len(data) < 2:
        raise RuntimeError("Google Sheet 에 데이터(헤더 포함)가 없습니다.")

    header = [to_str(x) for x in data[0]]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=header)

    # 필요한 기본 컬럼이 없으면 생성(빈값)
    for c in BASE_COLS:
        if c not in df.columns:
            df[c] = ""

    # no 정리
    df[COL_NO] = df[COL_NO].apply(to_int_safe)

    # no 없는 행 제거(안전)
    df = df[df[COL_NO].notnull()].copy()
    df[COL_NO] = df[COL_NO].astype(int)

    # 문자열 정리
    for c in BASE_COLS:
        if c != COL_NO:
            df[c] = df[c].apply(to_str)

    # 같은 no 중복은 마지막 행 우선
    df = df.sort_values(COL_NO).drop_duplicates(subset=[COL_NO], keep="last")

    return df


def read_excel_df() -> pd.DataFrame:
    if not os.path.exists(EXCEL_PATH):
        # 처음이면 빈 엑셀 생성
        df = pd.DataFrame(columns=BASE_COLS + SEO_COLS)
        df.to_excel(EXCEL_PATH, index=False)
        return df

    df = pd.read_excel(EXCEL_PATH)
    df = df.fillna("")
    df.columns = [to_str(c) for c in df.columns]

    # 필요한 컬럼이 없으면 생성
    for c in BASE_COLS + SEO_COLS:
        if c not in df.columns:
            df[c] = ""

    # no 정리
    df[COL_NO] = df[COL_NO].apply(to_int_safe)
    df = df[df[COL_NO].notnull()].copy()
    df[COL_NO] = df[COL_NO].astype(int)

    # 문자열 정리
    for c in BASE_COLS + SEO_COLS:
        if c != COL_NO:
            df[c] = df[c].apply(to_str)

    # 중복 no 제거(마지막 우선)
    df = df.sort_values(COL_NO).drop_duplicates(subset=[COL_NO], keep="last")
    return df


def merge_google_sheet_into_excel(preserve_seo: bool = True) -> None:
    """
    GoogleSheet의 기본 상품정보(BASE_COLS)만 Excel에 반영
    - preserve_seo=True: Excel의 SEO 컬럼은 절대 덮어쓰지 않음(유지)
    """
    if not GOOGLE_SHEET_ID:
        print("[STEP 1] GOOGLE_SHEET_ID 가 없어 GoogleSheet 동기화를 건너뜁니다.")
        return

    print("===================================================")
    print("[STEP 1] Google Sheet → products.xlsx MERGE (SEO 보존)")
    print("===================================================")

    gs_df = read_google_sheet_df()
    xl_df = read_excel_df()

    gs_map = {int(row[COL_NO]): row for _, row in gs_df.iterrows()}
    xl_map = {int(row[COL_NO]): row for _, row in xl_df.iterrows()}

    all_nos = sorted(set(gs_map.keys()) | set(xl_map.keys()))
    out_rows: List[Dict] = []

    updated = 0
    created = 0

    for no in all_nos:
        base = {}
        if no in xl_map:
            # 기존 엑셀 row 기반
            base = xl_map[no].to_dict()
        else:
            # 신규 생성
            base = {c: "" for c in (BASE_COLS + SEO_COLS)}
            base[COL_NO] = no

        if no in gs_map:
            # 구글시트의 기본정보를 엑셀에 반영(빈칸도 반영 여부는 정책 선택)
            gs_row = gs_map[no].to_dict()

            # 여기서는 "구글시트 값이 비어있지 않을 때만" 엑셀에 반영(안전)
            for c in BASE_COLS:
                if c == COL_NO:
                    continue
                v = to_str(gs_row.get(c, ""))
                if v:
                    if to_str(base.get(c, "")) != v:
                        base[c] = v

            if no in xl_map:
                updated += 1
            else:
                created += 1

        # SEO 보존: 아무것도 안함(엑셀 값 유지)
        # preserve_seo=False로 바꾸면, 원한다면 여기서 gs에서 SEO도 병합 가능

        out_rows.append(base)

    out_df = pd.DataFrame(out_rows)
    out_df = out_df.fillna("")
    out_df = out_df.sort_values(COL_NO)

    # 컬럼 순서 정리
    ordered_cols = BASE_COLS + SEO_COLS + [c for c in out_df.columns if c not in (BASE_COLS + SEO_COLS)]
    out_df = out_df[ordered_cols]

    out_df.to_excel(EXCEL_PATH, index=False)
    print(f"[STEP 1] MERGE 완료 → {EXCEL_PATH} (updated={updated}, created={created}, rows={len(out_df)})")


# =========================================================
# 2) update_insta_products.py & generate_product_pages.py 실행
# =========================================================
def run_generation():
    print("===================================================")
    print("[STEP 2] insta/index.html & site_products MD 생성")
    print("===================================================")

    print("[2-1] update_insta_products.py 실행...")
    run_script(SCRIPT_UPDATE_INSTA)

    print("[2-2] generate_product_pages.py 실행...")
    run_script(SCRIPT_GENERATE_PAGES)

    print("[STEP 2] 생성 완료")


# =========================================================
# 3) Git add / commit / push
# =========================================================
def git_has_changes() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def git_add_commit_push():
    print("===================================================")
    print("[STEP 3] git add / commit / push")
    print("===================================================")

    if not git_has_changes():
        print("[GIT] 커밋할 변경 사항이 없습니다.")
        return

    # 생성물만 stage (스크립트는 제외)
    add_targets = []
    if os.path.exists(EXCEL_PATH):
        add_targets.append("products.xlsx")
    if os.path.exists(GEN_HTML_PATH):
        add_targets.append("insta/index.html")
    if os.path.exists(GEN_MD_DIR):
        add_targets.append("site_products")

    if not add_targets:
        print("[GIT] stage할 대상 파일/폴더가 없습니다.")
        return

    subprocess.run(["git", "add", *add_targets], cwd=REPO_ROOT, check=True)
    print(f"[GIT] git add 완료: {add_targets}")

    commit_msg = f"All-in-one: update products & pages ({dt.datetime.now().strftime('%Y-%m-%d %H:%M')})"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True)
    print("[GIT] commit 생성 완료")

    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, check=True)
    print("[GIT] push origin main 완료")


# =========================================================
# main
# =========================================================
def main():
    print("=== ALL-IN-ONE 파이프라인 시작 (SEO 보존) ===")

    # 0) 엑셀 백업
    backup_excel()

    # 1) (선택) 구글시트 -> 엑셀 MERGE (SEO 보존)
    if SYNC_SHEET_TO_EXCEL:
        merge_google_sheet_into_excel(preserve_seo=True)
    else:
        print("[STEP 1] SYNC_SHEET_TO_EXCEL=0 → GoogleSheet→Excel 단계 건너뜀 (Excel을 SSOT로 유지)")

    # 2) 생성(인스타 랜딩 + MD + (generate_product_pages.py 내부에서 SEO 채움/구글시트 동기화까지 수행 가능))
    run_generation()

    # 3) git add/commit/push
    git_add_commit_push()

    print("=== ALL-IN-ONE 파이프라인 완료 ===")


if __name__ == "__main__":
    main()
