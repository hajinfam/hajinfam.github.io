import os
import sys
import shutil
import subprocess
import datetime as dt

# ========================
# 기본 경로 설정
# ========================
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(REPO_ROOT, "products.xlsx")
HTML_PATH = os.path.join(REPO_ROOT, "insta", "index.html")
BACKUP_DIR = os.path.join(REPO_ROOT, "_backup")
SITE_PRODUCTS_DIR = os.path.join(REPO_ROOT, "site_products")

UPDATE_SCRIPT = "update_insta_products.py"
MD_SCRIPT = "generate_product_pages.py"

# ========================
# 1) 엑셀 백업
# ========================
def backup_excel():
    if not os.path.exists(EXCEL_PATH):
        print(f"[BACKUP] products.xlsx 를 찾을 수 없습니다: {EXCEL_PATH}")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"products_{timestamp}.xlsx"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    shutil.copy2(EXCEL_PATH, backup_path)
    print(f"[BACKUP] {backup_path} 로 엑셀 백업 완료")


# ========================
# 2) insta HTML 갱신
# ========================
def run_update_insta_products():
    """
    update_insta_products.py 실행
    - GPT로 shortTitle / productDescription 채우기
    - insta/index.html 의 products 배열 갱신
    """
    script_path = os.path.join(REPO_ROOT, UPDATE_SCRIPT)
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"{UPDATE_SCRIPT} 파일을 찾을 수 없습니다: {script_path}")

    print(f"[STEP 1] {UPDATE_SCRIPT} 실행 중...")
    result = subprocess.run(
        [sys.executable, "-u", UPDATE_SCRIPT],
        cwd=REPO_ROOT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{UPDATE_SCRIPT} 실행 실패 (exit code {result.returncode})"
        )
    print("[STEP 1] insta/index.html 갱신 완료")


# ========================
# 3) 상품 MD 페이지 생성
# ========================
def run_generate_md_pages():
    """
    generate_product_pages.py 실행
    - site_products/ 아래에 각 상품별 .md 파일 생성
    - site_products/index.md 목차 생성
    """
    script_path = os.path.join(REPO_ROOT, MD_SCRIPT)
    if not os.path.exists(script_path):
        print(f"[STEP 2] {MD_SCRIPT} 를 찾을 수 없습니다. 이 단계는 건너뜁니다.")
        return

    print(f"[STEP 2] {MD_SCRIPT} 실행 중 (상품 MD 페이지 생성)...")
    result = subprocess.run(
        [sys.executable, "-u", UPDATE_SCRIPT],
        cwd=REPO_ROOT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{MD_SCRIPT} 실행 실패 (exit code {result.returncode})"
        )
    print("[STEP 2] site_products/ 내 MD 페이지 생성 완료")


# ========================
# 4) git add / commit / push
# ========================
def git_has_changes() -> bool:
    """git status --porcelain 으로 변경 사항 유무 확인."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    return bool(output)


def git_add_commit_push():
    if not git_has_changes():
        print("[STEP 3] 커밋할 변경 사항이 없습니다. (이미 최신 상태)")
        return

    print("[STEP 3] 변경 파일 stage 중...")

    add_targets = [
        "products.xlsx",
        "insta/index.html",
        UPDATE_SCRIPT,
        MD_SCRIPT,
    ]

    # site_products 디렉터리가 있으면 통째로 추가
    if os.path.isdir(SITE_PRODUCTS_DIR):
        add_targets.append("site_products")

    subprocess.run(
        ["git", "add"] + add_targets,
        cwd=REPO_ROOT,
        check=True,
    )

    print("[STEP 3] commit 생성 중...")
    commit_msg = "Auto update insta landing & product pages"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=REPO_ROOT,
        check=True,
    )

    print("[STEP 3] origin main 으로 push 중...")
    try:
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=REPO_ROOT,
            check=True,
        )
        print("[STEP 3] GIT PUSH 완료: 원격 저장소에 최신 상태가 반영되었습니다.")
    except subprocess.CalledProcessError as e:
        print("[STEP 3] GIT PUSH 실패. 에러 내용을 확인하세요.")
        print("        →", e)


# ========================
# main
# ========================
def main():
    print("====================================================")
    print("=== INSTAGRAM 랜딩 + MD 페이지 자동 배포 시작 ===")
    print("====================================================")

    # 1. 엑셀 백업
    backup_excel()

    # 2. insta 페이지 업데이트
    run_update_insta_products()

    # 3. 상품별 MD 페이지 + 목차 생성
    run_generate_md_pages()

    # 4. git add / commit / push
    git_add_commit_push()

    print("====================================================")
    print("=== 모든 배포 작업 완료 (deploy_insta_site.py) ===")
    print("====================================================")


if __name__ == "__main__":
    main()
