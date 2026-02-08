@echo off
chcp 65001 >nul
title 国庆餐馆管理系统
echo.
echo  ╔═══════════════════════════════════╗
echo  ║     🏮 国庆餐馆管理系统 🏮        ║
echo  ╚═══════════════════════════════════╝
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到Python，请先安装Python 3.8+
    pause
    exit
)

REM 安装依赖
echo 📦 正在检查依赖...
pip install -r requirements.txt -q

REM 初始化数据库（如果不存在）
if not exist "instance\guoqing.db" (
    echo 🗄️  首次运行，正在初始化数据库...
    python init_db.py
)

echo.
echo ✅ 系统启动中...
echo    顾客扫码点餐: http://localhost:5000/?table=1
echo    管理后台:      http://localhost:5000/admin
echo    密码: guoqing888
echo.
echo    按 Ctrl+C 停止服务
echo.

REM 延迟打开浏览器
start "" http://localhost:5000/admin

REM 启动Flask
python run.py
pause
