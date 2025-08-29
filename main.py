#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级Windows桌面笔记管理软件
主程序入口

Author: Kiro
Date: 2025-08-26
Version: 1.0.0
"""

import sys
import os
import signal
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir
from qfluentwidgets import setTheme, Theme

from src.controllers.main_controller import MainController
from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_logger


def signal_handler(signum, frame):
    """信号处理函数"""
    print(f"\n接收到信号 {signum}，正在退出...")
    sys.exit(0)


def main():
    """主函数"""
    # 设置高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 创建应用实例
    app = QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出程序，支持托盘模式
    app.setQuitOnLastWindowClosed(True)  # 关闭窗口时退出程序（简化逻辑）
    
    # 初始化日志系统
    logger = setup_logger()
    logger.info("应用程序启动")
    
    # 加载配置
    config = ConfigManager()
    
    # 设置主题
    theme_name = config.get('ui', 'theme', fallback='auto')
    if theme_name.lower() == 'dark':
        setTheme(Theme.DARK)
    elif theme_name.lower() == 'light':
        setTheme(Theme.LIGHT)
    else:
        setTheme(Theme.AUTO)
    
    # 创建主控制器
    main_controller = MainController(app, config, logger)
    
    try:
        # 初始化应用
        main_controller.init_application()
        
        # 显示主窗口
        main_controller.show_main_window()
        
        # 运行应用
        exit_code = app.exec()
        
        logger.info(f"应用程序退出，退出代码: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"应用程序运行出错: {e}")
        return 1
    
    finally:
        # 清理资源
        try:
            if 'main_controller' in locals() and main_controller:
                main_controller.cleanup()
        except Exception as e:
            print(f"清理资源失败: {e}")


if __name__ == "__main__":
    sys.exit(main())