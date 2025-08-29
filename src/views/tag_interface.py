#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签管理界面
实现标签的创建、分配、管理功能
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout

from qfluentwidgets import (
    ScrollArea, CardWidget, PrimaryPushButton, PushButton,
    LineEdit, ColorPickerButton, FlowLayout, InfoBadge, BodyLabel,
    CaptionLabel, MessageBox, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)

from src.utils.logger import LoggerMixin


class TagInterface(ScrollArea, LoggerMixin):
    """标签管理界面"""
    
    # 界面信号
    tag_created = Signal(str, str)
    tag_updated = Signal(int, dict)
    tag_deleted = Signal(int)
    
    def __init__(self, parent=None):
        """初始化标签管理界面"""
        super().__init__(parent)
        self.setObjectName('TagInterface')
        
        self.controller = None
        self._tags_data = []
        
        # 初始化界面
        self._init_ui()
        
        self.logger.debug("标签管理界面初始化完成")
    
    def _init_ui(self) -> None:
        """初始化用户界面"""
        self.view = QWidget()
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.main_layout = QVBoxLayout(self.view)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)
        
        # 创建各个区域
        self._create_header()
        self._create_new_tag_section()
        self._create_tags_grid()
        self._create_statistics_section()
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    def _create_header(self) -> None:
        """创建页面头部"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        
        title_label = BodyLabel("标签管理")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        refresh_btn = PushButton("刷新")
        refresh_btn.setIcon(FIF.SYNC)
        refresh_btn.clicked.connect(self.refresh_tags)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        
        self.main_layout.addWidget(header_widget)
    
    def _create_new_tag_section(self) -> None:
        """创建新建标签区域"""
        new_tag_card = CardWidget()
        layout = QVBoxLayout(new_tag_card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = BodyLabel("创建新标签")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)
        
        # 输入区域
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        
        # 标签名称输入
        self.tag_name_edit = LineEdit()
        self.tag_name_edit.setPlaceholderText("输入标签名称...")
        
        # 颜色选择器
        from PySide6.QtGui import QColor
        self.color_picker = ColorPickerButton(QColor(255, 0, 0), "标签颜色")
        
        # 创建按钮
        self.create_tag_btn = PrimaryPushButton("创建标签")
        self.create_tag_btn.setIcon(FIF.ADD)
        self.create_tag_btn.clicked.connect(self._create_new_tag)
        
        input_layout.addWidget(self.tag_name_edit, 2)
        input_layout.addWidget(self.color_picker)
        input_layout.addWidget(self.create_tag_btn)
        
        layout.addWidget(input_widget)
        self.main_layout.addWidget(new_tag_card)
    
    def _create_tags_grid(self) -> None:
        """创建标签网格"""
        self.tags_card = CardWidget()
        layout = QVBoxLayout(self.tags_card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        grid_title = BodyLabel("所有标签")
        grid_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(grid_title)
        
        # 标签容器
        self.tags_container = QWidget()
        self.tags_layout = FlowLayout(self.tags_container)
        
        layout.addWidget(self.tags_container, 1)
        self.main_layout.addWidget(self.tags_card)
    
    def _create_statistics_section(self) -> None:
        """创建统计信息区域"""
        stats_card = CardWidget()
        layout = QVBoxLayout(stats_card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        stats_title = BodyLabel("统计信息")
        stats_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(stats_title)
        
        # 统计信息
        self.stats_container = QWidget()
        stats_layout = QGridLayout(self.stats_container)
        
        self.total_tags_label = CaptionLabel("总标签数: 0")
        self.used_tags_label = CaptionLabel("已使用: 0")
        self.unused_tags_label = CaptionLabel("未使用: 0")
        
        stats_layout.addWidget(self.total_tags_label, 0, 0)
        stats_layout.addWidget(self.used_tags_label, 0, 1)
        stats_layout.addWidget(self.unused_tags_label, 0, 2)
        
        layout.addWidget(self.stats_container)
        self.main_layout.addWidget(stats_card)
    
    def set_controller(self, controller) -> None:
        """设置控制器"""
        self.controller = controller
        
        # 连接信号
        if hasattr(controller, 'tag_created'):
            controller.tag_created.connect(self._on_tag_created)
        if hasattr(controller, 'tag_updated'):
            controller.tag_updated.connect(self._on_tag_updated)
        if hasattr(controller, 'tag_deleted'):
            controller.tag_deleted.connect(self._on_tag_deleted)
        if hasattr(controller, 'tag_list_changed'):
            controller.tag_list_changed.connect(self.refresh_tags)
        
        # 加载数据
        self.refresh_tags()
    
    def refresh_tags(self) -> None:
        """刷新标签列表"""
        if not self.controller:
            return
        
        try:
            result = self.controller.get_tag_list()
            if result.success:
                self._tags_data = result.data['tags']
                self._update_tags_display()
                self._update_statistics()
            else:
                self._show_error_message(f"加载标签失败: {result.error}")
                
        except Exception as e:
            self.log_error(e, "刷新标签列表失败")
    
    def _update_tags_display(self) -> None:
        """更新标签显示"""
        # 清除现有标签
        while self.tags_layout.count() > 0:
            item = self.tags_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 添加标签项
        for tag in self._tags_data:
            tag_item = self._create_tag_item(tag)
            self.tags_layout.addWidget(tag_item)
    
    def _create_tag_item(self, tag: Dict[str, Any]) -> QWidget:
        """创建标签项"""
        item_widget = CardWidget()
        item_widget.setFixedSize(200, 120)
        
        layout = QVBoxLayout(item_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标签显示
        tag_badge = InfoBadge(tag['name'])
        tag_badge.setCustomBackgroundColor(tag['color'], tag['color'])
        layout.addWidget(tag_badge, 0, Qt.AlignCenter)
        
        # 使用数量
        usage_label = CaptionLabel(f"使用次数: {tag.get('note_count', 0)}")
        usage_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(usage_label)
        
        # 操作按钮
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        edit_btn = PushButton("编辑")
        edit_btn.setIcon(FIF.EDIT)
        edit_btn.clicked.connect(lambda: self._edit_tag(tag))
        
        delete_btn = PushButton("删除")
        delete_btn.setIcon(FIF.DELETE)
        delete_btn.clicked.connect(lambda: self._delete_tag(tag['id']))
        
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addWidget(delete_btn)
        
        layout.addWidget(buttons_widget)
        layout.addStretch()
        
        return item_widget
    
    def _create_new_tag(self) -> None:
        """创建新标签"""
        if not self.controller:
            return
        
        name = self.tag_name_edit.text().strip()
        if not name:
            self._show_error_message("请输入标签名称")
            return
        
        color = self.color_picker.color.name()
        
        result = self.controller.create_tag(name, color)
        if result.success:
            self.tag_name_edit.clear()
            self.tag_created.emit(name, color)
        else:
            self._show_error_message(f"创建标签失败: {result.error}")
    
    def _edit_tag(self, tag: Dict[str, Any]) -> None:
        """编辑标签"""
        # TODO: 实现编辑对话框
        pass
    
    def _delete_tag(self, tag_id: int) -> None:
        """删除标签"""
        if not self.controller:
            return
        
        msg_box = MessageBox("删除确认", "确定要删除这个标签吗？", self)
        if msg_box.exec():
            result = self.controller.delete_tag(tag_id)
            if result.success:
                self.tag_deleted.emit(tag_id)
            else:
                self._show_error_message(f"删除标签失败: {result.error}")
    
    def _update_statistics(self) -> None:
        """更新统计信息"""
        total = len(self._tags_data)
        used = len([tag for tag in self._tags_data if tag.get('note_count', 0) > 0])
        unused = total - used
        
        self.total_tags_label.setText(f"总标签数: {total}")
        self.used_tags_label.setText(f"已使用: {used}")
        self.unused_tags_label.setText(f"未使用: {unused}")
    
    def _show_error_message(self, message: str) -> None:
        """显示错误信息"""
        InfoBar.error(
            title="错误",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )
    
    # 控制器事件处理
    def _on_tag_created(self, tag_id: int, name: str, color: str) -> None:
        """标签创建事件"""
        self.refresh_tags()
    
    def _on_tag_updated(self, tag_id: int) -> None:
        """标签更新事件"""
        self.refresh_tags()
    
    def _on_tag_deleted(self, tag_id: int, name: str) -> None:
        """标签删除事件"""
        self.refresh_tags()