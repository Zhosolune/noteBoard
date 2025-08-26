#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
负责加载和管理应用程序配置
"""

import configparser
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为项目根目录下的config.ini
        """
        self.config = configparser.ConfigParser()
        
        if config_file is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / "config.ini"
        
        self.config_file = Path(config_file)
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        if self.config_file.exists():
            self.config.read(self.config_file, encoding='utf-8')
        else:
            # 如果配置文件不存在，使用默认配置
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置"""
        # App配置
        self.config.add_section('app')
        self.config.set('app', 'name', '轻量笔记管理器')
        self.config.set('app', 'version', '1.0.0')
        
        # 窗口配置
        self.config.add_section('window')
        self.config.set('window', 'default_width', '1200')
        self.config.set('window', 'default_height', '800')
        self.config.set('window', 'edge_trigger_width', '5')
        self.config.set('window', 'peek_width', '300')
        self.config.set('window', 'hide_delay_ms', '2000')
        
        # UI配置
        self.config.add_section('ui')
        self.config.set('ui', 'theme', 'auto')
        self.config.set('ui', 'language', 'zh_CN')
        
        # 数据库配置
        self.config.add_section('database')
        self.config.set('database', 'db_name', 'notes.db')
        
        # 保存默认配置
        self.save_config()
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            section: 配置段名
            key: 配置键名
            fallback: 默认值
        
        Returns:
            配置值
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """获取整数配置值"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """获取浮点数配置值"""
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """获取布尔值配置"""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            section: 配置段名
            key: 配置键名
            value: 配置值
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_sections(self) -> list:
        """获取所有配置段"""
        return self.config.sections()
    
    def get_options(self, section: str) -> list:
        """获取指定段的所有配置项"""
        try:
            return self.config.options(section)
        except configparser.NoSectionError:
            return []