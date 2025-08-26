#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用打包脚本
使用PyInstaller将应用程序打包为Windows可执行文件
"""

import os
import sys
import shutil
from pathlib import Path

def create_spec_file():
    """创建PyInstaller规格文件"""
    
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.ini', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'qfluentwidgets',
        'loguru',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='轻量笔记管理器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app_icon.ico',  # 应用图标
    version_file='version_info.txt',      # 版本信息文件
)
'''
    
    with open('noteBoard.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content.strip())
    
    print("✓ PyInstaller规格文件创建完成: noteBoard.spec")

def create_version_info():
    """创建版本信息文件"""
    
    version_info = '''
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Kiro Studio'),
        StringStruct(u'FileDescription', u'轻量级Windows桌面笔记管理软件'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'noteBoard'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2025 Kiro'),
        StringStruct(u'OriginalFilename', u'轻量笔记管理器.exe'),
        StringStruct(u'ProductName', u'轻量笔记管理器'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info.strip())
    
    print("✓ 版本信息文件创建完成: version_info.txt")

def create_build_script():
    """创建构建脚本"""
    
    build_script = '''@echo off
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
    echo 可执行文件位置: dist\\轻量笔记管理器.exe
    echo.
    pause
) else (
    echo.
    echo 打包失败！
    echo 请检查错误信息并重试。
    echo.
    pause
)
'''
    
    with open('build.bat', 'w', encoding='utf-8') as f:
        f.write(build_script.strip())
    
    print("✓ 构建脚本创建完成: build.bat")

def create_resources_dir():
    """创建资源目录"""
    resources_dir = Path('resources')
    icons_dir = resources_dir / 'icons'
    
    resources_dir.mkdir(exist_ok=True)
    icons_dir.mkdir(exist_ok=True)
    
    # 创建图标占位文件说明
    icon_readme = '''
# 图标文件说明

请将以下图标文件放置在此目录中：

- app_icon.ico: 应用程序主图标 (32x32, 48x48, 256x256)
- tray_icon.ico: 系统托盘图标 (16x16, 32x32)

图标格式要求：
- 文件格式: ICO
- 颜色深度: 32位 RGBA
- 建议尺寸: 多个尺寸集合

如果没有提供图标文件，应用程序将使用默认图标。
'''
    
    with open(icons_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(icon_readme.strip())
    
    print(f"✓ 资源目录创建完成: {resources_dir}")

def main():
    """主函数"""
    print("=" * 50)
    print("轻量级Windows桌面笔记管理软件 - 打包工具")
    print("=" * 50)
    
    try:
        # 检查是否在正确的目录
        if not Path('main.py').exists():
            print("✗ 错误: 请在项目根目录运行此脚本")
            return False
        
        # 创建打包所需的文件
        create_resources_dir()
        create_version_info()
        create_spec_file()
        create_build_script()
        
        print("\n" + "=" * 30)
        print("打包准备完成！")
        print("=" * 30)
        
        print("\n下一步操作：")
        print("1. (可选) 将应用图标放置到 resources/icons/ 目录")
        print("2. 运行 build.bat 开始打包")
        print("3. 打包完成后，可执行文件将在 dist/ 目录中")
        
        print(f"\n或者直接运行以下命令打包：")
        print("pyinstaller noteBoard.spec")
        
        return True
        
    except Exception as e:
        print(f"✗ 创建打包文件失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)