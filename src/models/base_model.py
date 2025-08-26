#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础模型类
所有数据模型的基类，提供通用的数据库操作接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from utils.logger import LoggerMixin


class BaseModel(ABC, LoggerMixin):
    """基础模型抽象类"""
    
    def __init__(self, db_manager):
        """
        初始化基础模型
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
        self._observers = []  # 观察者列表
    
    def add_observer(self, observer):
        """添加观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
            self.logger.debug(f"添加观察者: {observer}")
    
    def remove_observer(self, observer):
        """移除观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
            self.logger.debug(f"移除观察者: {observer}")
    
    def notify_observers(self, event_type: str, data: Any = None):
        """通知所有观察者"""
        self.logger.debug(f"通知观察者事件: {event_type}")
        for observer in self._observers:
            try:
                observer.handle_model_event(event_type, data)
            except Exception as e:
                self.logger.error(f"通知观察者失败: {e}")
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """
        创建新记录
        
        Args:
            data: 记录数据
        
        Returns:
            新记录的ID，失败返回None
        """
        pass
    
    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取记录
        
        Args:
            record_id: 记录ID
        
        Returns:
            记录数据字典，不存在返回None
        """
        pass
    
    @abstractmethod
    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        更新记录
        
        Args:
            record_id: 记录ID
            data: 更新数据
        
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """
        删除记录
        
        Args:
            record_id: 记录ID
        
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取所有记录
        
        Args:
            filters: 过滤条件
        
        Returns:
            记录列表
        """
        pass
    
    def validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 要验证的数据
            required_fields: 必需字段列表
        
        Returns:
            验证是否通过
        """
        for field in required_fields:
            if field not in data or data[field] is None:
                self.logger.warning(f"缺少必需字段: {field}")
                return False
        return True
    
    def format_datetime(self, dt: Union[datetime, str, None]) -> Optional[str]:
        """
        格式化日期时间
        
        Args:
            dt: 日期时间对象或字符串
        
        Returns:
            格式化后的日期时间字符串
        """
        if dt is None:
            return None
        
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(dt, str):
            return dt
        else:
            return str(dt)
    
    def parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """
        解析日期时间字符串
        
        Args:
            dt_str: 日期时间字符串
        
        Returns:
            datetime对象
        """
        if dt_str is None:
            return None
        
        try:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # 尝试其他格式
                return datetime.fromisoformat(dt_str)
            except ValueError:
                self.logger.warning(f"无法解析日期时间: {dt_str}")
                return None
    
    def get_current_timestamp(self) -> str:
        """获取当前时间戳字符串"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class ModelEventType:
    """模型事件类型常量"""
    
    # 记录操作事件
    RECORD_CREATED = "record_created"
    RECORD_UPDATED = "record_updated"
    RECORD_DELETED = "record_deleted"
    
    # 笔记特定事件
    NOTE_CREATED = "note_created"
    NOTE_UPDATED = "note_updated"
    NOTE_DELETED = "note_deleted"
    NOTE_TAG_ADDED = "note_tag_added"
    NOTE_TAG_REMOVED = "note_tag_removed"
    
    # 标签特定事件
    TAG_CREATED = "tag_created"
    TAG_UPDATED = "tag_updated"
    TAG_DELETED = "tag_deleted"
    
    # 数据库事件
    DATABASE_ERROR = "database_error"
    DATABASE_CONNECTED = "database_connected"
    DATABASE_DISCONNECTED = "database_disconnected"