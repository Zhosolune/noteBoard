#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔记控制器
负责笔记相关的业务逻辑和操作协调
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import Signal, QTimer

from controllers.base_controller import BaseController, OperationResult
from models.base_model import ModelEventType


class NoteController(BaseController):
    """笔记控制器"""
    
    # 笔记相关信号
    note_created = Signal(int, str)  # 笔记ID, 标题
    note_updated = Signal(int)       # 笔记ID
    note_deleted = Signal(int, str)  # 笔记ID, 标题
    note_list_changed = Signal()     # 笔记列表变更
    note_selected = Signal(int)      # 笔记被选中
    
    # 标签相关信号
    note_tag_added = Signal(int, int)     # 笔记ID, 标签ID
    note_tag_removed = Signal(int, int)   # 笔记ID, 标签ID
    
    def __init__(self, parent=None):
        """初始化笔记控制器"""
        super().__init__(parent)
        
        self._current_note_id = None
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save_current_note)
        
        self._pending_changes = {}  # 待保存的变更
        self._auto_save_enabled = True
        self._auto_save_interval = 30000  # 30秒
    
    def init_models(self) -> None:
        """初始化模型"""
        # 模型将在主控制器中添加
        pass
    
    def init_views(self) -> None:
        """初始化视图"""
        # 视图将在相应的界面控制器中添加
        pass
    
    def init_signals(self) -> None:
        """初始化信号连接"""
        # 连接自身信号到状态更新
        self.note_created.connect(self._on_note_created)
        self.note_updated.connect(self._on_note_updated)
        self.note_deleted.connect(self._on_note_deleted)
    
    def setup_event_handlers(self) -> None:
        """设置事件处理器"""
        super().setup_event_handlers()
        
        # 注册笔记相关事件处理器
        self.register_event_handler(ModelEventType.NOTE_CREATED, self._handle_note_created)
        self.register_event_handler(ModelEventType.NOTE_UPDATED, self._handle_note_updated)
        self.register_event_handler(ModelEventType.NOTE_DELETED, self._handle_note_deleted)
        self.register_event_handler(ModelEventType.NOTE_TAG_ADDED, self._handle_note_tag_added)
        self.register_event_handler(ModelEventType.NOTE_TAG_REMOVED, self._handle_note_tag_removed)
    
    def create_note(self, title: str, content: str = "", tag_ids: Optional[List[int]] = None) -> OperationResult:
        """
        创建新笔记
        
        Args:
            title: 笔记标题
            content: 笔记内容
            tag_ids: 标签ID列表
        
        Returns:
            操作结果
        """
        try:
            self.emit_status_changed("正在创建笔记...")
            
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            # 准备笔记数据
            note_data = {
                'title': title.strip(),
                'content': content,
                'tag_ids': tag_ids or []
            }
            
            # 验证标题
            if not note_data['title']:
                return OperationResult.error_result("笔记标题不能为空")
            
            # 创建笔记
            note_id = note_model.create(note_data)
            
            if note_id:
                self.logger.info(f"创建笔记成功: ID={note_id}, 标题={title}")
                return OperationResult.success_result({
                    'note_id': note_id,
                    'title': title
                })
            else:
                return OperationResult.error_result("创建笔记失败")
                
        except Exception as e:
            self.log_error(e, "创建笔记异常")
            return OperationResult.error_result(f"创建笔记异常: {str(e)}")
    
    def update_note(self, note_id: int, data: Dict[str, Any]) -> OperationResult:
        """
        更新笔记
        
        Args:
            note_id: 笔记ID
            data: 更新数据
        
        Returns:
            操作结果
        """
        try:
            self.emit_status_changed("正在保存笔记...")
            
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            # 验证标题
            if 'title' in data and not data['title'].strip():
                return OperationResult.error_result("笔记标题不能为空")
            
            # 更新笔记
            success = note_model.update(note_id, data)
            
            if success:
                self.logger.info(f"更新笔记成功: ID={note_id}")
                return OperationResult.success_result({'note_id': note_id})
            else:
                return OperationResult.error_result("更新笔记失败")
                
        except Exception as e:
            self.log_error(e, f"更新笔记异常: ID={note_id}")
            return OperationResult.error_result(f"更新笔记异常: {str(e)}")
    
    def delete_note(self, note_id: int) -> OperationResult:
        """
        删除笔记
        
        Args:
            note_id: 笔记ID
        
        Returns:
            操作结果
        """
        try:
            self.emit_status_changed("正在删除笔记...")
            
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            # 获取笔记信息
            note = note_model.get_by_id(note_id)
            if not note:
                return OperationResult.error_result("笔记不存在")
            
            # 删除笔记
            success = note_model.delete(note_id)
            
            if success:
                self.logger.info(f"删除笔记成功: ID={note_id}, 标题={note['title']}")
                
                # 如果删除的是当前笔记，清除当前选择
                if self._current_note_id == note_id:
                    self._current_note_id = None
                
                return OperationResult.success_result({
                    'note_id': note_id,
                    'title': note['title']
                })
            else:
                return OperationResult.error_result("删除笔记失败")
                
        except Exception as e:
            self.log_error(e, f"删除笔记异常: ID={note_id}")
            return OperationResult.error_result(f"删除笔记异常: {str(e)}")
    
    def get_note(self, note_id: int) -> OperationResult:
        """
        获取笔记详情
        
        Args:
            note_id: 笔记ID
        
        Returns:
            操作结果，包含笔记数据
        """
        try:
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            note = note_model.get_by_id(note_id)
            
            if note:
                return OperationResult.success_result(note)
            else:
                return OperationResult.error_result("笔记不存在")
                
        except Exception as e:
            self.log_error(e, f"获取笔记异常: ID={note_id}")
            return OperationResult.error_result(f"获取笔记异常: {str(e)}")
    
    def get_note_list(self, filters: Optional[Dict[str, Any]] = None) -> OperationResult:
        """
        获取笔记列表
        
        Args:
            filters: 过滤条件
        
        Returns:
            操作结果，包含笔记列表
        """
        try:
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            notes = note_model.get_all(filters)
            
            return OperationResult.success_result({
                'notes': notes,
                'total_count': len(notes)
            })
                
        except Exception as e:
            self.log_error(e, "获取笔记列表异常")
            return OperationResult.error_result(f"获取笔记列表异常: {str(e)}")
    
    def search_notes(self, keyword: str, limit: int = 50) -> OperationResult:
        """
        搜索笔记
        
        Args:
            keyword: 搜索关键词
            limit: 结果限制数量
        
        Returns:
            操作结果，包含搜索结果
        """
        try:
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            if not keyword.strip():
                return self.get_note_list({'limit': limit})
            
            notes = note_model.search(keyword.strip(), limit)
            
            return OperationResult.success_result({
                'notes': notes,
                'keyword': keyword,
                'total_count': len(notes)
            })
                
        except Exception as e:
            self.log_error(e, f"搜索笔记异常: keyword={keyword}")
            return OperationResult.error_result(f"搜索笔记异常: {str(e)}")
    
    def get_notes_by_tags(self, tag_ids: List[int]) -> OperationResult:
        """
        根据标签获取笔记
        
        Args:
            tag_ids: 标签ID列表
        
        Returns:
            操作结果，包含笔记列表
        """
        try:
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            notes = note_model.get_by_tags(tag_ids)
            
            return OperationResult.success_result({
                'notes': notes,
                'tag_ids': tag_ids,
                'total_count': len(notes)
            })
                
        except Exception as e:
            self.log_error(e, f"根据标签获取笔记异常: tag_ids={tag_ids}")
            return OperationResult.error_result(f"根据标签获取笔记异常: {str(e)}")
    
    def add_tag_to_note(self, note_id: int, tag_id: int) -> OperationResult:
        """
        为笔记添加标签
        
        Args:
            note_id: 笔记ID
            tag_id: 标签ID
        
        Returns:
            操作结果
        """
        try:
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            success = note_model.add_tag_to_note(note_id, tag_id)
            
            if success:
                self.logger.info(f"为笔记添加标签成功: note_id={note_id}, tag_id={tag_id}")
                return OperationResult.success_result({
                    'note_id': note_id,
                    'tag_id': tag_id
                })
            else:
                return OperationResult.error_result("添加标签失败")
                
        except Exception as e:
            self.log_error(e, f"添加标签异常: note_id={note_id}, tag_id={tag_id}")
            return OperationResult.error_result(f"添加标签异常: {str(e)}")
    
    def remove_tag_from_note(self, note_id: int, tag_id: int) -> OperationResult:
        """
        从笔记移除标签
        
        Args:
            note_id: 笔记ID
            tag_id: 标签ID
        
        Returns:
            操作结果
        """
        try:
            note_model = self.get_model('note')
            if not note_model:
                return OperationResult.error_result("笔记模型未初始化")
            
            success = note_model.remove_tag_from_note(note_id, tag_id)
            
            if success:
                self.logger.info(f"从笔记移除标签成功: note_id={note_id}, tag_id={tag_id}")
                return OperationResult.success_result({
                    'note_id': note_id,
                    'tag_id': tag_id
                })
            else:
                return OperationResult.error_result("移除标签失败")
                
        except Exception as e:
            self.log_error(e, f"移除标签异常: note_id={note_id}, tag_id={tag_id}")
            return OperationResult.error_result(f"移除标签异常: {str(e)}")
    
    def select_note(self, note_id: int) -> None:
        """
        选择笔记
        
        Args:
            note_id: 笔记ID
        """
        if self._current_note_id != note_id:
            # 保存当前笔记的待保存变更
            if self._current_note_id and self._pending_changes:
                self._save_pending_changes()
            
            self._current_note_id = note_id
            self.note_selected.emit(note_id)
            
            self.logger.debug(f"选择笔记: ID={note_id}")
    
    def get_current_note_id(self) -> Optional[int]:
        """获取当前选中的笔记ID"""
        return self._current_note_id
    
    def schedule_auto_save(self, note_id: int, data: Dict[str, Any]) -> None:
        """
        安排自动保存
        
        Args:
            note_id: 笔记ID
            data: 变更数据
        """
        if not self._auto_save_enabled:
            return
        
        # 更新待保存的变更
        if note_id not in self._pending_changes:
            self._pending_changes[note_id] = {}
        
        self._pending_changes[note_id].update(data)
        
        # 重启自动保存定时器
        self._auto_save_timer.stop()
        self._auto_save_timer.start(self._auto_save_interval)
        
        self.logger.debug(f"安排自动保存: note_id={note_id}")
    
    def _auto_save_current_note(self) -> None:
        """自动保存当前笔记"""
        if self._pending_changes:
            self._save_pending_changes()
    
    def _save_pending_changes(self) -> None:
        """保存待保存的变更"""
        if not self._pending_changes:
            return
        
        try:
            for note_id, changes in self._pending_changes.items():
                result = self.update_note(note_id, changes)
                if result.success:
                    self.logger.debug(f"自动保存成功: note_id={note_id}")
                else:
                    self.logger.warning(f"自动保存失败: note_id={note_id}, error={result.error}")
            
            self._pending_changes.clear()
            
        except Exception as e:
            self.log_error(e, "自动保存异常")
    
    def set_auto_save_enabled(self, enabled: bool) -> None:
        """设置自动保存启用状态"""
        self._auto_save_enabled = enabled
        
        if not enabled and self._auto_save_timer.isActive():
            self._auto_save_timer.stop()
    
    def set_auto_save_interval(self, interval_ms: int) -> None:
        """设置自动保存间隔"""
        self._auto_save_interval = max(1000, interval_ms)  # 最少1秒
    
    def force_save_all(self) -> None:
        """强制保存所有待保存的变更"""
        if self._auto_save_timer.isActive():
            self._auto_save_timer.stop()
        
        self._save_pending_changes()
    
    # 事件处理器
    def _handle_note_created(self, data: Any) -> None:
        """处理笔记创建事件"""
        if isinstance(data, dict) and 'note_id' in data:
            note_id = data['note_id']
            title = data.get('title', '')
            self.note_created.emit(note_id, title)
    
    def _handle_note_updated(self, data: Any) -> None:
        """处理笔记更新事件"""
        if isinstance(data, dict) and 'note_id' in data:
            note_id = data['note_id']
            self.note_updated.emit(note_id)
    
    def _handle_note_deleted(self, data: Any) -> None:
        """处理笔记删除事件"""
        if isinstance(data, dict) and 'note_id' in data:
            note_id = data['note_id']
            title = data.get('title', '')
            self.note_deleted.emit(note_id, title)
    
    def _handle_note_tag_added(self, data: Any) -> None:
        """处理笔记标签添加事件"""
        if isinstance(data, dict) and 'note_id' in data and 'tag_id' in data:
            note_id = data['note_id']
            tag_id = data['tag_id']
            self.note_tag_added.emit(note_id, tag_id)
    
    def _handle_note_tag_removed(self, data: Any) -> None:
        """处理笔记标签移除事件"""
        if isinstance(data, dict) and 'note_id' in data and 'tag_id' in data:
            note_id = data['note_id']
            tag_id = data['tag_id']
            self.note_tag_removed.emit(note_id, tag_id)
    
    # 信号槽
    def _on_note_created(self, note_id: int, title: str) -> None:
        """笔记创建时的处理"""
        self.note_list_changed.emit()
        self.emit_status_changed(f"笔记创建成功: {title}")
    
    def _on_note_updated(self, note_id: int) -> None:
        """笔记更新时的处理"""
        self.note_list_changed.emit()
        self.emit_status_changed("笔记保存成功")
    
    def _on_note_deleted(self, note_id: int, title: str) -> None:
        """笔记删除时的处理"""
        self.note_list_changed.emit()
        self.emit_status_changed(f"笔记删除成功: {title}")
    
    def cleanup(self) -> None:
        """清理资源"""
        # 保存待保存的变更
        self.force_save_all()
        
        super().cleanup()