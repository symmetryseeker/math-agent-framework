@echo off
chcp 65001 >nul
title Math Agent Framework

echo.
echo ============================================================
echo   Math Agent Framework v1.0
echo   可复用数学推导与验证框架
echo ============================================================
echo.
echo   [1] 列出所有模型
echo   [2] 运行模型推导 (network_embedded_growth)
echo   [3] 运行模型推导 (quadratic_form)
echo   [4] 运行验证
echo   [5] 生成文档 (Markdown)
echo   [6] 生成文档 (Word .docx)
echo   [7] 生成形式化证明
echo   [8] 交互式模式
echo   [9] 启动 MCP 服务器
echo   [0] 退出
echo.

set /p choice="  请选择 [0-9]: "

cd /d "D:\tools\math-agent-framework"

if "%choice%"=="1" (
    python cli\cli.py list
    pause
    goto end
)
if "%choice%"=="2" (
    python cli\cli.py derive network_embedded_growth --output ./output
    pause
    goto end
)
if "%choice%"=="3" (
    python cli\cli.py derive quadratic_form --output ./output
    pause
    goto end
)
if "%choice%"=="4" (
    python cli\cli.py verify network_embedded_growth
    pause
    goto end
)
if "%choice%"=="5" (
    python cli\cli.py doc network_embedded_growth --format md --output ./output
    pause
    goto end
)
if "%choice%"=="6" (
    python cli\cli.py doc network_embedded_growth --format docx --output ./output
    pause
    goto end
)
if "%choice%"=="7" (
    python cli\cli.py proof quadratic_minimum
    pause
    goto end
)
if "%choice%"=="8" (
    python cli\cli.py interactive
    goto end
)
if "%choice%"=="9" (
    echo   Starting MCP Server...
    python mcp\mcp_server.py
    goto end
)
if "%choice%"=="0" goto end

echo   无效选择
pause
:end
