#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置界面
应用程序设置和配置管理
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import (
    ScrollArea, SettingCardGroup, SwitchSettingCard, RangeSettingCard,
    OptionsSettingCard, BodyLabel, FluentIcon as FIF
)

from utils.logger import LoggerMixin


class SettingsInterface(ScrollArea, LoggerMixin):
    """设置界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('SettingsInterface')
        
        self._init_ui()
        self.logger.debug("设置界面初始化完成")
    
    def _init_ui(self):
        """初始化界面"""
        self.view = QWidget()
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        layout = QVBoxLayout(self.view)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = BodyLabel("应用设置")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # 窗口设置组
        window_group = SettingCardGroup("窗口设置")
        
        self.always_on_top_card = SwitchSettingCard(
            FIF.PIN, "窗口置顶", "将窗口保持在最前面"
        )
        
        self.edge_hide_card = SwitchSettingCard(
            FIF.HIDE, "边缘隐藏", "启用边缘隐藏功能"
        )
        
        window_group.addSettingCard(self.always_on_top_card)
        window_group.addSettingCard(self.edge_hide_card)
        layout.addWidget(window_group)
        
        # 功能设置组
        feature_group = SettingCardGroup("功能设置")
        
        self.auto_save_card = SwitchSettingCard(
            FIF.SAVE, "自动保存", "编辑时自动保存笔记"
        )
        
        self.word_wrap_card = SwitchSettingCard(
            FIF.EDIT, "自动换行", "编辑器自动换行"
        )
        
        feature_group.addSettingCard(self.auto_save_card)
        feature_group.addSettingCard(self.word_wrap_card)
        layout.addWidget(feature_group)
        
        # UI设置组
        ui_group = SettingCardGroup("界面设置")
        
        self.theme_card = OptionsSettingCard(
            FIF.BRUSH, "应用主题", "选择应用程序主题",
            texts=["自动", "浅色", "深色"],
            values=["auto", "light", "dark"]
        )
        
        ui_group.addSettingCard(self.theme_card)
        layout.addWidget(ui_group)
        
        layout.addStretch()
    
    def set_controller(self, controller):
        """设置控制器"""
        self.controller = controller