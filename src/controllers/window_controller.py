#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口控制器
实现边缘隐藏、鼠标唤起、窗口置顶等功能
"""

from typing import Optional
from PySide6.QtCore import QTimer, QPoint, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCursor

try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

from controllers.base_controller import BaseController, OperationResult
from utils.logger import LoggerMixin


class WindowController(BaseController):
    """窗口控制器"""
    
    # 窗口状态信号
    window_shown = Signal()
    window_hidden = Signal()
    edge_triggered = Signal()
    
    def __init__(self, main_window, parent=None):
        """初始化窗口控制器"""
        super().__init__(parent)
        
        self.main_window = main_window
        self._edge_hidden = False
        self._mouse_listener = None
        
        # 边缘检测设置
        self._edge_trigger_width = 5
        self._peek_width = 300  
        self._hide_delay = 2000
        
        # 定时器
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide_window)
        
        self._edge_check_timer = QTimer()
        self._edge_check_timer.timeout.connect(self._check_mouse_position)
    
    def init_models(self):
        """初始化模型"""
        pass
    
    def init_views(self):
        """初始化视图"""
        pass
    
    def init_signals(self):
        """初始化信号连接"""
        if self.main_window:
            self.main_window.window_state_changed.connect(self._on_window_state_changed)
    
    def enable_edge_hiding(self, enabled: bool = True) -> OperationResult:
        """
        启用/禁用边缘隐藏功能
        
        Args:
            enabled: 是否启用
            
        Returns:
            操作结果
        """
        try:
            if enabled:
                if PYNPUT_AVAILABLE:
                    self._start_mouse_monitoring()
                else:
                    # 使用Qt定时器方式
                    self._edge_check_timer.start(100)
                
                self.logger.info("边缘隐藏功能已启用")
            else:
                self._stop_mouse_monitoring()
                self._edge_check_timer.stop()
                self.logger.info("边缘隐藏功能已禁用")
            
            return OperationResult.success_result({'enabled': enabled})
            
        except Exception as e:
            self.log_error(e, "设置边缘隐藏功能失败")
            return OperationResult.error_result(f"设置边缘隐藏功能失败: {str(e)}")
    
    def _start_mouse_monitoring(self):
        """开始鼠标监控"""
        if not PYNPUT_AVAILABLE:
            return
        
        try:
            if self._mouse_listener:
                self._mouse_listener.stop()
            
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click
            )
            self._mouse_listener.start()
            
        except Exception as e:
            self.log_error(e, "启动鼠标监控失败")
    
    def _stop_mouse_monitoring(self):
        """停止鼠标监控"""
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
    
    def _on_mouse_move(self, x: int, y: int):
        """鼠标移动事件处理"""
        try:
            screen = QApplication.primaryScreen()
            if not screen:
                return
            
            screen_geometry = screen.geometry()
            
            # 检查是否在屏幕边缘
            at_edge = (
                x <= self._edge_trigger_width or  # 左边缘
                x >= screen_geometry.width() - self._edge_trigger_width or  # 右边缘
                y <= self._edge_trigger_width or  # 上边缘
                y >= screen_geometry.height() - self._edge_trigger_width  # 下边缘
            )
            
            if at_edge and not self.main_window.isVisible():
                self._show_peek_window()
                self.edge_triggered.emit()
            
            # 检查鼠标是否在窗口内
            if self.main_window.isVisible():
                window_geometry = self.main_window.geometry()
                mouse_in_window = window_geometry.contains(x, y)
                
                if not mouse_in_window and not self._hide_timer.isActive():
                    # 启动隐藏延时
                    self._hide_timer.start(self._hide_delay)
                elif mouse_in_window and self._hide_timer.isActive():
                    # 鼠标回到窗口内，取消隐藏
                    self._hide_timer.stop()
                    
        except Exception as e:
            self.log_error(e, "处理鼠标移动事件失败")
    
    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
        """鼠标点击事件处理"""
        if pressed and self.main_window.isVisible():
            window_geometry = self.main_window.geometry()
            if window_geometry.contains(x, y):
                # 点击窗口内，展开完整窗口
                self._show_full_window()
    
    def _check_mouse_position(self):
        """检查鼠标位置（Qt定时器方式）"""
        try:
            cursor_pos = QCursor.pos()
            screen = QApplication.primaryScreen()
            if not screen:
                return
            
            screen_geometry = screen.geometry()
            
            # 检查边缘触发
            at_edge = (
                cursor_pos.x() <= self._edge_trigger_width or
                cursor_pos.x() >= screen_geometry.width() - self._edge_trigger_width
            )
            
            if at_edge and not self.main_window.isVisible():
                self._show_peek_window()
                
        except Exception as e:
            self.log_error(e, "检查鼠标位置失败")
    
    def _show_peek_window(self):
        """显示预览窗口"""
        try:
            if self._edge_hidden:
                return
            
            # 设置窗口为预览模式
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                
                # 设置预览窗口大小和位置
                self.main_window.setFixedWidth(self._peek_width)
                self.main_window.move(0, 0)
                self.main_window.setFixedHeight(screen_geometry.height())
                
            self.main_window.show()
            self.main_window.setWindowOpacity(0.9)
            
            self.window_shown.emit()
            
        except Exception as e:
            self.log_error(e, "显示预览窗口失败")
    
    def _show_full_window(self):
        """显示完整窗口"""
        try:
            # 恢复窗口正常大小
            self.main_window.setFixedSize(16777215, 16777215)  # 取消固定大小
            self.main_window.resize(1200, 800)
            self.main_window.center_window()
            self.main_window.setWindowOpacity(1.0)
            
            self.window_shown.emit()
            
        except Exception as e:
            self.log_error(e, "显示完整窗口失败")
    
    def _hide_window(self):
        """隐藏窗口到边缘"""
        try:
            if not self.main_window.isVisible():
                return
            
            # 隐藏到边缘
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                
                # 移动到屏幕左边缘
                self.main_window.setFixedWidth(self._edge_trigger_width)
                self.main_window.move(-self._edge_trigger_width + 2, 0)
                self.main_window.setFixedHeight(screen_geometry.height())
                self.main_window.setWindowOpacity(0.1)
            
            self._edge_hidden = True
            self.window_hidden.emit()
            
        except Exception as e:
            self.log_error(e, "隐藏窗口失败")
    
    def set_always_on_top(self, enabled: bool) -> OperationResult:
        """
        设置窗口置顶
        
        Args:
            enabled: 是否置顶
            
        Returns:
            操作结果
        """
        try:
            if self.main_window:
                self.main_window.set_always_on_top(enabled)
                return OperationResult.success_result({'pinned': enabled})
            else:
                return OperationResult.error_result("主窗口未初始化")
                
        except Exception as e:
            self.log_error(e, f"设置窗口置顶失败: {enabled}")
            return OperationResult.error_result(f"设置窗口置顶失败: {str(e)}")
    
    def toggle_window_visibility(self) -> OperationResult:
        """切换窗口显示状态"""
        try:
            if self.main_window.isVisible():
                self._hide_window()
            else:
                self._show_full_window()
            
            return OperationResult.success_result({
                'visible': self.main_window.isVisible()
            })
            
        except Exception as e:
            self.log_error(e, "切换窗口显示状态失败")
            return OperationResult.error_result(f"切换窗口显示状态失败: {str(e)}")
    
    def set_edge_trigger_width(self, width: int):
        """设置边缘触发宽度"""
        self._edge_trigger_width = max(1, min(width, 20))  # 限制在1-20像素
    
    def set_peek_width(self, width: int):
        """设置预览宽度"""
        self._peek_width = max(200, min(width, 500))  # 限制在200-500像素
    
    def set_hide_delay(self, delay_ms: int):
        """设置隐藏延时"""
        self._hide_delay = max(500, min(delay_ms, 10000))  # 限制在0.5-10秒
    
    def _on_window_state_changed(self, state: str):
        """窗口状态变化处理"""
        if state == "shown":
            self._edge_hidden = False
            if self._hide_timer.isActive():
                self._hide_timer.stop()
        elif state == "hidden":
            self._edge_hidden = True
    
    def cleanup(self):
        """清理资源"""
        self._stop_mouse_monitoring()
        if self._hide_timer.isActive():
            self._hide_timer.stop()
        if self._edge_check_timer.isActive():
            self._edge_check_timer.stop()
        
        super().cleanup()