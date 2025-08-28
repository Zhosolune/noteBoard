#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
首页界面
显示应用概览、最近笔记、统计信息等
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtGui import QPixmap, QPainter, QPainterPath

from qfluentwidgets import (
    ScrollArea, CardWidget, ImageLabel, BodyLabel, TitleLabel, 
    CaptionLabel, PushButton, PrimaryPushButton, InfoBadge,
    FlowLayout, ProgressRing, ElevatedCardWidget,
    IconWidget, FluentIcon as FIF, InfoBarPosition, InfoBar
)

from utils.logger import LoggerMixin


class HomeInterface(ScrollArea, LoggerMixin):
    """首页界面"""
    
    # 界面信号
    note_create_requested = Signal()
    note_open_requested = Signal(int)
    tag_manage_requested = Signal()
    search_requested = Signal(str)
    
    def __init__(self, parent=None):
        """初始化首页界面"""
        super().__init__(parent)
        self.setObjectName('HomeInterface')
        
        self.controller = None
        self._statistics_data = {}
        self._recent_notes = []
        
        # 动画
        self._card_animations = []
        
        # 初始化界面
        self._init_ui()
        self._init_animations()
        
        # 初始加载数据（不使用定时器）
        self.refresh_data()
        
        self.logger.debug("首页界面初始化完成")
    
    def _init_ui(self) -> None:
        """初始化用户界面"""
        # 创建主容器
        self.view = QWidget()
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        # 设置布局
        self.main_layout = QVBoxLayout(self.view)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)
        
        # 创建各个区域
        self._create_header()
        self._create_statistics_section()
        self._create_quick_actions_section()
        self._create_recent_notes_section()
        self._create_footer()
        
        # 设置滚动属性
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    def _create_header(self) -> None:
        """创建页面头部"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 欢迎标题
        self.welcome_label = TitleLabel("欢迎使用轻量笔记管理器")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        
        # 副标题
        self.subtitle_label = CaptionLabel("高效管理您的知识与灵感")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(self.welcome_label)
        header_layout.addWidget(self.subtitle_label)
        
        self.main_layout.addWidget(header_widget)
    
    def _create_statistics_section(self) -> None:
        """创建统计信息区域"""
        stats_widget = ElevatedCardWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # 标题
        stats_title = BodyLabel("数据统计")
        stats_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        stats_layout.addWidget(stats_title)
        
        # 统计卡片容器
        self.stats_container = QWidget()
        self.stats_grid = QGridLayout(self.stats_container)
        self.stats_grid.setSpacing(15)
        
        # 创建统计卡片
        self.notes_count_card = self._create_stat_card(
            "笔记数量", "0", FIF.EDIT, "#007ACC"
        )
        self.tags_count_card = self._create_stat_card(
            "标签数量", "0", FIF.TAG, "#28A745"
        )
        self.recent_activity_card = self._create_stat_card(
            "今日活动", "0", FIF.CALENDAR, "#FFC107"
        )
        self.total_words_card = self._create_stat_card(
            "总字数", "0", FIF.DOCUMENT, "#6F42C1"
        )
        
        # 添加到网格布局
        self.stats_grid.addWidget(self.notes_count_card, 0, 0)
        self.stats_grid.addWidget(self.tags_count_card, 0, 1)
        self.stats_grid.addWidget(self.recent_activity_card, 1, 0)
        self.stats_grid.addWidget(self.total_words_card, 1, 1)
        
        stats_layout.addWidget(self.stats_container)
        self.main_layout.addWidget(stats_widget)
    
    def _create_stat_card(self, title: str, value: str, icon: FIF, color: str) -> CardWidget:
        """
        创建统计卡片
        
        Args:
            title: 标题
            value: 数值
            icon: 图标
            color: 颜色
        
        Returns:
            统计卡片组件
        """
        card = CardWidget()
        card.setFixedHeight(120)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 图标
        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(48, 48)
        icon_widget.setStyleSheet(f"color: {color};")
        
        # 内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)
        
        # 数值标签
        value_label = TitleLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        
        # 标题标签
        title_label = CaptionLabel(title)
        title_label.setStyleSheet("color: gray;")
        
        content_layout.addWidget(value_label)
        content_layout.addWidget(title_label)
        content_layout.addStretch()
        
        layout.addWidget(icon_widget)
        layout.addWidget(content_widget, 1)
        
        # 存储标签引用以便更新
        card.value_label = value_label
        card.title_label = title_label
        
        return card
    
    def _create_quick_actions_section(self) -> None:
        """创建快速操作区域"""
        actions_widget = ElevatedCardWidget()
        actions_layout = QVBoxLayout(actions_widget)
        
        # 标题
        actions_title = BodyLabel("快速操作")
        actions_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        actions_layout.addWidget(actions_title)
        
        # 按钮容器
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        
        # 创建新笔记按钮
        self.new_note_btn = PrimaryPushButton("新建笔记")
        self.new_note_btn.setIcon(FIF.ADD)
        self.new_note_btn.setFixedHeight(50)
        self.new_note_btn.clicked.connect(self.note_create_requested.emit)
        
        # 管理标签按钮
        self.manage_tags_btn = PushButton("管理标签")
        self.manage_tags_btn.setIcon(FIF.TAG)
        self.manage_tags_btn.setFixedHeight(50)
        self.manage_tags_btn.clicked.connect(self.tag_manage_requested.emit)
        
        # 搜索笔记按钮
        self.search_btn = PushButton("搜索笔记")
        self.search_btn.setIcon(FIF.SEARCH)
        self.search_btn.setFixedHeight(50)
        self.search_btn.clicked.connect(lambda: self.search_requested.emit(""))
        
        buttons_layout.addWidget(self.new_note_btn, 2)
        buttons_layout.addWidget(self.manage_tags_btn, 1)
        buttons_layout.addWidget(self.search_btn, 1)
        
        actions_layout.addWidget(buttons_container)
        self.main_layout.addWidget(actions_widget)
    
    def _create_recent_notes_section(self) -> None:
        """创建最近笔记区域"""
        recent_widget = ElevatedCardWidget()
        recent_layout = QVBoxLayout(recent_widget)
        
        # 标题行
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        recent_title = BodyLabel("最近笔记")
        recent_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        # 查看更多按钮
        self.view_more_btn = PushButton("查看更多")
        self.view_more_btn.setIcon(FIF.RIGHT_ARROW)
        self.view_more_btn.clicked.connect(lambda: self.parent().switch_to_interface('note'))
        
        title_layout.addWidget(recent_title)
        title_layout.addStretch()
        title_layout.addWidget(self.view_more_btn)
        
        recent_layout.addWidget(title_container)
        
        # 笔记列表容器
        self.notes_container = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.setSpacing(10)
        
        # 空状态提示
        self.empty_state_widget = self._create_empty_state()
        self.notes_layout.addWidget(self.empty_state_widget)
        
        recent_layout.addWidget(self.notes_container)
        self.main_layout.addWidget(recent_widget)
    
    def _create_empty_state(self) -> QWidget:
        """创建空状态组件"""
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(15)
        
        # 空状态图标
        empty_icon = IconWidget(FIF.DOCUMENT)
        empty_icon.setFixedSize(64, 64)
        empty_icon.setStyleSheet("color: gray;")
        
        # 空状态文本
        empty_text = BodyLabel("暂无笔记")
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setStyleSheet("color: gray;")
        
        # 创建笔记按钮
        create_note_btn = PrimaryPushButton("创建第一条笔记")
        create_note_btn.setIcon(FIF.ADD)
        create_note_btn.clicked.connect(self.note_create_requested.emit)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        empty_layout.addWidget(create_note_btn)
        
        return empty_widget
    
    def _create_footer(self) -> None:
        """创建页面底部"""
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 20, 0, 0)
        
        # 版本信息
        version_label = CaptionLabel("轻量笔记管理器 v1.0.0")
        version_label.setStyleSheet("color: gray;")
        
        footer_layout.addWidget(version_label)
        footer_layout.addStretch()
        
        self.main_layout.addWidget(footer_widget)
        self.main_layout.addStretch()
    
    def _init_animations(self) -> None:
        """初始化动画效果"""
        # 为统计卡片创建动画
        stat_cards = [
            self.notes_count_card,
            self.tags_count_card, 
            self.recent_activity_card,
            self.total_words_card
        ]
        
        for i, card in enumerate(stat_cards):
            animation = QPropertyAnimation(card, b"pos")
            animation.setDuration(500)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            self._card_animations.append(animation)
    
    def set_controller(self, controller) -> None:
        """
        设置控制器
        
        Args:
            controller: 控制器实例
        """
        self.controller = controller
        
        # 连接控制器信号
        if hasattr(controller, 'operation_completed'):
            controller.operation_completed.connect(self._on_operation_completed)
        if hasattr(controller, 'error_occurred'):
            controller.error_occurred.connect(self._on_error_occurred)
    
    def refresh_data(self) -> None:
        """刷新页面数据"""
        if not self.controller:
            return
        
        try:
            # 刷新统计数据
            self._refresh_statistics()
            
            # 刷新最近笔记
            self._refresh_recent_notes()
            
            self.logger.debug("首页数据刷新完成")
            
        except Exception as e:
            self.log_error(e, "刷新首页数据失败")
    
    def _refresh_statistics(self) -> None:
        """刷新统计数据"""
        if not self.controller:
            return
        
        # 这里需要根据实际的控制器接口来实现
        # 暂时使用模拟数据
        self._update_statistics({
            'notes_count': 10,
            'tags_count': 5,
            'recent_activity': 3,
            'total_words': 2580
        })
    
    def _refresh_recent_notes(self) -> None:
        """刷新最近笔记"""
        if not self.controller:
            return
        
        # 这里需要根据实际的控制器接口来实现
        # 暂时使用模拟数据
        recent_notes = [
            {
                'id': 1,
                'title': '学习笔记：Python基础',
                'content': '今天学习了Python的基础语法...',
                'updated_at': '2025-01-20 14:30:00',
                'tags': [{'name': 'Python', 'color': '#007ACC'}]
            },
            {
                'id': 2,
                'title': '项目规划',
                'content': '需要完成的任务清单...',
                'updated_at': '2025-01-19 16:45:00',
                'tags': [{'name': '工作', 'color': '#28A745'}]
            }
        ]
        
        self._update_recent_notes(recent_notes)
    
    def _update_statistics(self, stats: Dict[str, Any]) -> None:
        """
        更新统计数据
        
        Args:
            stats: 统计数据字典
        """
        self._statistics_data = stats
        
        # 更新统计卡片
        if 'notes_count' in stats:
            self.notes_count_card.value_label.setText(str(stats['notes_count']))
        
        if 'tags_count' in stats:
            self.tags_count_card.value_label.setText(str(stats['tags_count']))
        
        if 'recent_activity' in stats:
            self.recent_activity_card.value_label.setText(str(stats['recent_activity']))
        
        if 'total_words' in stats:
            self.total_words_card.value_label.setText(f"{stats['total_words']:,}")
    
    def _update_recent_notes(self, notes: List[Dict[str, Any]]) -> None:
        """
        更新最近笔记列表
        
        Args:
            notes: 笔记列表
        """
        self._recent_notes = notes
        
        # 清除现有笔记项
        self._clear_notes_container()
        
        if not notes:
            # 显示空状态
            self.empty_state_widget.show()
        else:
            # 隐藏空状态
            self.empty_state_widget.hide()
            
            # 添加笔记项
            for note in notes[:5]:  # 最多显示5条
                note_item = self._create_note_item(note)
                self.notes_layout.addWidget(note_item)
    
    def _clear_notes_container(self) -> None:
        """清除笔记容器中的项目"""
        while self.notes_layout.count() > 1:  # 保留空状态组件
            item = self.notes_layout.takeAt(1)
            if item and item.widget():
                item.widget().deleteLater()
    
    def _create_note_item(self, note: Dict[str, Any]) -> CardWidget:
        """
        创建笔记项组件
        
        Args:
            note: 笔记数据
        
        Returns:
            笔记项卡片
        """
        card = CardWidget()
        card.setFixedHeight(80)
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)
        
        # 标题
        title_label = BodyLabel(note.get('title', '无标题'))
        title_label.setStyleSheet("font-weight: bold;")
        
        # 内容预览和时间
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 内容预览（限制长度）
        content_preview = note.get('content', '')[:50]
        if len(note.get('content', '')) > 50:
            content_preview += '...'
        
        preview_label = CaptionLabel(content_preview)
        preview_label.setStyleSheet("color: gray;")
        
        # 更新时间
        time_label = CaptionLabel(note.get('updated_at', ''))
        time_label.setStyleSheet("color: gray;")
        
        info_layout.addWidget(preview_label, 1)
        info_layout.addWidget(time_label)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(info_widget)
        
        # 标签区域
        tags_widget = QWidget()
        tags_layout = FlowLayout(tags_widget)
        
        for tag in note.get('tags', []):
            tag_badge = InfoBadge(tag['name'])
            tag_badge.setCustomBackgroundColor(tag['color'], tag['color'])
            tags_layout.addWidget(tag_badge)
        
        layout.addWidget(content_widget, 1)
        layout.addWidget(tags_widget)
        
        # 点击事件
        card.mousePressEvent = lambda event: self.note_open_requested.emit(note['id'])
        
        return card
    
    def show_welcome_animation(self) -> None:
        """显示欢迎动画"""
        # 可以添加欢迎动画效果
        pass
    
    # 信号槽
    def _on_operation_completed(self, operation_type: str, result: dict) -> None:
        """操作完成处理"""
        if operation_type in ['note_created', 'note_updated', 'note_deleted']:
            # 刷新数据
            self.refresh_data()
    
    def _on_error_occurred(self, error_type: str, message: str) -> None:
        """错误处理"""
        InfoBar.error(
            title="操作失败",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止所有动画
            if hasattr(self, '_card_animations'):
                for animation in self._card_animations:
                    if animation.state() == QPropertyAnimation.Running:
                        animation.stop()
                self._card_animations.clear()
            
            self.logger.debug("首页界面清理完成")
            
        except Exception as e:
            self.log_error(e, "首页界面清理失败")