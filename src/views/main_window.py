#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口
基于PyQt-Fluent-Widgets的FluentWindow实现现代化主界面
"""

from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF,
    setTheme, Theme, isDarkTheme, qconfig, InfoBar, InfoBarPosition,
    SystemTrayIcon, RoundMenu, Action, MessageBox
)

from utils.logger import LoggerMixin
from views.home_interface import HomeInterface
from views.note_interface import NoteInterface  
from views.tag_interface import TagInterface
from views.search_interface import SearchInterface
from views.settings_interface import SettingsInterface


class MainWindow(FluentWindow, LoggerMixin):
    """主窗口类"""
    
    # 窗口信号
    window_closing = Signal()
    window_state_changed = Signal(str)  # 窗口状态变化
    theme_changed = Signal(str)  # 主题变化
    
    def __init__(self, config_manager=None, parent=None):
        """
        初始化主窗口
        
        Args:
            config_manager: 配置管理器
            parent: 父对象
        """
        super().__init__(parent)
        
        self.config = config_manager
        self._interfaces = {}  # 界面实例字典
        self._controllers = {}  # 控制器字典
        self._current_interface = None
        
        # 系统托盘
        self.tray_icon = None
        self.tray_menu = None
        
        # 窗口状态
        self._is_pinned = False  # 是否置顶
        self._is_edge_hidden = False  # 是否边缘隐藏
        
        # 初始化界面
        self._init_window()
        self._init_interfaces()
        self._init_navigation()
        self._init_system_tray()
        self._load_window_settings()
        
        self.logger.info("主窗口初始化完成")
    
    def _init_window(self) -> None:
        """初始化窗口基础设置"""
        # 设置窗口标题和图标
        self.setWindowTitle("轻量笔记管理器")
        
        # 设置窗口大小和位置
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        # 设置窗口图标（如果存在）
        try:
            self.setWindowIcon(QIcon("resources/icons/app_icon.ico"))
        except:
            pass  # 图标文件不存在时忽略
        
        # 设置窗口属性
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        # 启用窗口阴影效果
        self.setStyleSheet("""
            MainWindow {
                background-color: transparent;
            }
        """)
    
    def _init_interfaces(self) -> None:
        """初始化所有子界面"""
        # 创建各个子界面实例
        self._interfaces['home'] = HomeInterface(self)
        self._interfaces['note'] = NoteInterface(self)
        self._interfaces['tag'] = TagInterface(self)
        self._interfaces['search'] = SearchInterface(self)
        self._interfaces['settings'] = SettingsInterface(self)
        
        self.logger.debug("所有子界面创建完成")
    
    def _init_navigation(self) -> None:
        """初始化导航菜单 - 采用官方推荐方式"""
        # 主要功能页面 - 放在顶部
        self.addSubInterface(
            self._interfaces['home'], 
            FIF.HOME, 
            "首页",
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self._interfaces['note'], 
            FIF.EDIT, 
            "笔记管理",
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self._interfaces['tag'], 
            FIF.TAG, 
            "标签管理",
            NavigationItemPosition.TOP
        )
        
        # 搜索功能 - 放在滚动区域
        self.addSubInterface(
            self._interfaces['search'],
            FIF.SEARCH,
            "搜索",
            NavigationItemPosition.SCROLL
        )
        
        # 设置页面 - 放在底部
        self.addSubInterface(
            self._interfaces['settings'],
            FIF.SETTING,
            "设置",
            NavigationItemPosition.BOTTOM
        )
        
        # 设置默认页面为首页
        self.navigationInterface.setDefaultRouteKey(
            self._interfaces['home'].objectName()
        )
        
        # 连接导航切换信号
        self.navigationInterface.displayModeChanged.connect(
            self._on_navigation_display_mode_changed
        )
        
        self.logger.debug("导航菜单初始化完成")
    
    def _init_system_tray(self) -> None:
        """初始化系统托盘"""
        try:
            # 创建托盘图标
            self.tray_icon = SystemTrayIcon(self)
            
            # 设置托盘图标
            try:
                self.tray_icon.setIcon(QIcon("resources/icons/tray_icon.ico"))
            except:
                # 使用默认图标
                self.tray_icon.setIcon(self.windowIcon())
            
            self.tray_icon.setToolTip("轻量笔记管理器")
            
            # 创建托盘菜单
            self.tray_menu = RoundMenu(parent=self)
            
            # 添加菜单项
            show_action = Action(FIF.VIEW, "显示主窗口")
            show_action.triggered.connect(self.show_window)
            self.tray_menu.addAction(show_action)
            
            hide_action = Action(FIF.HIDE, "隐藏到托盘")
            hide_action.triggered.connect(self.hide_to_tray)
            self.tray_menu.addAction(hide_action)
            
            self.tray_menu.addSeparator()
            
            pin_action = Action(FIF.PIN, "窗口置顶")
            pin_action.setCheckable(True)
            pin_action.triggered.connect(self.toggle_always_on_top)
            self.tray_menu.addAction(pin_action)
            
            self.tray_menu.addSeparator()
            
            exit_action = Action(FIF.CLOSE, "退出程序")
            exit_action.triggered.connect(self.close_application)
            self.tray_menu.addAction(exit_action)
            
            # 设置托盘菜单
            self.tray_icon.setContextMenu(self.tray_menu)
            
            # 连接托盘图标信号
            self.tray_icon.activated.connect(self._on_tray_icon_activated)
            
            # 显示托盘图标
            if QApplication.instance().arguments().count("--start-minimized") == 0:
                self.tray_icon.show()
            
            self.logger.debug("系统托盘初始化完成")
            
        except Exception as e:
            self.log_error(e, "初始化系统托盘失败")
    
    def _load_window_settings(self) -> None:
        """加载窗口设置"""
        if not self.config:
            return
        
        try:
            # 加载窗口大小和位置
            width = self.config.getint('window', 'width', 1200)
            height = self.config.getint('window', 'height', 800)
            x = self.config.getint('window', 'x', -1)
            y = self.config.getint('window', 'y', -1)
            
            self.resize(width, height)
            
            # 如果位置有效，设置窗口位置
            if x >= 0 and y >= 0:
                self.move(x, y)
            else:
                # 居中显示
                self.center_window()
            
            # 加载最大化状态
            maximized = self.config.getboolean('window', 'maximized', False)
            if maximized:
                self.showMaximized()
            
            # 加载置顶状态
            always_on_top = self.config.getboolean('window', 'always_on_top', False)
            if always_on_top:
                self.set_always_on_top(True)
            
            # 加载主题设置
            theme_name = self.config.get('ui', 'theme', 'auto')
            self.apply_theme(theme_name)
            
            self.logger.debug("窗口设置加载完成")
            
        except Exception as e:
            self.log_error(e, "加载窗口设置失败")
    
    def _save_window_settings(self) -> None:
        """保存窗口设置"""
        if not self.config:
            return
        
        try:
            # 保存窗口大小和位置
            if not self.isMaximized():
                self.config.set('window', 'width', self.width())
                self.config.set('window', 'height', self.height())
                self.config.set('window', 'x', self.x())
                self.config.set('window', 'y', self.y())
            
            # 保存最大化状态
            self.config.set('window', 'maximized', self.isMaximized())
            
            # 保存置顶状态
            self.config.set('window', 'always_on_top', self._is_pinned)
            
            # 保存配置
            self.config.save_config()
            
            self.logger.debug("窗口设置保存完成")
            
        except Exception as e:
            self.log_error(e, "保存窗口设置失败")
    
    def center_window(self) -> None:
        """居中显示窗口"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            
            # 计算居中位置
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            
            self.move(x, y)
    
    def apply_theme(self, theme_name: str) -> None:
        """
        应用主题
        
        Args:
            theme_name: 主题名称 (auto, light, dark)
        """
        try:
            if theme_name.lower() == 'dark':
                setTheme(Theme.DARK)
            elif theme_name.lower() == 'light':
                setTheme(Theme.LIGHT)
            else:
                setTheme(Theme.AUTO)
            
            self.theme_changed.emit(theme_name)
            self.logger.debug(f"应用主题: {theme_name}")
            
        except Exception as e:
            self.log_error(e, f"应用主题失败: {theme_name}")
    
    def set_controller(self, name: str, controller) -> None:
        """
        设置控制器
        
        Args:
            name: 控制器名称
            controller: 控制器实例
        """
        self._controllers[name] = controller
        
        # 将控制器传递给相应的界面
        if name in self._interfaces:
            interface = self._interfaces[name]
            if hasattr(interface, 'set_controller'):
                interface.set_controller(controller)
    
    def get_interface(self, name: str):
        """
        获取界面实例
        
        Args:
            name: 界面名称
        
        Returns:
            界面实例
        """
        return self._interfaces.get(name)
    
    def get_controller(self, name: str):
        """
        获取控制器实例
        
        Args:
            name: 控制器名称
        
        Returns:
            控制器实例
        """
        return self._controllers.get(name)
    
    def show_window(self) -> None:
        """显示主窗口"""
        if self.isMinimized():
            self.showNormal()
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        self.window_state_changed.emit("shown")
        self.logger.debug("显示主窗口")
    
    def hide_to_tray(self) -> None:
        """隐藏到系统托盘"""
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            self.show_info_message("程序已隐藏到系统托盘")
            self.window_state_changed.emit("hidden")
            self.logger.debug("隐藏到系统托盘")
        else:
            self.showMinimized()
    
    def toggle_always_on_top(self) -> None:
        """切换窗口置顶状态"""
        self.set_always_on_top(not self._is_pinned)
    
    def set_always_on_top(self, pinned: bool) -> None:
        """
        设置窗口置顶
        
        Args:
            pinned: 是否置顶
        """
        self._is_pinned = pinned
        
        # 更新窗口标志
        flags = self.windowFlags()
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        
        # 保存当前状态
        was_visible = self.isVisible()
        geometry = self.geometry()
        
        # 应用新标志
        self.setWindowFlags(flags)
        
        # 恢复窗口状态
        if was_visible:
            self.setGeometry(geometry)
            self.show()
        
        # 更新托盘菜单
        if self.tray_menu:
            pin_action = None
            for action in self.tray_menu.actions():
                if action.text() == "窗口置顶":
                    pin_action = action
                    break
            
            if pin_action:
                pin_action.setChecked(pinned)
        
        self.window_state_changed.emit("pinned" if pinned else "unpinned")
        self.logger.debug(f"窗口置顶状态: {pinned}")
    
    def show_info_message(self, message: str, title: str = "提示", duration: int = 3000) -> None:
        """
        显示信息提示
        
        Args:
            message: 消息内容
            title: 标题
            duration: 显示时长（毫秒）
        """
        InfoBar.success(
            title=title,
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self
        )
    
    def show_error_message(self, message: str, title: str = "错误") -> None:
        """
        显示错误提示
        
        Args:
            message: 错误消息
            title: 标题
        """
        InfoBar.error(
            title=title,
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )
    
    def close_application(self) -> None:
        """关闭应用程序"""
        # 显示确认对话框
        msg_box = MessageBox(
            "退出确认",
            "确定要退出轻量笔记管理器吗？",
            self
        )
        
        if msg_box.exec():
            self.window_closing.emit()
            QApplication.instance().quit()
    
    def switch_to_interface(self, interface_name: str) -> None:
        """
        切换到指定界面
        
        Args:
            interface_name: 界面名称
        """
        if interface_name in self._interfaces:
            interface = self._interfaces[interface_name]
            self.navigationInterface.setCurrentItem(interface.objectName())
            self._current_interface = interface_name
            self.logger.debug(f"切换到界面: {interface_name}")
    
    # 事件处理器
    def _on_tray_icon_activated(self, reason) -> None:
        """托盘图标激活事件处理"""
        if reason == SystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_window()
    
    def _on_navigation_display_mode_changed(self) -> None:
        """导航显示模式变化处理"""
        self.logger.debug("导航显示模式已变化")
    
    # Qt事件重写
    def closeEvent(self, event) -> None:
        """窗口关闭事件"""
        # 保存窗口设置
        self._save_window_settings()
        
        # 如果有系统托盘，隐藏到托盘而不是关闭
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide_to_tray()
        else:
            # 发出关闭信号
            self.window_closing.emit()
            event.accept()
    
    def changeEvent(self, event) -> None:
        """窗口状态变化事件"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.tray_icon and self.tray_icon.isVisible():
                # 最小化时隐藏到托盘
                self.hide()
                event.ignore()
                return
        
        super().changeEvent(event)
    
    def resizeEvent(self, event) -> None:
        """窗口大小调整事件"""
        super().resizeEvent(event)
        # 可以在这里添加响应式布局调整逻辑
    
    def moveEvent(self, event) -> None:
        """窗口移动事件"""
        super().moveEvent(event)
        # 可以在这里添加边缘检测逻辑
    
    def showEvent(self, event) -> None:
        """窗口显示事件"""
        super().showEvent(event)
        self.window_state_changed.emit("shown")
    
    def hideEvent(self, event) -> None:
        """窗口隐藏事件"""
        super().hideEvent(event)
        self.window_state_changed.emit("hidden")