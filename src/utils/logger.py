#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器
使用loguru提供日志记录功能
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logger:
    """
    设置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，默认为项目根目录下的logs/app.log
    
    Returns:
        配置好的logger实例
    """
    # 移除默认的handler
    logger.remove()
    
    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    # 添加控制台handler
    logger.add(
        sys.stderr,
        format=console_format,
        level=log_level,
        colorize=True
    )
    
    # 设置日志文件路径
    if log_file is None:
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "app.log"
    
    # 添加文件handler
    logger.add(
        log_file,
        format=file_format,
        level=log_level,
        rotation="10 MB",  # 日志文件大小轮转
        retention="7 days",  # 保留7天的日志
        compression="zip",  # 压缩旧日志
        encoding="utf-8"
    )
    
    # 添加错误日志文件
    error_log_file = Path(log_file).parent / "error.log"
    logger.add(
        error_log_file,
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")
    return logger


class LoggerMixin:
    """日志混入类，为其他类提供日志功能"""
    
    @property
    def logger(self):
        """获取logger实例"""
        return logger.bind(name=self.__class__.__name__)
    
    def log_method_call(self, method_name: str, **kwargs):
        """记录方法调用"""
        args_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.debug(f"调用方法 {method_name}({args_str})")
    
    def log_error(self, error: Exception, context: str = ""):
        """记录错误信息"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg)
        self.logger.exception("详细错误堆栈:")


# 创建全局logger实例
app_logger = setup_logger()