#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置数据模型
负责应用程序设置的存储和管理
"""

import json
from typing import Any, Dict, List, Optional, Union
from models.base_model import BaseModel, ModelEventType


class SettingsModel(BaseModel):
    """设置数据模型"""
    
    def __init__(self, db_manager):
        """初始化设置模型"""
        super().__init__(db_manager)
        self._settings_cache = {}  # 设置缓存
        self._load_all_settings()
    
    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """创建设置项（内部使用set_setting）"""
        key = data.get('key')
        value = data.get('value')
        if key and value is not None:
            return 1 if self.set_setting(key, value) else None
        return None
    
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取设置（设置模型不使用数字ID）"""
        return None
    
    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """更新设置（内部使用set_setting）"""
        key = data.get('key')
        value = data.get('value')
        if key and value is not None:
            return self.set_setting(key, value)
        return False
    
    def delete(self, record_id: int) -> bool:
        """删除设置（设置模型不支持按ID删除）"""
        return False
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """获取所有设置"""
        try:
            sql = "SELECT key, value, created_at, updated_at FROM settings ORDER BY key"
            rows = self.db.execute_query(sql, fetch='all')
            
            settings = []
            for row in rows:
                setting = dict(row)
                # 尝试解析JSON值
                setting['parsed_value'] = self._parse_value(setting['value'])
                settings.append(setting)
            
            return settings
            
        except Exception as e:
            self.log_error(e, "获取所有设置失败")
            return []
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        获取设置值
        
        Args:
            key: 设置键名
            default: 默认值
        
        Returns:
            设置值
        """
        try:
            # 先从缓存获取
            if key in self._settings_cache:
                return self._settings_cache[key]
            
            # 从数据库获取
            sql = "SELECT value FROM settings WHERE key = ?"
            row = self.db.execute_query(sql, (key,), fetch='one')
            
            if row:
                value = self._parse_value(row[0])
                self._settings_cache[key] = value
                return value
            
            return default
            
        except Exception as e:
            self.log_error(e, f"获取设置失败: key={key}")
            return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """
        设置值
        
        Args:
            key: 设置键名
            value: 设置值
        
        Returns:
            设置是否成功
        """
        try:
            # 序列化值
            serialized_value = self._serialize_value(value)
            current_time = self.get_current_timestamp()
            
            # 检查设置是否已存在
            existing = self.db.execute_query(
                "SELECT key FROM settings WHERE key = ?", 
                (key,), 
                fetch='one'
            )
            
            if existing:
                # 更新现有设置
                sql = "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?"
                self.db.execute_query(sql, (serialized_value, current_time, key), fetch='none')
            else:
                # 创建新设置
                sql = "INSERT INTO settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)"
                self.db.execute_query(sql, (key, serialized_value, current_time, current_time), fetch='none')
            
            # 更新缓存
            self._settings_cache[key] = value
            
            self.logger.debug(f"设置成功: {key} = {value}")
            
            # 通知观察者
            self.notify_observers(ModelEventType.RECORD_UPDATED, {
                'key': key,
                'value': value
            })
            
            return True
            
        except Exception as e:
            self.log_error(e, f"设置失败: key={key}, value={value}")
            return False
    
    def delete_setting(self, key: str) -> bool:
        """
        删除设置
        
        Args:
            key: 设置键名
        
        Returns:
            删除是否成功
        """
        try:
            sql = "DELETE FROM settings WHERE key = ?"
            affected_rows = self.db.execute_query(sql, (key,), fetch='none')
            
            if affected_rows > 0:
                # 从缓存中移除
                self._settings_cache.pop(key, None)
                
                self.logger.info(f"删除设置成功: {key}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.RECORD_DELETED, {
                    'key': key
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"删除设置失败: key={key}")
            return False
    
    def get_settings_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        根据前缀获取设置组
        
        Args:
            prefix: 设置键前缀
        
        Returns:
            设置字典
        """
        try:
            sql = "SELECT key, value FROM settings WHERE key LIKE ? ORDER BY key"
            pattern = f"{prefix}%"
            rows = self.db.execute_query(sql, (pattern,), fetch='all')
            
            settings = {}
            for row in rows:
                key = row[0]
                value = self._parse_value(row[1])
                settings[key] = value
                # 更新缓存
                self._settings_cache[key] = value
            
            return settings
            
        except Exception as e:
            self.log_error(e, f"根据前缀获取设置失败: prefix={prefix}")
            return {}
    
    def set_settings_batch(self, settings: Dict[str, Any]) -> bool:
        """
        批量设置
        
        Args:
            settings: 设置字典
        
        Returns:
            设置是否成功
        """
        try:
            success_count = 0
            for key, value in settings.items():
                if self.set_setting(key, value):
                    success_count += 1
            
            self.logger.info(f"批量设置完成: 成功{success_count}/{len(settings)}项")
            return success_count == len(settings)
            
        except Exception as e:
            self.log_error(e, "批量设置失败")
            return False
    
    def load_default_settings(self) -> None:
        """加载默认设置"""
        default_settings = {
            # 窗口设置
            'window.width': 1200,
            'window.height': 800,
            'window.x': -1,  # -1表示居中
            'window.y': -1,
            'window.maximized': False,
            'window.edge_trigger_width': 5,
            'window.peek_width': 300,
            'window.hide_delay': 2000,
            'window.always_on_top': False,
            
            # UI设置
            'ui.theme': 'auto',  # auto, light, dark
            'ui.language': 'zh_CN',
            'ui.font_size': 12,
            'ui.animation_enabled': True,
            
            # 功能设置
            'features.auto_save': True,
            'features.auto_save_interval': 30,  # 秒
            'features.spell_check': False,
            'features.word_wrap': True,
            'features.show_line_numbers': False,
            
            # 搜索设置
            'search.max_results': 100,
            'search.highlight_enabled': True,
            'search.fuzzy_search': True,
            'search.case_sensitive': False,
            
            # 备份设置
            'backup.enabled': True,
            'backup.interval_days': 7,
            'backup.max_backups': 10,
            
            # 性能设置
            'performance.cache_enabled': True,
            'performance.cache_size_mb': 50,
            'performance.lazy_load': True,
        }
        
        for key, value in default_settings.items():
            # 只设置不存在的默认值
            if self.get_setting(key) is None:
                self.set_setting(key, value)
        
        self.logger.info("默认设置加载完成")
    
    def reset_to_defaults(self) -> bool:
        """重置为默认设置"""
        try:
            # 清除所有设置
            self.db.execute_query("DELETE FROM settings", fetch='none')
            self._settings_cache.clear()
            
            # 加载默认设置
            self.load_default_settings()
            
            self.logger.info("设置已重置为默认值")
            return True
            
        except Exception as e:
            self.log_error(e, "重置设置失败")
            return False
    
    def export_settings(self) -> Dict[str, Any]:
        """导出所有设置"""
        try:
            all_settings = self.get_all()
            
            export_data = {}
            for setting in all_settings:
                export_data[setting['key']] = setting['parsed_value']
            
            self.logger.info(f"导出设置: {len(export_data)}项")
            return export_data
            
        except Exception as e:
            self.log_error(e, "导出设置失败")
            return {}
    
    def import_settings(self, settings: Dict[str, Any]) -> bool:
        """
        导入设置
        
        Args:
            settings: 设置字典
        
        Returns:
            导入是否成功
        """
        try:
            imported_count = 0
            
            for key, value in settings.items():
                if self.set_setting(key, value):
                    imported_count += 1
            
            self.logger.info(f"导入设置: 成功{imported_count}/{len(settings)}项")
            return imported_count > 0
            
        except Exception as e:
            self.log_error(e, "导入设置失败")
            return False
    
    def _load_all_settings(self) -> None:
        """加载所有设置到缓存"""
        try:
            all_settings = self.get_all()
            
            for setting in all_settings:
                self._settings_cache[setting['key']] = setting['parsed_value']
            
            self.logger.debug(f"设置缓存加载完成: {len(self._settings_cache)}项")
            
        except Exception as e:
            self.log_error(e, "加载设置缓存失败")
    
    def _serialize_value(self, value: Any) -> str:
        """序列化设置值"""
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        else:
            return str(value)
    
    def _parse_value(self, value: str) -> Any:
        """解析设置值"""
        if not isinstance(value, str):
            return value
        
        # 尝试解析布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 尝试解析数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 尝试解析JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 返回原字符串
        return value
    
    def get_window_settings(self) -> Dict[str, Any]:
        """获取窗口相关设置"""
        return self.get_settings_by_prefix('window.')
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """获取UI相关设置"""
        return self.get_settings_by_prefix('ui.')
    
    def get_feature_settings(self) -> Dict[str, Any]:
        """获取功能相关设置"""
        return self.get_settings_by_prefix('features.')
    
    def get_search_settings(self) -> Dict[str, Any]:
        """获取搜索相关设置"""
        return self.get_settings_by_prefix('search.')
    
    def is_first_run(self) -> bool:
        """检查是否首次运行"""
        return self.get_setting('app.first_run', True)
    
    def mark_first_run_complete(self) -> None:
        """标记首次运行完成"""
        self.set_setting('app.first_run', False)