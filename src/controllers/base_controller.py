#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础控制器类
所有控制器的基类，提供通用的控制器功能和事件处理接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer

from utils.logger import LoggerMixin
from models.base_model import ModelEventType


class BaseController(QObject, LoggerMixin):
    """基础控制器抽象类"""
    
    # 控制器通用信号
    error_occurred = Signal(str, str)  # 错误类型, 错误消息
    operation_completed = Signal(str, dict)  # 操作类型, 操作结果
    status_changed = Signal(str)  # 状态消息
    
    def __init__(self, parent=None):
        """
        初始化基础控制器
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        
        self._models = {}  # 关联的模型字典
        self._views = {}   # 关联的视图字典
        self._event_handlers = {}  # 事件处理器字典
        self._initialized = False
    
    def add_model(self, name: str, model) -> None:
        """
        添加模型
        
        Args:
            name: 模型名称
            model: 模型实例
        """
        self._models[name] = model
        
        # 为模型添加观察者
        if hasattr(model, 'add_observer'):
            model.add_observer(self)
        
        self.logger.debug(f"添加模型: {name}")
    
    def get_model(self, name: str):
        """
        获取模型
        
        Args:
            name: 模型名称
        
        Returns:
            模型实例
        """
        return self._models.get(name)
    
    def add_view(self, name: str, view) -> None:
        """
        添加视图
        
        Args:
            name: 视图名称
            view: 视图实例
        """
        self._views[name] = view
        self.logger.debug(f"添加视图: {name}")
    
    def get_view(self, name: str):
        """
        获取视图
        
        Args:
            name: 视图名称
        
        Returns:
            视图实例
        """
        return self._views.get(name)
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        self.logger.debug(f"注册事件处理器: {event_type}")
    
    def handle_model_event(self, event_type: str, data: Any = None) -> None:
        """
        处理模型事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self.logger.debug(f"处理模型事件: {event_type}")
        
        # 调用注册的事件处理器
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                self.log_error(e, f"处理事件失败: {event_type}")
    
    def emit_error(self, error_type: str, message: str) -> None:
        """
        发出错误信号
        
        Args:
            error_type: 错误类型
            message: 错误消息
        """
        self.logger.error(f"控制器错误 [{error_type}]: {message}")
        self.error_occurred.emit(error_type, message)
    
    def emit_operation_completed(self, operation_type: str, result: Dict[str, Any]) -> None:
        """
        发出操作完成信号
        
        Args:
            operation_type: 操作类型
            result: 操作结果
        """
        self.logger.info(f"操作完成: {operation_type}")
        self.operation_completed.emit(operation_type, result)
    
    def emit_status_changed(self, message: str) -> None:
        """
        发出状态变更信号
        
        Args:
            message: 状态消息
        """
        self.status_changed.emit(message)
    
    def init_controller(self) -> None:
        """初始化控制器（直接执行）"""
        if not self._initialized:
            self._direct_init()
    
    def _direct_init(self) -> None:
        """直接初始化"""
        try:
            self.init_models()
            self.init_views()
            self.init_signals()
            self.setup_event_handlers()
            
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} 初始化完成")
            
        except Exception as e:
            self.log_error(e, "控制器初始化失败")
    
    @abstractmethod
    def init_models(self) -> None:
        """初始化模型（子类实现）"""
        pass
    
    @abstractmethod
    def init_views(self) -> None:
        """初始化视图（子类实现）"""
        pass
    
    @abstractmethod
    def init_signals(self) -> None:
        """初始化信号连接（子类实现）"""
        pass
    
    def setup_event_handlers(self) -> None:
        """设置事件处理器（子类可重写）"""
        # 注册通用事件处理器
        self.register_event_handler(ModelEventType.DATABASE_ERROR, self._handle_database_error)
    
    def _handle_database_error(self, data: Any) -> None:
        """处理数据库错误"""
        self.emit_error("database", "数据库操作失败")
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 从模型移除观察者
            for model in self._models.values():
                if hasattr(model, 'remove_observer'):
                    model.remove_observer(self)
            
            # 清理引用
            self._models.clear()
            self._views.clear()
            self._event_handlers.clear()
            
            self.logger.debug(f"{self.__class__.__name__} 清理完成")
            
        except Exception as e:
            self.log_error(e, "控制器清理失败")


class ControllerManager(QObject, LoggerMixin):
    """控制器管理器"""
    
    def __init__(self, parent=None):
        """初始化控制器管理器"""
        super().__init__(parent)
        self._controllers = {}
        self._controller_dependencies = {}
    
    def register_controller(self, name: str, controller: BaseController, dependencies: Optional[List[str]] = None) -> None:
        """
        注册控制器
        
        Args:
            name: 控制器名称
            controller: 控制器实例
            dependencies: 依赖的控制器列表
        """
        self._controllers[name] = controller
        self._controller_dependencies[name] = dependencies or []
        
        self.logger.debug(f"注册控制器: {name}")
    
    def get_controller(self, name: str) -> Optional[BaseController]:
        """
        获取控制器
        
        Args:
            name: 控制器名称
        
        Returns:
            控制器实例
        """
        return self._controllers.get(name)
    
    def init_all_controllers(self) -> None:
        """按依赖顺序初始化所有控制器"""
        initialized = set()
        
        def init_controller(name: str):
            if name in initialized or name not in self._controllers:
                return
            
            # 先初始化依赖
            for dep in self._controller_dependencies.get(name, []):
                init_controller(dep)
            
            # 初始化当前控制器
            controller = self._controllers[name]
            controller.init_controller()
            initialized.add(name)
            
            self.logger.info(f"控制器已初始化: {name}")
        
        # 初始化所有控制器
        for name in self._controllers:
            init_controller(name)
        
        self.logger.info(f"所有控制器初始化完成: {len(initialized)}个")
    
    def cleanup_all_controllers(self) -> None:
        """清理所有控制器"""
        # 使用list()复制字典的items，避免在迭代过程中修改字典
        controllers_to_cleanup = list(self._controllers.items())
        
        for name, controller in controllers_to_cleanup:
            try:
                controller.cleanup()
                self.logger.debug(f"控制器已清理: {name}")
            except Exception as e:
                self.logger.error(f"清理控制器失败 {name}: {e}")
        
        # 清空字典
        self._controllers.clear()
        self._controller_dependencies.clear()


class EventBus(QObject):
    """事件总线 - 用于控制器间通信"""
    
    # 全局事件信号
    global_event = Signal(str, object)  # 事件类型, 事件数据
    
    def __init__(self, parent=None):
        """初始化事件总线"""
        super().__init__(parent)
        self._subscribers = {}  # 事件订阅者
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def emit_event(self, event_type: str, data: Any = None) -> None:
        """
        发出事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        # 发出全局信号
        self.global_event.emit(event_type, data)
        
        # 调用订阅者回调
        subscribers = self._subscribers.get(event_type, [])
        for callback in subscribers:
            try:
                callback(data)
            except Exception as e:
                print(f"事件回调执行失败 {event_type}: {e}")


# 全局事件总线实例
global_event_bus = EventBus()


class AsyncOperation(QObject):
    """异步操作基类"""
    
    # 操作信号
    started = Signal()
    progress = Signal(int)  # 进度百分比
    completed = Signal(object)  # 操作结果
    error = Signal(str)  # 错误信息
    
    def __init__(self, parent=None):
        """初始化异步操作"""
        super().__init__(parent)
        self._cancelled = False
    
    def cancel(self) -> None:
        """取消操作"""
        self._cancelled = True
    
    @property
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._cancelled
    
    @abstractmethod
    def execute(self) -> Any:
        """执行操作（子类实现）"""
        pass


class OperationResult:
    """操作结果类"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None):
        """
        初始化操作结果
        
        Args:
            success: 操作是否成功
            data: 结果数据
            error: 错误信息
        """
        self.success = success
        self.data = data
        self.error = error
    
    @classmethod
    def success_result(cls, data: Any = None) -> 'OperationResult':
        """创建成功结果"""
        return cls(True, data)
    
    @classmethod
    def error_result(cls, error: str) -> 'OperationResult':
        """创建错误结果"""
        return cls(False, error=error)
    
    def __bool__(self) -> bool:
        """返回操作是否成功"""
        return self.success