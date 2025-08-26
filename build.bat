@echo off
echo 开始打包轻量笔记管理器...

REM 检查是否安装了PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install PyInstaller
)

REM 清理旧的构建文件
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM 使用规格文件进行打包
echo 正在使用PyInstaller打包应用程序...
pyinstaller noteBoard.spec

if errorlevel 0 (
    echo.
    echo 打包完成！
    echo 可执行文件位置: dist\轻量笔记管理器.exe
    echo.
    pause
) else (
    echo.
    echo 打包失败！
    echo 请检查错误信息并重试。
    echo.
    pause
)