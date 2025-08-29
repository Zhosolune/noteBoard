#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置界面
应用程序设置和配置管理
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from qfluentwidgets import (
    ScrollArea, CardWidget, SwitchButton, ComboBox, 
    BodyLabel, CaptionLabel, FluentIcon as FIF
)

from src.utils.logger import LoggerMixin


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
        layout.setSpacing(20)
        
        # 标题
        title = BodyLabel("应用设置")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # 窗口设置组
        window_card = self._create_window_settings_card()
        layout.addWidget(window_card)
        
        # 功能设置组
        feature_card = self._create_feature_settings_card()
        layout.addWidget(feature_card)
        
        # UI设置组
        ui_card = self._create_ui_settings_card()
        layout.addWidget(ui_card)
        
        layout.addStretch()
    
    def _create_window_settings_card(self) -> CardWidget:
        """创建窗口设置卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = BodyLabel("窗口设置")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 窗口置顶
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        top_label = BodyLabel("窗口置顶")
        top_desc = CaptionLabel("将窗口保持在最前面")
        top_desc.setStyleSheet("color: gray;")
        
        self.always_on_top_switch = SwitchButton()
        
        top_info = QWidget()
        top_info_layout = QVBoxLayout(top_info)
        top_info_layout.setContentsMargins(0, 0, 0, 0)
        top_info_layout.setSpacing(2)
        top_info_layout.addWidget(top_label)
        top_info_layout.addWidget(top_desc)
        
        top_layout.addWidget(top_info)
        top_layout.addStretch()
        top_layout.addWidget(self.always_on_top_switch)
        
        # 边缘隐藏
        edge_widget = QWidget()
        edge_layout = QHBoxLayout(edge_widget)
        edge_layout.setContentsMargins(0, 0, 0, 0)
        
        edge_label = BodyLabel("边缘隐藏")
        edge_desc = CaptionLabel("启用边缘隐藏功能")
        edge_desc.setStyleSheet("color: gray;")
        
        self.edge_hide_switch = SwitchButton()
        
        edge_info = QWidget()
        edge_info_layout = QVBoxLayout(edge_info)
        edge_info_layout.setContentsMargins(0, 0, 0, 0)
        edge_info_layout.setSpacing(2)
        edge_info_layout.addWidget(edge_label)
        edge_info_layout.addWidget(edge_desc)
        
        edge_layout.addWidget(edge_info)
        edge_layout.addStretch()
        edge_layout.addWidget(self.edge_hide_switch)
        
        layout.addWidget(top_widget)
        layout.addWidget(edge_widget)
        
        return card
    
    def _create_feature_settings_card(self) -> CardWidget:
        """创建功能设置卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = BodyLabel("功能设置")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 自动保存
        save_widget = QWidget()
        save_layout = QHBoxLayout(save_widget)
        save_layout.setContentsMargins(0, 0, 0, 0)
        
        save_label = BodyLabel("自动保存")
        save_desc = CaptionLabel("编辑时自动保存笔记")
        save_desc.setStyleSheet("color: gray;")
        
        self.auto_save_switch = SwitchButton()
        
        save_info = QWidget()
        save_info_layout = QVBoxLayout(save_info)
        save_info_layout.setContentsMargins(0, 0, 0, 0)
        save_info_layout.setSpacing(2)
        save_info_layout.addWidget(save_label)
        save_info_layout.addWidget(save_desc)
        
        save_layout.addWidget(save_info)
        save_layout.addStretch()
        save_layout.addWidget(self.auto_save_switch)
        
        # 自动换行
        wrap_widget = QWidget()
        wrap_layout = QHBoxLayout(wrap_widget)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        
        wrap_label = BodyLabel("自动换行")
        wrap_desc = CaptionLabel("编辑器自动换行")
        wrap_desc.setStyleSheet("color: gray;")
        
        self.word_wrap_switch = SwitchButton()
        
        wrap_info = QWidget()
        wrap_info_layout = QVBoxLayout(wrap_info)
        wrap_info_layout.setContentsMargins(0, 0, 0, 0)
        wrap_info_layout.setSpacing(2)
        wrap_info_layout.addWidget(wrap_label)
        wrap_info_layout.addWidget(wrap_desc)
        
        wrap_layout.addWidget(wrap_info)
        wrap_layout.addStretch()
        wrap_layout.addWidget(self.word_wrap_switch)
        
        layout.addWidget(save_widget)
        layout.addWidget(wrap_widget)
        
        return card
    
    def _create_ui_settings_card(self) -> CardWidget:
        """创建UI设置卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = BodyLabel("界面设置")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 主题选择
        theme_widget = QWidget()
        theme_layout = QHBoxLayout(theme_widget)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        
        theme_label = BodyLabel("应用主题")
        theme_desc = CaptionLabel("选择应用程序主题")
        theme_desc.setStyleSheet("color: gray;")
        
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["自动", "浅色", "深色"])
        self.theme_combo.setCurrentIndex(0)
        
        theme_info = QWidget()
        theme_info_layout = QVBoxLayout(theme_info)
        theme_info_layout.setContentsMargins(0, 0, 0, 0)
        theme_info_layout.setSpacing(2)
        theme_info_layout.addWidget(theme_label)
        theme_info_layout.addWidget(theme_desc)
        
        theme_layout.addWidget(theme_info)
        theme_layout.addStretch()
        theme_layout.addWidget(self.theme_combo)
        
        layout.addWidget(theme_widget)
        
        return card
    
    def set_controller(self, controller):
        """设置控制器"""
        self.controller = controller