#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主控制器
整合所有控制器，实现应用程序的整体协调
"""

import sys
from typing import Optional, Dict, Any
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from controllers.base_controller import BaseController, ControllerManager, OperationResult
from controllers.note_controller import NoteController
from controllers.tag_controller import TagController
from controllers.window_controller import WindowController

from models.database_model import DatabaseManager
from models.note_model import NoteModel
from models.tag_model import TagModel
from models.settings_model import SettingsModel

from views.main_window import MainWindow


class MainController(BaseController):
    """主控制器"""
    
    def __init__(self, app: QApplication, config_manager, logger, parent=None):
        """
        初始化主控制器
        
        Args:
            app: Qt应用程序实例
            config_manager: 配置管理器
            logger: 日志记录器
        """
        super().__init__(parent)
        
        self.app = app
        self.config = config_manager
        
        # 核心组件
        self.db_manager = None
        self.main_window = None
        
        # 模型实例
        self.note_model = None
        self.tag_model = None
        self.settings_model = None
        
        # 控制器管理器
        self.controller_manager = ControllerManager()
        
        # 清理状态标志，防止递归调用
        self._is_cleaning_up = False
        
        # 子控制器
        self.note_controller = None
        self.tag_controller = None
        self.window_controller = None
        
        self.logger.info("主控制器初始化完成")
    
    def init_models(self) -> None:
        """初始化数据模型"""
        try:
            # 初始化数据库管理器
            db_path = self.config.get('database', 'db_name', 'notes.db')
            self.db_manager = DatabaseManager(db_path)
            self.db_manager.initialize_database()
            
            # 初始化模型
            self.note_model = NoteModel(self.db_manager)
            self.tag_model = TagModel(self.db_manager)
            self.settings_model = SettingsModel(self.db_manager)
            
            # 加载默认设置
            if self.settings_model.is_first_run():
                self.settings_model.load_default_settings()
                self.settings_model.mark_first_run_complete()
            
            self.logger.info("数据模型初始化完成")
            
        except Exception as e:
            self.log_error(e, "初始化数据模型失败")
            raise
    
    def init_views(self) -> None:
        """初始化视图"""
        try:
            # 创建主窗口
            self.main_window = MainWindow(self.config)
            
            # 连接主窗口信号
            self.main_window.window_closing.connect(self._on_application_closing)
            
            self.logger.info("视图初始化完成")
            
        except Exception as e:
            self.log_error(e, "初始化视图失败")
            raise
    
    def init_signals(self) -> None:
        """初始化信号连接"""
        # 连接应用程序退出信号
        self.app.aboutToQuit.connect(self.cleanup)
    
    def init_application(self) -> None:
        """初始化应用程序"""
        try:
            # 按顺序初始化各个组件
            self.init_models()
            self.init_views()
            self._init_controllers()
            self.init_signals()
            
            # 初始化控制器管理器
            self.controller_manager.init_all_controllers()
            
            self.logger.info("应用程序初始化完成")
            
        except Exception as e:
            self.log_error(e, "初始化应用程序失败")
            raise
    
    def _init_controllers(self) -> None:
        """初始化所有控制器"""
        try:
            # 创建子控制器
            self.note_controller = NoteController()
            self.tag_controller = TagController()
            self.window_controller = WindowController(self.main_window)
            
            # 注册子控制器到控制器管理器（不包括MainController自己）
            # 注意：不再注册MainController，避免递归调用
            self.controller_manager.register_controller('note', self.note_controller, [])
            self.controller_manager.register_controller('tag', self.tag_controller, [])
            self.controller_manager.register_controller('window', self.window_controller, [])
            
            # 为控制器添加模型
            self.note_controller.add_model('note', self.note_model)
            self.note_controller.add_model('tag', self.tag_model)
            
            self.tag_controller.add_model('tag', self.tag_model)
            self.tag_controller.add_model('note', self.note_model)
            
            # 为主窗口设置控制器
            self.main_window.set_controller('note', self.note_controller)
            self.main_window.set_controller('tag', self.tag_controller)
            self.main_window.set_controller('window', self.window_controller)
            
            # 连接控制器间的信号
            self._connect_controller_signals()
            
            self.logger.info("控制器初始化完成")
            
        except Exception as e:
            self.log_error(e, "初始化控制器失败")
            raise
    
    def _connect_controller_signals(self) -> None:
        """连接控制器间的信号"""
        try:
            # 笔记控制器信号连接
            if self.note_controller:
                self.note_controller.error_occurred.connect(self._handle_controller_error)
                self.note_controller.operation_completed.connect(self._handle_operation_completed)
            
            # 标签控制器信号连接
            if self.tag_controller:
                self.tag_controller.error_occurred.connect(self._handle_controller_error)
                self.tag_controller.operation_completed.connect(self._handle_operation_completed)
            
            # 窗口控制器信号连接
            if self.window_controller:
                self.window_controller.error_occurred.connect(self._handle_controller_error)
            
            self.logger.debug("控制器信号连接完成")
            
        except Exception as e:
            self.log_error(e, "连接控制器信号失败")
    
    def show_main_window(self) -> None:
        """显示主窗口"""
        try:
            if self.main_window:
                # 禁用边缘隐藏功能，直接显示窗口
                self.main_window.show_window()
                self.logger.info("主窗口已准备就绪")
            
        except Exception as e:
            self.log_error(e, "显示主窗口失败")
    
    def get_application_info(self) -> Dict[str, Any]:
        """获取应用程序信息"""
        try:
            info = {
                'app_name': self.config.get('app', 'name', '轻量笔记管理器'),
                'version': self.config.get('app', 'version', '1.0.0'),
                'author': self.config.get('app', 'author', 'Kiro'),
                'database_info': self.db_manager.get_database_info() if self.db_manager else {},
                'notes_count': self.note_model.get_notes_count() if self.note_model else 0,
                'tags_count': self.tag_model.get_tags_count() if self.tag_model else 0,
            }
            
            return info
            
        except Exception as e:
            self.log_error(e, "获取应用程序信息失败")
            return {}
    
    def backup_data(self) -> OperationResult:
        """备份数据"""
        try:
            if not self.db_manager:
                return OperationResult.error_result("数据库管理器未初始化")
            
            from datetime import datetime
            backup_filename = f"notes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            success = self.db_manager.backup_database(backup_filename)
            
            if success:
                self.logger.info(f"数据备份成功: {backup_filename}")
                return OperationResult.success_result({
                    'backup_file': backup_filename,
                    'backup_time': datetime.now().isoformat()
                })
            else:
                return OperationResult.error_result("数据备份失败")
                
        except Exception as e:
            self.log_error(e, "备份数据异常")
            return OperationResult.error_result(f"备份数据异常: {str(e)}")
    
    def import_data(self, file_path: str) -> OperationResult:
        """导入数据"""
        try:
            # TODO: 实现数据导入功能
            self.logger.info(f"导入数据: {file_path}")
            return OperationResult.success_result({'imported': True})
            
        except Exception as e:
            self.log_error(e, f"导入数据失败: {file_path}")
            return OperationResult.error_result(f"导入数据失败: {str(e)}")
    
    def export_data(self, file_path: str, format_type: str = 'json') -> OperationResult:
        """导出数据"""
        try:
            # TODO: 实现数据导出功能
            self.logger.info(f"导出数据: {file_path}, 格式: {format_type}")
            return OperationResult.success_result({'exported': True})
            
        except Exception as e:
            self.log_error(e, f"导出数据失败: {file_path}")
            return OperationResult.error_result(f"导出数据失败: {str(e)}")
    
    def get_statistics(self) -> OperationResult:
        """获取统计信息"""
        try:
            stats = {}
            
            # 笔记统计
            if self.note_model:
                stats['notes_count'] = self.note_model.get_notes_count()
                recent_notes = self.note_model.get_recent_notes(5)
                stats['recent_notes'] = recent_notes
            
            # 标签统计
            if self.tag_controller:
                tag_stats_result = self.tag_controller.get_tags_statistics()
                if tag_stats_result.success:
                    stats['tags_stats'] = tag_stats_result.data
            
            # 数据库统计
            if self.db_manager:
                stats['database_info'] = self.db_manager.get_database_info()
            
            return OperationResult.success_result(stats)
            
        except Exception as e:
            self.log_error(e, "获取统计信息失败")
            return OperationResult.error_result(f"获取统计信息失败: {str(e)}")
    
    def cleanup(self) -> None:
        """清理资源（强制退出模式）"""
        # 防止重复调用
        if hasattr(self, '_is_cleaning_up') and self._is_cleaning_up:
            self.logger.debug("正在清理中，跳过重复调用")
            return
            
        self._is_cleaning_up = True
        
        try:
            self.logger.info("开始强制清理应用程序资源")
            
            # 尝试清理子控制器，但不让失败阻止退出
            try:
                if hasattr(self, 'controller_manager') and self.controller_manager:
                    self.controller_manager.cleanup_all_controllers()
            except Exception as e:
                self.logger.error(f"清理控制器失败，忽略: {e}")
            
            # 尝试关闭数据库
            try:
                if hasattr(self, 'db_manager') and self.db_manager:
                    self.db_manager.close()
            except Exception as e:
                self.logger.error(f"关闭数据库失败，忽略: {e}")
            
            # 尝试保存配置
            try:
                if hasattr(self, 'config') and self.config:
                    self.config.save_config()
            except Exception as e:
                self.logger.error(f"保存配置失败，忽略: {e}")
            
            self.logger.info("应用程序资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理过程出现异常，忽略: {e}")
        
        # 强制退出，不管上面是否成功
        self.logger.info("执行强制退出")
        try:
            if hasattr(self, 'app') and self.app:
                self.app.quit()
        except:
            pass
        
        # 最后的保障
        import sys
        sys.exit(0)
    
    # 事件处理器
    def _handle_controller_error(self, error_type: str, message: str) -> None:
        """处理控制器错误"""
        self.logger.error(f"控制器错误 [{error_type}]: {message}")
        
        # 在主窗口显示错误信息
        if self.main_window:
            self.main_window.show_error_message(message, f"错误 ({error_type})")
    
    def _handle_operation_completed(self, operation_type: str, result: Dict[str, Any]) -> None:
        """处理操作完成"""
        self.logger.debug(f"操作完成: {operation_type}")
        
        # 根据操作类型执行相应的后续处理
        if operation_type in ['note_created', 'note_updated', 'note_deleted']:
            # 可以在这里添加统计更新等逻辑
            pass
    
    def _on_application_closing(self) -> None:
        """应用程序关闭处理"""
        self.logger.info("应用程序正在关闭")
        
        try:
            # 执行清理操作
            self.cleanup()
            
        except Exception as e:
            self.log_error(e, "应用程序关闭处理失败")