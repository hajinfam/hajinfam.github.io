import os
import sys
import json
import time
import shutil
import subprocess
import datetime as dt

import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from openai import OpenAI

# =========================================================
# 공통 설정
# =========================================================
load_dotenv()

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(REPO_ROOT, "products.xlsx")
HTML_PATH = os.path.join(REPO_ROOT, "insta", "index.html")
BACKUP_DIR = os.path.join(REPO_ROOT, "_backup")
LAST_INDEX_FILE = os.path.join(REPO_ROOT, "last_post_index.txt")

# --- Google Sheets 설정 ---
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "insta")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "google-service-account.json")

# --- OpenAI / Instagram 설정 ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
GRAPH_API_VERSION = "v21.0"

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY 가 설정되어 있지 않습니다. .env 를 확인하세요.")

client = OpenAI(api_key=OPENAI_API_KEY)

# products.xlsx 에 맞춘 컬럼
COL_NO = "no"
COL_NAME = "productName"
COL_URL = "productUrl"
COL_IMG = "mainImage"
COL_SHORT = "shortTitle"
COL_DESC = "productDescription"

# =========================================================
# 0. 유틸 함수: last_post_index
# =========================================================
def load_last_index() -> int:
    if not os.path.exists(LAST_INDEX_FILE):
        return -1
    with open(LAST_INDEX_FILE, "r", encoding="utf-8") as f:
        txt = f.read().strip()
        return int(txt) if txt else -1


def save_last_index(idx: int) -> None:
    with open(LAST_INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(str(idx))


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
# 4. GPT 캡션 + 인스타그램 업로드 (1개만)
# =========================================================
def generate_instagram_caption(name: str, desc: str, url: str) -> tuple[str, str, str]:
    """
    인스타용 본문 + 해시태그 + 짧은 상품명 생성
    """
    system_msg = (
        "너는 한국의 마케팅 카피라이터야. "
        "인스타그램 피드용 홍보글을 20~40대 여성이 좋아할 감성으로 작성해. "
        "톤은 친근하지만 과도한 광고 느낌은 피하고, 자연스럽게 설득력 있게 써. "
        "본문은 400자 이내, 이모지는 문장마다 0~2개 정도 사용. "
        "마지막에는 부드러운 구매 유도 문장과 10개 이하의 해시태그를 넣어. "
        "또한 짧은 상품명(short_title)은 12자 이내, 핵심 키워드만 남겨. "
        "출력은 JSON 형식으로만:\n"
        "{\n"
        '  "caption": "인스타그램 본문",\n'
        '  "hashtags": "#태그1 #태그2",\n'
        '  "short_title": "짧은 상품명"\n'
        "}"
    )

    user_msg = (
        f"상품명: {name}\n"
        f"설명: {desc}\n"
        f"링크: {url}\n\n"
        "위 정보를 기반으로 위 JSON 형식만 출력해줘."
    )

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=500,
    )

    content = resp.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.strip("`")
        lines = content.splitlines()
        if lines and lines[0].strip().lower() in ("json", "javascript"):
            content = "\n".join(lines[1:])

    data = json.loads(content)

    caption = data.get("caption", "").strip()
    hashtags = data.get("hashtags", "").strip()
    short_title = data.get("short_title", "").strip() or name.strip()

    return caption, hashtags, short_title


def post_to_instagram(image_url: str, caption: str) -> dict:
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        raise RuntimeError("IG_USER_ID / IG_ACCESS_TOKEN 이 설정되지 않았습니다.")

    media_api = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    res = requests.post(media_api, data=payload)
    data = res.json()

    if "id" not in data:
        raise RuntimeError(f"이미지 업로드 실패: {data}")

    creation_id = data["id"]

    publish_api = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    }
    res = requests.post(publish_api, data=payload)
    data = res.json()

    if "id" not in data:
        raise RuntimeError(f"게시 실패: {data}")

    return data


def post_all_remaining_products():
    """
    last_post_index.txt 이후의 '남은 모든 상품'을
    순서대로 인스타그램에 올린 뒤 종료.
    """
    print("===================================================")
    print("[STEP 4] 인스타그램 남은 모든 상품 업로드")
    print("===================================================")

    if not os.path.exists(EXCEL_PATH):
        print(f"[STEP 4] {EXCEL_PATH} 를 찾을 수 없어 인스타 업로드를 건너뜁니다.")
        return

    df = pd.read_excel(EXCEL_PATH)
    if df.empty:
        print("[STEP 4] 엑셀에 데이터가 없어 업로드를 건너뜁니다.")
        return

    last_idx = load_last_index()
    start_idx = last_idx + 1

    if start_idx >= len(df):
        print("[STEP 4] 이미 모든 상품을 업로드했습니다. 새로 올릴 상품이 없습니다.")
        return

    total = len(df) - start_idx
    print(f"[INFO] 이번 실행에서 업로드할 상품 개수: {total}개 (index {start_idx} ~ {len(df)-1})")

    for idx in range(start_idx, len(df)):
        row = df.iloc[idx]

        name = str(row.get(COL_NAME, "")).strip()
        desc = str(row.get(COL_DESC, "")).strip()
        url = str(row.get(COL_URL, "")).strip()
        image_url = str(row.get(COL_IMG, "")).strip()

        if not image_url.startswith("http"):
            print(f"[WARN] index={idx}: 이미지 URL 이 잘못되어 건너뜁니다. ({image_url!r})")
            save_last_index(idx)  # 그래도 인덱스는 앞으로 진행
            continue

        product_no = row.get(COL_NO, idx + 1)
        print(f"\n[INFO] 업로드 대상 index={idx}, 상품번호={product_no}, 이름='{name}'")

        # 1) 캡션 생성
        try:
            caption, hashtags, short_title = generate_instagram_caption(name, desc, url)
        except Exception as e:
            print("[ERROR] 캡션 생성 실패, 이 상품은 건너뜁니다:", e)
            save_last_index(idx)
            continue

        label = f"{product_no}번. {short_title}"
        full_caption = caption
        full_caption += f"\n\n{label}\n프로필 링크에서 '{product_no}번'을 찾아주세요!"
        if hashtags:
            full_caption += f"\n\n{hashtags}"

        print("[PREVIEW] 캡션 일부:", full_caption[:120].replace("\n", " "), "...")

        # 2) 인스타 업로드
        try:
            res = post_to_instagram(image_url, full_caption)
            print("[SUCCESS] 인스타그램 업로드 완료:", res)
            save_last_index(idx)
        except Exception as e:
            print("[ERROR] 인스타 업로드 실패, 이 상품은 건너뜁니다:", e)
            save_last_index(idx)
            continue

        # 안전하게 약간의 딜레이 (API 연속 호출 완화용)
        time.sleep(5)

    print("\n[STEP 4] 모든 남은 상품 업로드 시도 완료.")

# =========================================================
# main
# =========================================================
def main():
    print("=== ALL-IN-ONE 파이프라인 시작 ===")

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

    # 4. 인스타그램 다음 상품 1개 업로드
    post_all_remaining_products()

    print("=== ALL-IN-ONE 파이프라인 완료 ===")


if __name__ == "__main__":
    main()