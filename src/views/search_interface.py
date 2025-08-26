#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索界面
实现全文搜索和标签筛选功能
"""

from typing import List, Dict, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    ScrollArea, CardWidget, SearchLineEdit, SegmentedWidget,
    ListView, FlowLayout, InfoBadge, BodyLabel, CaptionLabel,
    FluentIcon as FIF
)

from utils.logger import LoggerMixin


class SearchInterface(ScrollArea, LoggerMixin):
    """搜索界面"""
    
    # 信号
    note_selected = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('SearchInterface')
        
        self.controller = None
        self._search_results = []
        
        self._init_ui()
        self.logger.debug("搜索界面初始化完成")
    
    def _init_ui(self) -> None:
        """初始化界面"""
        self.view = QWidget()
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        layout = QVBoxLayout(self.view)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 搜索框
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索笔记内容...")
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)
        
        # 搜索类型选择
        self.search_type = SegmentedWidget()
        self.search_type.addItem('content', "内容搜索")
        self.search_type.addItem('title', "标题搜索")  
        self.search_type.addItem('tag', "标签搜索")
        layout.addWidget(self.search_type)
        
        # 结果列表
        self.results_list = ListView()
        layout.addWidget(self.results_list, 1)
        
        # 结果统计
        self.results_info = CaptionLabel("输入关键词开始搜索")
        layout.addWidget(self.results_info)
    
    def set_controller(self, controller):
        """设置控制器"""
        self.controller = controller
    
    def _on_search(self, text: str):
        """执行搜索"""
        if not self.controller or len(text.strip()) < 2:
            self.results_list.clear()
            self.results_info.setText("输入至少2个字符开始搜索")
            return
        
        try:
            result = self.controller.search_notes(text.strip())
            if result.success:
                self._search_results = result.data['notes']
                self._update_results()
                count = len(self._search_results)
                self.results_info.setText(f"找到 {count} 条相关笔记")
            else:
                self.results_info.setText("搜索失败")
        except Exception as e:
            self.log_error(e, "搜索失败")
    
    def _update_results(self):
        """更新搜索结果"""
        self.results_list.clear()
        # TODO: 添加搜索结果显示逻辑