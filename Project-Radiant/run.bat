@echo off
chcp 65001 >nul
title Radiant 项目启动
echo ========================================
echo    Radiant 学术研究协作平台
echo ========================================
echo.
echo 正在启动开发服务器...
echo.
cd /d "%~dp0Radiant-main" 
if not exist "node_modules" ( 
    echo 检测到未安装依赖，正在安装...
    echo.
    call npm i
    echo.
    echo 依赖安装完成！
    echo.
)

echo 启动开发服务器...
echo 浏览器将自动打开 http://localhost:5173 
echo 按 Ctrl+C 可停止服务
echo.
echo ======================================== 
echo.

start http://localhost:5173
call npm run dev

pause