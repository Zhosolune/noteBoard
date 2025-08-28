#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔记管理界面
实现笔记的创建、编辑、显示功能
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QStackedWidget
)
from PySide6.QtGui import QFont

from qfluentwidgets import (
    ScrollArea, CardWidget, SearchLineEdit, PrimaryPushButton, PushButton,
    SegmentedWidget, ToolButton, DropDownPushButton, RoundMenu, Action,
    ListView, TextEdit, LineEdit, BodyLabel, CaptionLabel, TitleLabel,
    InfoBadge, FlowLayout, MessageBox, InfoBar, InfoBarPosition,
    FluentIcon as FIF, MenuAnimationType, IconWidget
)

from utils.logger import LoggerMixin


class NoteInterface(ScrollArea, LoggerMixin):
    """笔记管理界面"""
    
    # 界面信号
    note_selected = Signal(int)
    note_create_requested = Signal()
    note_save_requested = Signal(int, dict)
    note_delete_requested = Signal(int)
    tag_add_requested = Signal(int, str)
    tag_remove_requested = Signal(int, int)
    
    def __init__(self, parent=None):
        """初始化笔记管理界面"""
        super().__init__(parent)
        self.setObjectName('NoteInterface')
        
        self.controller = None
        self._current_note_id = None
        self._notes_data = []
        self._is_editing = False
        
        # 初始化界面
        self._init_ui()
        self._init_toolbar()
        self._init_content_area()
        
        # 连接视图切换信号（在内容区域创建后）
        if hasattr(self, 'view_stack'):
            self.view_stack.currentChanged.connect(self._on_view_stack_changed)
        
        self.logger.debug("笔记管理界面初始化完成")
    
    def _init_ui(self) -> None:
        """初始化用户界面"""
        # 创建主容器
        self.view = QWidget()
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.view)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 设置滚动属性
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    # def _init_toolbar(self) -> None:
    #     """初始化工具栏"""
    #     toolbar_widget = QWidget()
    #     toolbar_layout = QHBoxLayout(toolbar_widget)
    #     toolbar_layout.setContentsMargins(0, 0, 0, 0)
    #     toolbar_layout.setSpacing(10)
        
    #     # 搜索框
    #     self.search_edit = SearchLineEdit()
    #     self.search_edit.setPlaceholderText("搜索笔记...")
    #     self.search_edit.setFixedWidth(300)
    #     self.search_edit.textChanged.connect(self._on_search_text_changed)
        
    #     # 新建笔记按钮
    #     self.new_note_btn = PrimaryPushButton("新建笔记")
    #     self.new_note_btn.setIcon(FIF.ADD)
    #     self.new_note_btn.clicked.connect(self._create_new_note)
        
    #     # 视图切换
    #     self.view_toggle = SegmentedWidget()
    #     self.view_toggle.addItem('list', "列表视图", lambda: self._switch_view('list'))
    #     self.view_toggle.addItem('card', "卡片视图", lambda: self._switch_view('card'))
    #     self.view_toggle.setCurrentItem('list')
        
    #     # 更多操作按钮
    #     self.more_btn = DropDownPushButton("更多操作")
    #     self.more_btn.setIcon(FIF.MORE)
    #     self._init_more_menu()
        
    #     toolbar_layout.addWidget(self.search_edit)
    #     toolbar_layout.addStretch()
    #     toolbar_layout.addWidget(self.view_toggle)
    #     toolbar_layout.addWidget(self.new_note_btn)
    #     toolbar_layout.addWidget(self.more_btn)
        
    #     self.main_layout.addWidget(toolbar_widget)

    def _init_toolbar(self) -> None:
        """初始化工具栏"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)
        
        # 搜索框
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索笔记...")
        self.search_edit.setFixedWidth(300)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        
        # 新建笔记按钮
        self.new_note_btn = PrimaryPushButton("新建笔记")
        self.new_note_btn.setIcon(FIF.ADD)
        self.new_note_btn.clicked.connect(self._create_new_note)
        
        # 视图切换（SegmentedWidget）
        self.view_toggle = SegmentedWidget()
        self.view_toggle.addItem("list", "列表视图")
        self.view_toggle.addItem("card", "卡片视图")
        self.view_toggle.setCurrentItem("list")
        
        # 用信号处理切换逻辑
        self.view_toggle.currentItemChanged.connect(self._switch_view)

        # 更多操作按钮
        self.more_btn = DropDownPushButton("更多操作")
        self.more_btn.setIcon(FIF.MORE)
        self._init_more_menu()
        
        toolbar_layout.addWidget(self.search_edit)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.view_toggle)
        toolbar_layout.addWidget(self.new_note_btn)
        toolbar_layout.addWidget(self.more_btn)
        
        self.main_layout.addWidget(toolbar_widget)

    
    def _init_more_menu(self) -> None:
        """初始化更多操作菜单"""
        menu = RoundMenu(parent=self)
        
        # 导入笔记
        import_action = Action(FIF.FOLDER, "导入笔记")
        import_action.triggered.connect(self._import_notes)
        menu.addAction(import_action)
        
        # 导出笔记
        export_action = Action(FIF.SHARE, "导出笔记")
        export_action.triggered.connect(self._export_notes)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # 刷新列表
        refresh_action = Action(FIF.SYNC, "刷新列表")
        refresh_action.triggered.connect(self.refresh_notes_list)
        menu.addAction(refresh_action)
        
        self.more_btn.setMenu(menu)
    
    def _init_content_area(self) -> None:
        """初始化主内容区域"""
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        # 左侧笔记列表
        self.notes_list_widget = self._create_notes_list_widget()
        
        # 右侧视图切换区域（使用QStackedWidget）
        self.view_container = self._create_view_container()
        
        # 添加到分割器
        self.splitter.addWidget(self.notes_list_widget)
        self.splitter.addWidget(self.view_container)
        
        # 设置分割比例
        self.splitter.setSizes([350, 600])
        
        self.main_layout.addWidget(self.splitter)
    
    def _create_notes_list_widget(self) -> QWidget:
        """创建笔记列表组件"""
        widget = CardWidget()
        widget.setFixedWidth(370)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 列表标题
        list_title = BodyLabel("笔记列表")
        list_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(list_title)
        
        # 筛选器区域
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        # 排序选择
        self.sort_combo = SegmentedWidget()
        self.sort_combo.addItem('time', "按时间", lambda: self._sort_notes('time'))
        self.sort_combo.addItem('title', "按标题", lambda: self._sort_notes('title'))
        self.sort_combo.setCurrentItem('time')
        
        filter_layout.addWidget(self.sort_combo)
        layout.addWidget(filter_widget)
        
        # 笔记列表
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self._on_note_item_clicked)
        layout.addWidget(self.notes_list, 1)
        
        # 列表底部信息
        self.list_info_label = CaptionLabel("共 0 条笔记")
        self.list_info_label.setStyleSheet("color: gray;")
        layout.addWidget(self.list_info_label)
        
        return widget
    
    def _create_view_container(self) -> QWidget:
        """创建视图切换容器（使用QStackedWidget的正确实现）"""
        container = CardWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建堆叠组件（用于切换不同视图）
        self.view_stack = QStackedWidget()
        
        # 创建列表视图（默认视图）
        self.list_view_widget = self._create_note_detail_widget()
        self.list_view_widget.setObjectName('listView')
        
        # 创建卡片视图
        self.card_view_widget = self._create_card_view_widget()
        self.card_view_widget.setObjectName('cardView')
        
        # 添加到堆叠组件
        self.view_stack.addWidget(self.list_view_widget)
        self.view_stack.addWidget(self.card_view_widget)
        
        # 设置默认视图
        self.view_stack.setCurrentWidget(self.list_view_widget)
        
        # 添加到容器
        layout.addWidget(self.view_stack)
        
        # 保存引用以保持兼容性
        self.note_detail_widget = self.list_view_widget
        
        return container
    
    def _create_note_detail_widget(self) -> QWidget:
        widget = CardWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 笔记头部
        self.note_header = self._create_note_header()
        layout.addWidget(self.note_header)
        
        # 标题编辑器
        self.title_edit = LineEdit()
        self.title_edit.setPlaceholderText("输入笔记标题...")
        self.title_edit.setStyleSheet("font-size: 18px; font-weight: bold; border: none; background: transparent;")
        self.title_edit.textChanged.connect(self._on_title_changed)
        layout.addWidget(self.title_edit)
        
        # 标签区域
        self.tags_area = self._create_tags_area()
        layout.addWidget(self.tags_area)
        
        # 内容编辑器
        self.content_edit = TextEdit()
        self.content_edit.setPlaceholderText("开始写作...")
        self.content_edit.textChanged.connect(self._on_content_changed)
        
        # 设置编辑器字体
        font = QFont()
        font.setFamily("Consolas, Monaco, monospace")
        font.setPointSize(12)
        self.content_edit.setFont(font)
        
        layout.addWidget(self.content_edit, 1)
        
        # 状态栏
        self.status_bar = self._create_status_bar()
        layout.addWidget(self.status_bar)
        
        # 初始状态为禁用
        self._set_editor_enabled(False)
        
        return widget
    
    def _create_card_view_widget(self) -> QWidget:
        """创建卡片视图组件"""
        widget = CardWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 卡片视图标题
        card_title = BodyLabel("卡片视图")
        card_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(card_title)
        
        # 卡片容器（使用滚动区域）
        scroll_area = ScrollArea()
        scroll_content = QWidget()
        self.card_layout = FlowLayout(scroll_content)
        self.card_layout.setContentsMargins(10, 10, 10, 10)
        self.card_layout.setHorizontalSpacing(15)
        self.card_layout.setVerticalSpacing(15)
        
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        layout.addWidget(scroll_area, 1)
        
        # 初始化时显示提示
        self._show_card_view_placeholder()
        
        return widget
    
    def _show_card_view_placeholder(self) -> None:
        """显示卡片视图占位符"""
        placeholder = CardWidget()
        placeholder.setFixedSize(200, 150)
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        
        icon = IconWidget(FIF.VIEW)
        icon.setFixedSize(48, 48)
        icon.setStyleSheet("color: gray;")
        
        text = BodyLabel("卡片视图模式")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("color: gray;")
        
        desc = CaptionLabel("选择笔记在此显示")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: gray; font-size: 12px;")
        
        placeholder_layout.addWidget(icon)
        placeholder_layout.addWidget(text)
        placeholder_layout.addWidget(desc)
        
        self.card_layout.addWidget(placeholder)
    
    def _create_note_header(self) -> QWidget:
        """创建笔记头部"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 10)
        
        # 笔记信息
        self.note_info_label = CaptionLabel("选择一个笔记开始编辑")
        self.note_info_label.setStyleSheet("color: gray;")
        
        # 操作按钮
        self.save_btn = PushButton("保存")
        self.save_btn.setIcon(FIF.SAVE)
        self.save_btn.clicked.connect(self._save_current_note)
        self.save_btn.setEnabled(False)
        
        self.delete_btn = PushButton("删除")
        self.delete_btn.setIcon(FIF.DELETE)
        self.delete_btn.clicked.connect(self._delete_current_note)
        self.delete_btn.setEnabled(False)
        
        layout.addWidget(self.note_info_label)
        layout.addStretch()
        layout.addWidget(self.save_btn)
        layout.addWidget(self.delete_btn)
        
        return widget
    
    def _create_tags_area(self) -> QWidget:
        """创建标签区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 10)
        
        # 标签标题
        tags_title = CaptionLabel("标签")
        layout.addWidget(tags_title)
        
        # 标签容器
        self.tags_container = QWidget()
        self.tags_layout = FlowLayout(self.tags_container)
        
        # 添加标签按钮
        self.add_tag_btn = PushButton("添加标签")
        self.add_tag_btn.setIcon(FIF.ADD)
        self.add_tag_btn.clicked.connect(self._show_add_tag_dialog)
        self.add_tag_btn.setEnabled(False)
        self.tags_layout.addWidget(self.add_tag_btn)
        
        layout.addWidget(self.tags_container)
        
        return widget
    
    def _create_status_bar(self) -> QWidget:
        """创建状态栏"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        
        # 字数统计
        self.word_count_label = CaptionLabel("0 字")
        self.word_count_label.setStyleSheet("color: gray;")
        
        # 保存状态
        self.save_status_label = CaptionLabel("已保存")
        self.save_status_label.setStyleSheet("color: green;")
        
        # 最后修改时间
        self.last_modified_label = CaptionLabel("")
        self.last_modified_label.setStyleSheet("color: gray;")
        
        layout.addWidget(self.word_count_label)
        layout.addStretch()
        layout.addWidget(self.save_status_label)
        layout.addWidget(self.last_modified_label)
        
        return widget
    
    def set_controller(self, controller) -> None:
        """设置控制器"""
        self.controller = controller
        
        # 连接控制器信号
        if hasattr(controller, 'note_created'):
            controller.note_created.connect(self._on_note_created)
        if hasattr(controller, 'note_updated'):
            controller.note_updated.connect(self._on_note_updated)
        if hasattr(controller, 'note_deleted'):
            controller.note_deleted.connect(self._on_note_deleted)
        if hasattr(controller, 'note_list_changed'):
            controller.note_list_changed.connect(self.refresh_notes_list)
        
        # 初始加载数据
        self.refresh_notes_list()
    
    def refresh_notes_list(self) -> None:
        """刷新笔记列表"""
        if not self.controller:
            return
        
        try:
            # 获取笔记列表
            result = self.controller.get_note_list()
            if result.success:
                self._notes_data = result.data['notes']
                self._update_notes_list()
                self._update_list_info()
            else:
                self._show_error_message(f"加载笔记列表失败: {result.error}")
                
        except Exception as e:
            self.log_error(e, "刷新笔记列表失败")
            self._show_error_message("刷新笔记列表时发生错误")
    
    def _update_notes_list(self) -> None:
        """更新笔记列表显示"""
        self.notes_list.clear()
        
        for note in self._notes_data:
            item = QListWidgetItem()
            item_widget = self._create_note_item_widget(note)
            
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.UserRole, note['id'])
            
            self.notes_list.addItem(item)
            self.notes_list.setItemWidget(item, item_widget)
        
        # 同时更新卡片视图（如果当前是卡片视图）
        if hasattr(self, 'view_stack') and self.view_stack.currentWidget() == self.card_view_widget:
            self._update_card_view()
    
    def _create_note_item_widget(self, note: Dict[str, Any]) -> QWidget:
        """创建笔记列表项组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # 标题
        title_label = BodyLabel(note.get('title', '无标题'))
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        
        # 内容预览
        content = note.get('content', '')
        preview = content[:100] + '...' if len(content) > 100 else content
        preview_label = CaptionLabel(preview)
        preview_label.setStyleSheet("color: gray;")
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label)
        
        # 时间和标签
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 更新时间
        time_label = CaptionLabel(note.get('updated_at', ''))
        time_label.setStyleSheet("color: gray; font-size: 10px;")
        
        # 标签
        tags_widget = QWidget()
        tags_layout = FlowLayout(tags_widget)
        
        for tag in note.get('tags', [])[:3]:  # 最多显示3个标签
            tag_badge = InfoBadge(tag['name'])
            tag_badge.setCustomBackgroundColor(tag['color'], tag['color'])
            tags_layout.addWidget(tag_badge)
        
        info_layout.addWidget(time_label)
        info_layout.addStretch()
        info_layout.addWidget(tags_widget)
        
        layout.addWidget(info_widget)
        
        return widget
    
    def _update_list_info(self) -> None:
        """更新列表信息"""
        count = len(self._notes_data)
        self.list_info_label.setText(f"共 {count} 条笔记")
    
    def _create_new_note(self) -> None:
        """创建新笔记"""
        if not self.controller:
            return
        
        # 保存当前笔记
        if self._current_note_id and self._is_editing:
            self._save_current_note()
        
        # 请求创建新笔记
        result = self.controller.create_note("新建笔记", "")
        if result.success:
            note_id = result.data['note_id']
            self._select_note(note_id)
        else:
            self._show_error_message(f"创建笔记失败: {result.error}")
    
    def _select_note(self, note_id: int) -> None:
        """选择笔记"""
        if not self.controller:
            return
        
        # 保存当前编辑的笔记
        if self._current_note_id and self._is_editing:
            self._save_current_note()
        
        # 加载新笔记
        result = self.controller.get_note(note_id)
        if result.success:
            note = result.data
            self._load_note_to_editor(note)
            self._current_note_id = note_id
            self.note_selected.emit(note_id)
        else:
            self._show_error_message(f"加载笔记失败: {result.error}")
    
    def _load_note_to_editor(self, note: Dict[str, Any]) -> None:
        """加载笔记到编辑器"""
        # 设置标题
        self.title_edit.setText(note.get('title', ''))
        
        # 设置内容
        self.content_edit.setPlainText(note.get('content', ''))
        
        # 更新笔记信息
        created_at = note.get('created_at', '')
        updated_at = note.get('updated_at', '')
        self.note_info_label.setText(f"创建于 {created_at}")
        self.last_modified_label.setText(f"修改于 {updated_at}")
        
        # 加载标签
        self._load_tags(note.get('tags', []))
        
        # 更新字数统计
        self._update_word_count()
        
        # 启用编辑器
        self._set_editor_enabled(True)
        
        # 重置编辑状态
        self._is_editing = False
        self._update_save_status(True)
    
    def _load_tags(self, tags: List[Dict[str, Any]]) -> None:
        """加载标签"""
        # 清除现有标签
        self._clear_tags()
        
        # 添加标签
        for tag in tags:
            self._add_tag_to_display(tag)
    
    def _clear_tags(self) -> None:
        """清除标签显示"""
        while self.tags_layout.count() > 1:  # 保留添加按钮
            item = self.tags_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
    
    def _add_tag_to_display(self, tag: Dict[str, Any]) -> None:
        """添加标签到显示区域"""
        tag_widget = QWidget()
        tag_layout = QHBoxLayout(tag_widget)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(5)
        
        # 标签badge
        tag_badge = InfoBadge(tag['name'])
        tag_badge.setCustomBackgroundColor(tag['color'], tag['color'])
        
        # 删除按钮
        remove_btn = ToolButton()
        remove_btn.setIcon(FIF.CLOSE)
        remove_btn.setFixedSize(16, 16)
        remove_btn.clicked.connect(
            lambda: self._remove_tag_from_note(tag['id'])
        )
        
        tag_layout.addWidget(tag_badge)
        tag_layout.addWidget(remove_btn)
        
        # 插入到添加按钮之前
        index = self.tags_layout.count() - 1
        self.tags_layout.insertWidget(index, tag_widget)
    
    def _set_editor_enabled(self, enabled: bool) -> None:
        """设置编辑器启用状态"""
        self.title_edit.setEnabled(enabled)
        self.content_edit.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.add_tag_btn.setEnabled(enabled)
    
    def _save_current_note(self) -> None:
        """保存当前笔记"""
        if not self.controller or not self._current_note_id:
            return
        
        data = {
            'title': self.title_edit.text().strip(),
            'content': self.content_edit.toPlainText()
        }
        
        result = self.controller.update_note(self._current_note_id, data)
        if result.success:
            self._update_save_status(True)
            self._is_editing = False
        else:
            self._show_error_message(f"保存笔记失败: {result.error}")
    
    def _delete_current_note(self) -> None:
        """删除当前笔记"""
        if not self.controller or not self._current_note_id:
            return
        
        # 确认删除
        msg_box = MessageBox(
            "删除确认",
            "确定要删除这条笔记吗？此操作不可恢复。",
            self
        )
        
        if msg_box.exec():
            result = self.controller.delete_note(self._current_note_id)
            if result.success:
                self._clear_editor()
                self._current_note_id = None
            else:
                self._show_error_message(f"删除笔记失败: {result.error}")
    
    def _clear_editor(self) -> None:
        """清空编辑器"""
        self.title_edit.clear()
        self.content_edit.clear()
        self.note_info_label.setText("选择一个笔记开始编辑")
        self.last_modified_label.clear()
        self._clear_tags()
        self._set_editor_enabled(False)
        self._update_word_count()
    
    def _auto_save_note(self) -> None:
        """自动保存笔记"""
        if self._current_note_id and self._is_editing:
            self._save_current_note()
    
    def _update_word_count(self) -> None:
        """更新字数统计"""
        content = self.content_edit.toPlainText()
        word_count = len(content)
        self.word_count_label.setText(f"{word_count} 字")
    
    def _update_save_status(self, saved: bool) -> None:
        """更新保存状态"""
        if saved:
            self.save_status_label.setText("已保存")
            self.save_status_label.setStyleSheet("color: green;")
        else:
            self.save_status_label.setText("未保存")
            self.save_status_label.setStyleSheet("color: orange;")
    
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
    
    # 事件处理
    def _on_note_item_clicked(self, item: QListWidgetItem) -> None:
        """笔记项点击事件"""
        note_id = item.data(Qt.UserRole)
        if note_id:
            self._select_note(note_id)
    
    def _on_title_changed(self) -> None:
        """标题变更事件"""
        if self._current_note_id:
            self._is_editing = True
            self._update_save_status(False)
            
            # 直接通知控制器处理自动保存
            if self.controller:
                title = self.title_edit.text()
                self.controller.schedule_auto_save(self._current_note_id, {'title': title})
    
    def _on_content_changed(self) -> None:
        """内容变更事件"""
        if self._current_note_id:
            self._is_editing = True
            self._update_save_status(False)
            self._update_word_count()
            
            # 直接通知控制器处理自动保存
            if self.controller:
                content = self.content_edit.toPlainText()
                self.controller.schedule_auto_save(self._current_note_id, {'content': content})
    
    def _on_search_text_changed(self, text: str) -> None:
        """搜索文本变更事件"""
        # 实现搜索功能
        if not self.controller:
            return
        
        if text.strip():
            result = self.controller.search_notes(text.strip())
            if result.success:
                self._notes_data = result.data['notes']
                self._update_notes_list()
                self._update_list_info()
        else:
            self.refresh_notes_list()
    
    def _switch_view(self, view_type: str) -> None:
        """切换视图类型（正确实现）"""
        self.logger.debug(f"切换到 {view_type} 视图")
        
        if view_type == 'list':
            # 切换到列表视图
            self.view_stack.setCurrentWidget(self.list_view_widget)
            self.note_detail_widget = self.list_view_widget
        elif view_type == 'card':
            # 切换到卡片视图
            self.view_stack.setCurrentWidget(self.card_view_widget)
            self.note_detail_widget = self.card_view_widget
            self._update_card_view()
        
        # 可以在这里添加其他视图切换逻辑
        
    def _update_card_view(self) -> None:
        """更新卡片视图内容"""
        # 清除现有的卡片（使用更安全的方法）
        # 获取所有子控件
        children_to_remove = []
        for i in range(self.card_layout.count()):
            item = self.card_layout.itemAt(i)
            if item and item.widget():
                children_to_remove.append(item.widget())
        
        # 删除所有子控件
        for widget in children_to_remove:
            self.card_layout.removeWidget(widget)
            widget.deleteLater()
        
        if not self._notes_data:
            # 没有笔记时显示占位符
            self._show_card_view_placeholder()
        else:
            # 为每个笔记创建卡片
            for note in self._notes_data:
                card = self._create_note_card(note)
                self.card_layout.addWidget(card)
    
    def _create_note_card(self, note: Dict[str, Any]) -> CardWidget:
        """为笔记创建卡片组件"""
        card = CardWidget()
        card.setFixedSize(250, 180)
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # 标题
        title = BodyLabel(note.get('title', '无标题')[:20] + ('...' if len(note.get('title', '')) > 20 else ''))
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 内容预览
        content_preview = note.get('content', '')[:60]
        if len(note.get('content', '')) > 60:
            content_preview += '...'
        
        content_label = CaptionLabel(content_preview)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(content_label, 1)
        
        # 标签区域
        if note.get('tags'):
            tags_container = QWidget()
            tags_layout = FlowLayout(tags_container)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            
            for tag in note.get('tags', [])[:3]:  # 最多显示3个标签
                tag_badge = InfoBadge(tag['name'])
                tag_badge.setCustomBackgroundColor(tag['color'], tag['color'])
                tags_layout.addWidget(tag_badge)
            
            layout.addWidget(tags_container)
        
        # 时间信息
        time_label = CaptionLabel(note.get('updated_at', ''))
        time_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(time_label)
        
        # 点击事件
        card.mousePressEvent = lambda event: self._on_note_card_clicked(note['id'])
        
        return card
    
    def _on_note_card_clicked(self, note_id: int) -> None:
        """笔记卡片点击事件"""
        # 切换到列表视图并选中笔记
        self.view_toggle.setCurrentItem('list')
        self._switch_view('list')
        self._select_note(note_id)
    
    def _on_view_stack_changed(self, index: int) -> None:
        """视图堆叠组件变化事件"""
        # 同步SegmentedWidget的选中状态
        current_widget = self.view_stack.widget(index)
        if current_widget:
            if current_widget.objectName() == 'listView':
                self.view_toggle.setCurrentItem('list')
            elif current_widget.objectName() == 'cardView':
                self.view_toggle.setCurrentItem('card')
    
    def _sort_notes(self, sort_type: str) -> None:
        """排序笔记"""
        if sort_type == 'title':
            self._notes_data.sort(key=lambda x: x.get('title', ''))
        else:  # 按时间排序
            self._notes_data.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        self._update_notes_list()
    
    def _import_notes(self) -> None:
        """导入笔记"""
        # TODO: 实现笔记导入功能
        self.logger.debug("导入笔记")
    
    def _export_notes(self) -> None:
        """导出笔记"""
        # TODO: 实现笔记导出功能
        self.logger.debug("导出笔记")
    
    def _show_add_tag_dialog(self) -> None:
        """显示添加标签对话框"""
        # TODO: 实现添加标签对话框
        self.logger.debug("添加标签")
    
    def _remove_tag_from_note(self, tag_id: int) -> None:
        """从笔记移除标签"""
        if not self.controller or not self._current_note_id:
            return
        
        result = self.controller.remove_tag_from_note(self._current_note_id, tag_id)
        if result.success:
            # 重新加载笔记以刷新标签显示
            self._select_note(self._current_note_id)
        else:
            self._show_error_message(f"移除标签失败: {result.error}")
    
    # 控制器事件处理
    def _on_note_created(self, note_id: int, title: str) -> None:
        """笔记创建事件处理"""
        self.refresh_notes_list()
    
    def _on_note_updated(self, note_id: int) -> None:
        """笔记更新事件处理"""
        self.refresh_notes_list()
    
    def _on_note_deleted(self, note_id: int, title: str) -> None:
        """笔记删除事件处理"""
        if note_id == self._current_note_id:
            self._clear_editor()
            self._current_note_id = None
        self.refresh_notes_list()
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 如果正在编辑，保存当前笔记
            if self._is_editing and self._current_note_id and self.controller:
                # 直接保存，不使用定时器
                title = self.title_edit.text() if hasattr(self, 'title_edit') else ''
                content = self.content_edit.toPlainText() if hasattr(self, 'content_edit') else ''
                if title or content:
                    self.controller.update_note(self._current_note_id, {'title': title, 'content': content})
            
            self.logger.debug("笔记界面清理完成")
            
        except Exception as e:
            self.log_error(e, "笔记界面清理失败")