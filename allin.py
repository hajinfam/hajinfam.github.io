import os
import sys
import shutil
import subprocess
import datetime as dt

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
HTML_PATH = os.path.join(REPO_ROOT, "insta", "index.html")
BACKUP_DIR = os.path.join(REPO_ROOT, "_backup")

# --- Google Sheets 설정 ---
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "insta")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "google-service-account.json"
)

# products.xlsx 에 맞춘 컬럼
COL_NO = "no"
COL_NAME = "productName"
COL_URL = "productUrl"
COL_IMG = "mainImage"
COL_SHORT = "shortTitle"
COL_DESC = "productDescription"


# =========================================================
# 1. Google Sheet → products.xlsx 동기화
# =========================================================
def sync_google_sheet_to_excel():
    if not GOOGLE_SHEET_ID:
        print("[STEP 1] GOOGLE_SHEET_ID 가 .env 에 없습니다. 이 단계는 건너뜁니다.")
        return

    print("===================================================")
    print("[STEP 1] Google Sheet → products.xlsx 동기화 시작")
    print("===================================================")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    creds = Credentials.from_service_account_file(
        os.path.join(REPO_ROOT, GOOGLE_SERVICE_ACCOUNT_FILE),
        scopes=scopes,
    )
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    ws = sh.worksheet(GOOGLE_SHEET_NAME)

    data = ws.get_all_values()
    if not data:
        raise RuntimeError("Google Sheet 에 데이터가 없습니다.")

    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)

    # 컬럼 이름 표준화 (없으면 생성)
    for col in [COL_NO, COL_NAME, COL_URL, COL_IMG, COL_SHORT, COL_DESC]:
        if col not in df.columns:
            df[col] = ""

    # 숫자 no 컬럼 정리
    def to_int_safe(x):
        try:
            return int(str(x).strip())
        except Exception:
            return None

    df[COL_NO] = df[COL_NO].apply(to_int_safe)

    # 번호 비어있으면 1부터 순서대로
    if df[COL_NO].isnull().any():
        df[COL_NO] = list(range(1, len(df) + 1))

    df.to_excel(EXCEL_PATH, index=False)
    print(f"[STEP 1] 동기화 완료 → {EXCEL_PATH}")


# =========================================================
# 2. update_insta_products.py & generate_product_pages.py 실행
# =========================================================
def run_update_insta_products():
    print("===================================================")
    print("[STEP 2] insta/index.html & site_products MD 생성")
    print("===================================================")

    # 2-1) update_insta_products.py 실행
    print("[2-1] update_insta_products.py 실행 중...")
    r1 = subprocess.run(
        [sys.executable, "update_insta_products.py"],
        cwd=REPO_ROOT,
        text=True,
    )
    if r1.returncode != 0:
        raise RuntimeError(f"update_insta_products.py 실패 (code={r1.returncode})")

    # 2-2) generate_product_pages.py 실행
    print("[2-2] generate_product_pages.py 실행 중...")
    r2 = subprocess.run(
        [sys.executable, "generate_product_pages.py"],
        cwd=REPO_ROOT,
        text=True,
    )
    if r2.returncode != 0:
        raise RuntimeError(f"generate_product_pages.py 실패 (code={r2.returncode})")

    print("[STEP 2] index.html / MD 페이지 생성 완료")


# =========================================================
# 3. Git add / commit / push
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

    # 엑셀, 랜딩, MD를 모두 stage
    add_cmd = [
        "git",
        "add",
        "products.xlsx",
        "insta/index.html",
        "update_insta_products.py",
        "generate_product_pages.py",
        "site_products",
    ]
    subprocess.run(add_cmd, cwd=REPO_ROOT, check=True)
    print("[GIT] git add 완료")

    commit_msg = "All-in-one: update products & pages"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=REPO_ROOT,
        check=True,
    )
    print("[GIT] commit 생성 완료")

    try:
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=REPO_ROOT,
            check=True,
        )
        print("[GIT] push origin main 완료")
    except subprocess.CalledProcessError as e:
        print("[GIT] push 실패:", e)


# =========================================================
# main
# =========================================================
def main():
    print("=== ALL-IN-ONE 파이프라인 시작 (GitHub까지) ===")

    # 0. 엑셀 백업
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(EXCEL_PATH):
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"products_{ts}.xlsx")
        shutil.copy2(EXCEL_PATH, backup_path)
        print(f"[BACKUP] {backup_path} 로 products.xlsx 백업 완료")

    # 1. 구글 시트 → 엑셀
    sync_google_sheet_to_excel()

    # 2. insta/index.html & MD 갱신
    run_update_insta_products()

    # 3. git add / commit / push
    git_add_commit_push()

    print("=== ALL-IN-ONE 파이프라인 완료 (GitHub 반영까지) ===")


if __name__ == "__main__":
    main()