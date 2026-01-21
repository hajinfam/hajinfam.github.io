@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

REM ==================================================
REM run_allin_pipeline.bat
REM - products.xlsx 하나로:
REM   1) 백업
REM   2) 인스타 HTML 갱신 (insta/index.html)
REM   3) 제품 페이지 생성 (site_products 등)
REM   4) git add/commit/push
REM ==================================================

REM --------------------------------------------------
REM 0) 작업 폴더(배치파일 위치)
REM --------------------------------------------------
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

REM --------------------------------------------------
REM 1) 필수 파일/도구 확인
REM --------------------------------------------------
if not exist "products.xlsx" (
    echo [ERROR] products.xlsx 를 찾을 수 없습니다: %ROOT_DIR%products.xlsx
    pause
    exit /b 1
)

where python > nul 2>&1
if errorlevel 1 (
    echo [ERROR] python 실행기를 찾을 수 없습니다.
    pause
    exit /b 1
)

where git > nul 2>&1
if errorlevel 1 (
    echo [ERROR] git 실행기를 찾을 수 없습니다.
    pause
    exit /b 1
)

REM --------------------------------------------------
REM 2) 백업 폴더 생성 + products.xlsx 백업
REM --------------------------------------------------
if not exist "_backup" mkdir "_backup"

for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%t"
copy /y "products.xlsx" "_backup\products_%TS%.xlsx" > nul
if errorlevel 1 (
    echo [ERROR] products.xlsx 백업 실패
    pause
    exit /b 1
)
echo [OK] Backup: _backup\products_%TS%.xlsx

REM --------------------------------------------------
REM 3) 인스타 HTML 갱신
REM    - update_insta_products.py 가 products.xlsx -> insta/index.html 반영
REM --------------------------------------------------
if not exist "update_insta_products.py" (
    echo [ERROR] update_insta_products.py 를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo.
echo [STEP] Update Insta HTML
python update_insta_products.py
if errorlevel 1 (
    echo [ERROR] update_insta_products.py 실행 실패
    pause
    exit /b 1
)

if not exist "insta\index.html" (
    echo [ERROR] insta\index.html 생성/갱신 결과가 없습니다.
    pause
    exit /b 1
)
echo [OK] Updated: insta\index.html

REM --------------------------------------------------
REM 4) 제품 페이지 생성
REM    - generate_product_pages.py 가 products.xlsx -> site_products(또는 _products) 생성
REM --------------------------------------------------
if not exist "generate_product_pages.py" (
    echo [ERROR] generate_product_pages.py 를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo.
echo [STEP] Generate Product Pages
python generate_product_pages.py
if errorlevel 1 (
    echo [ERROR] generate_product_pages.py 실행 실패
    pause
    exit /b 1
)

REM (선택) 산출물 폴더 존재 확인 - 프로젝트에 맞게 유지/삭제
if not exist "site_products" (
    echo [WARN] site_products 폴더가 없습니다. (프로젝트 구조가 다르면 무시해도 됩니다)
) else (
    echo [OK] Generated: site_products
)

REM --------------------------------------------------
REM 5) Git 커밋/푸시
REM --------------------------------------------------
echo.
echo [STEP] Git add/commit/push

git status --porcelain > _backup\git_status_%TS%.txt

REM 변경 없으면 종료
for /f %%a in ('git status --porcelain ^| find /c /v ""') do set "CHANGES=%%a"
if "%CHANGES%"=="0" (
    echo [INFO] 변경 사항이 없습니다. 커밋/푸시 생략.
    pause
    exit /b 0
)

git add -A
if errorlevel 1 (
    echo [ERROR] git add 실패
    pause
    exit /b 1
)

set "COMMIT_MSG=allin: products.xlsx -> insta + product pages (%TS%)"
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo [ERROR] git commit 실패
    pause
    exit /b 1
)

git push
if errorlevel 1 (
    echo [ERROR] git push 실패
    pause
    exit /b 1
)

echo.
echo ================================================
echo  ALL-IN PIPELINE COMPLETED SUCCESSFULLY
echo ================================================
pause
endlocal
