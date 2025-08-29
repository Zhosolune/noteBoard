#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签控制器
负责标签相关的业务逻辑和操作协调
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import Signal

from src.controllers.base_controller import BaseController, OperationResult
from src.models.base_model import ModelEventType


class TagController(BaseController):
    """标签控制器"""
    
    # 标签相关信号
    tag_created = Signal(int, str, str)   # 标签ID, 名称, 颜色
    tag_updated = Signal(int)             # 标签ID
    tag_deleted = Signal(int, str)        # 标签ID, 名称
    tag_list_changed = Signal()           # 标签列表变更
    tag_selected = Signal(int)            # 标签被选中
    
    def __init__(self, parent=None):
        """初始化标签控制器"""
        super().__init__(parent)
        
        self._selected_tag_ids = []  # 当前选中的标签ID列表
        
        # 预定义的标签颜色
        self._predefined_colors = [
            '#007ACC',  # 蓝色
            '#28A745',  # 绿色
            '#DC3545',  # 红色
            '#FFC107',  # 黄色
            '#6F42C1',  # 紫色
            '#FD7E14',  # 橙色
            '#20C997',  # 青色
            '#E83E8C',  # 粉色
            '#6C757D',  # 灰色
            '#17A2B8',  # 浅蓝
        ]
    
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
        self.tag_created.connect(self._on_tag_created)
        self.tag_updated.connect(self._on_tag_updated)
        self.tag_deleted.connect(self._on_tag_deleted)
    
    def setup_event_handlers(self) -> None:
        """设置事件处理器"""
        super().setup_event_handlers()
        
        # 注册标签相关事件处理器
        self.register_event_handler(ModelEventType.TAG_CREATED, self._handle_tag_created)
        self.register_event_handler(ModelEventType.TAG_UPDATED, self._handle_tag_updated)
        self.register_event_handler(ModelEventType.TAG_DELETED, self._handle_tag_deleted)
    
    def create_tag(self, name: str, color: str = None) -> OperationResult:
        """
        创建新标签
        
        Args:
            name: 标签名称
            color: 标签颜色，如果为None则自动分配
        
        Returns:
            操作结果
        """
        try:
            self.emit_status_changed("正在创建标签...")
            
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            # 验证标签名称
            name = name.strip()
            if not name:
                return OperationResult.error_result("标签名称不能为空")
            
            # 检查标签是否已存在
            existing_tag = tag_model.get_by_name(name)
            if existing_tag:
                return OperationResult.error_result(f"标签 '{name}' 已存在")
            
            # 如果没有指定颜色，自动分配颜色
            if not color:
                color = self._get_next_available_color()
            
            # 准备标签数据
            tag_data = {
                'name': name,
                'color': color
            }
            
            # 创建标签
            tag_id = tag_model.create(tag_data)
            
            if tag_id:
                self.logger.info(f"创建标签成功: ID={tag_id}, 名称={name}")
                return OperationResult.success_result({
                    'tag_id': tag_id,
                    'name': name,
                    'color': color
                })
            else:
                return OperationResult.error_result("创建标签失败")
                
        except Exception as e:
            self.log_error(e, "创建标签异常")
            return OperationResult.error_result(f"创建标签异常: {str(e)}")
    
    def update_tag(self, tag_id: int, data: Dict[str, Any]) -> OperationResult:
        """
        更新标签
        
        Args:
            tag_id: 标签ID
            data: 更新数据
        
        Returns:
            操作结果
        """
        try:
            self.emit_status_changed("正在更新标签...")
            
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            # 验证标签名称
            if 'name' in data:
                name = data['name'].strip()
                if not name:
                    return OperationResult.error_result("标签名称不能为空")
                
                # 检查名称冲突
                existing_tag = tag_model.get_by_name(name)
                if existing_tag and existing_tag['id'] != tag_id:
                    return OperationResult.error_result(f"标签名称 '{name}' 已存在")
                
                data['name'] = name
            
            # 更新标签
            success = tag_model.update(tag_id, data)
            
            if success:
                self.logger.info(f"更新标签成功: ID={tag_id}")
                return OperationResult.success_result({'tag_id': tag_id})
            else:
                return OperationResult.error_result("更新标签失败")
                
        except Exception as e:
            self.log_error(e, f"更新标签异常: ID={tag_id}")
            return OperationResult.error_result(f"更新标签异常: {str(e)}")
    
    def delete_tag(self, tag_id: int, force: bool = False) -> OperationResult:
        """
        删除标签
        
        Args:
            tag_id: 标签ID
            force: 是否强制删除（包括相关联的笔记标签关系）
        
        Returns:
            操作结果
        """
        try:
            self.emit_status_changed("正在删除标签...")
            
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            # 获取标签信息
            tag = tag_model.get_by_id(tag_id)
            if not tag:
                return OperationResult.error_result("标签不存在")
            
            # 根据强制删除标志选择删除方法
            if force:
                success = tag_model.force_delete(tag_id)
            else:
                success = tag_model.delete(tag_id)
            
            if success:
                self.logger.info(f"删除标签成功: ID={tag_id}, 名称={tag['name']}")
                
                # 如果删除的标签在选中列表中，移除它
                if tag_id in self._selected_tag_ids:
                    self._selected_tag_ids.remove(tag_id)
                
                return OperationResult.success_result({
                    'tag_id': tag_id,
                    'name': tag['name'],
                    'force': force
                })
            else:
                if not force and tag.get('note_count', 0) > 0:
                    return OperationResult.error_result(f"标签 '{tag['name']}' 正在使用中，无法删除")
                else:
                    return OperationResult.error_result("删除标签失败")
                
        except Exception as e:
            self.log_error(e, f"删除标签异常: ID={tag_id}")
            return OperationResult.error_result(f"删除标签异常: {str(e)}")
    
    def get_tag(self, tag_id: int) -> OperationResult:
        """
        获取标签详情
        
        Args:
            tag_id: 标签ID
        
        Returns:
            操作结果，包含标签数据
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            tag = tag_model.get_by_id(tag_id)
            
            if tag:
                return OperationResult.success_result(tag)
            else:
                return OperationResult.error_result("标签不存在")
                
        except Exception as e:
            self.log_error(e, f"获取标签异常: ID={tag_id}")
            return OperationResult.error_result(f"获取标签异常: {str(e)}")
    
    def get_tag_list(self, filters: Optional[Dict[str, Any]] = None) -> OperationResult:
        """
        获取标签列表
        
        Args:
            filters: 过滤条件
        
        Returns:
            操作结果，包含标签列表
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            tags = tag_model.get_all(filters)
            
            return OperationResult.success_result({
                'tags': tags,
                'total_count': len(tags)
            })
                
        except Exception as e:
            self.log_error(e, "获取标签列表异常")
            return OperationResult.error_result(f"获取标签列表异常: {str(e)}")
    
    def search_tags(self, keyword: str, limit: int = 20) -> OperationResult:
        """
        搜索标签
        
        Args:
            keyword: 搜索关键词
            limit: 结果限制数量
        
        Returns:
            操作结果，包含搜索结果
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            if not keyword.strip():
                return self.get_tag_list({'limit': limit})
            
            tags = tag_model.search_tags(keyword.strip(), limit)
            
            return OperationResult.success_result({
                'tags': tags,
                'keyword': keyword,
                'total_count': len(tags)
            })
                
        except Exception as e:
            self.log_error(e, f"搜索标签异常: keyword={keyword}")
            return OperationResult.error_result(f"搜索标签异常: {str(e)}")
    
    def get_popular_tags(self, limit: int = 10) -> OperationResult:
        """
        获取热门标签
        
        Args:
            limit: 返回数量限制
        
        Returns:
            操作结果，包含热门标签列表
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            tags = tag_model.get_popular_tags(limit)
            
            return OperationResult.success_result({
                'tags': tags,
                'total_count': len(tags)
            })
                
        except Exception as e:
            self.log_error(e, "获取热门标签异常")
            return OperationResult.error_result(f"获取热门标签异常: {str(e)}")
    
    def get_unused_tags(self) -> OperationResult:
        """
        获取未使用的标签
        
        Returns:
            操作结果，包含未使用的标签列表
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            tags = tag_model.get_unused_tags()
            
            return OperationResult.success_result({
                'tags': tags,
                'total_count': len(tags)
            })
                
        except Exception as e:
            self.log_error(e, "获取未使用标签异常")
            return OperationResult.error_result(f"获取未使用标签异常: {str(e)}")
    
    def get_tags_by_note(self, note_id: int) -> OperationResult:
        """
        获取笔记的所有标签
        
        Args:
            note_id: 笔记ID
        
        Returns:
            操作结果，包含标签列表
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            tags = tag_model.get_by_note(note_id)
            
            return OperationResult.success_result({
                'tags': tags,
                'note_id': note_id,
                'total_count': len(tags)
            })
                
        except Exception as e:
            self.log_error(e, f"获取笔记标签异常: note_id={note_id}")
            return OperationResult.error_result(f"获取笔记标签异常: {str(e)}")
    
    def get_or_create_tag(self, name: str, color: str = None) -> OperationResult:
        """
        获取或创建标签
        
        Args:
            name: 标签名称
            color: 标签颜色
        
        Returns:
            操作结果，包含标签数据
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            # 如果没有指定颜色，使用默认颜色
            if not color:
                color = self._get_next_available_color()
            
            tag = tag_model.get_or_create_tag(name.strip(), color)
            
            if tag:
                return OperationResult.success_result(tag)
            else:
                return OperationResult.error_result("获取或创建标签失败")
                
        except Exception as e:
            self.log_error(e, f"获取或创建标签异常: name={name}")
            return OperationResult.error_result(f"获取或创建标签异常: {str(e)}")
    
    def select_tags(self, tag_ids: List[int]) -> None:
        """
        选择标签（用于筛选）
        
        Args:
            tag_ids: 标签ID列表
        """
        self._selected_tag_ids = list(tag_ids)
        self.logger.debug(f"选择标签: {tag_ids}")
        
        # 发出标签选中信号
        for tag_id in tag_ids:
            self.tag_selected.emit(tag_id)
    
    def add_selected_tag(self, tag_id: int) -> None:
        """
        添加到选中的标签列表
        
        Args:
            tag_id: 标签ID
        """
        if tag_id not in self._selected_tag_ids:
            self._selected_tag_ids.append(tag_id)
            self.tag_selected.emit(tag_id)
            self.logger.debug(f"添加选中标签: {tag_id}")
    
    def remove_selected_tag(self, tag_id: int) -> None:
        """
        从选中的标签列表中移除
        
        Args:
            tag_id: 标签ID
        """
        if tag_id in self._selected_tag_ids:
            self._selected_tag_ids.remove(tag_id)
            self.logger.debug(f"移除选中标签: {tag_id}")
    
    def clear_selected_tags(self) -> None:
        """清除所有选中的标签"""
        self._selected_tag_ids.clear()
        self.logger.debug("清除所有选中标签")
    
    def get_selected_tag_ids(self) -> List[int]:
        """获取当前选中的标签ID列表"""
        return list(self._selected_tag_ids)
    
    def get_predefined_colors(self) -> List[str]:
        """获取预定义的标签颜色列表"""
        return list(self._predefined_colors)
    
    def _get_next_available_color(self) -> str:
        """获取下一个可用的颜色"""
        try:
            # 获取当前所有标签的颜色
            result = self.get_tag_list()
            if not result.success:
                return self._predefined_colors[0]
            
            used_colors = set()
            for tag in result.data['tags']:
                used_colors.add(tag.get('color', ''))
            
            # 找到第一个未使用的预定义颜色
            for color in self._predefined_colors:
                if color not in used_colors:
                    return color
            
            # 如果所有预定义颜色都被使用，返回第一个颜色
            return self._predefined_colors[0]
            
        except Exception as e:
            self.log_error(e, "获取下一个可用颜色异常")
            return self._predefined_colors[0]
    
    def validate_color(self, color: str) -> bool:
        """
        验证颜色格式
        
        Args:
            color: 颜色字符串
        
        Returns:
            颜色格式是否有效
        """
        if not isinstance(color, str):
            return False
        
        # 支持十六进制颜色格式 #RRGGBB 或 #RGB
        import re
        hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.match(hex_pattern, color))
    
    def get_tags_statistics(self) -> OperationResult:
        """
        获取标签统计信息
        
        Returns:
            操作结果，包含统计数据
        """
        try:
            tag_model = self.get_model('tag')
            if not tag_model:
                return OperationResult.error_result("标签模型未初始化")
            
            # 获取所有标签
            all_tags_result = self.get_tag_list()
            if not all_tags_result.success:
                return all_tags_result
            
            all_tags = all_tags_result.data['tags']
            
            # 统计信息
            total_tags = len(all_tags)
            used_tags = [tag for tag in all_tags if tag.get('note_count', 0) > 0]
            unused_tags = [tag for tag in all_tags if tag.get('note_count', 0) == 0]
            
            # 计算总使用数
            total_usage = sum(tag.get('note_count', 0) for tag in all_tags)
            
            # 最常用的标签
            most_used_tag = max(all_tags, key=lambda x: x.get('note_count', 0)) if all_tags else None
            
            statistics = {
                'total_tags': total_tags,
                'used_tags_count': len(used_tags),
                'unused_tags_count': len(unused_tags),
                'total_usage': total_usage,
                'average_usage': total_usage / total_tags if total_tags > 0 else 0,
                'most_used_tag': most_used_tag,
                'usage_distribution': {
                    'used_tags': used_tags,
                    'unused_tags': unused_tags
                }
            }
            
            return OperationResult.success_result(statistics)
            
        except Exception as e:
            self.log_error(e, "获取标签统计异常")
            return OperationResult.error_result(f"获取标签统计异常: {str(e)}")
    
    # 事件处理器
    def _handle_tag_created(self, data: Any) -> None:
        """处理标签创建事件"""
        if isinstance(data, dict) and 'tag_id' in data:
            tag_id = data['tag_id']
            name = data.get('name', '')
            color = data.get('color', '')
            self.tag_created.emit(tag_id, name, color)
    
    def _handle_tag_updated(self, data: Any) -> None:
        """处理标签更新事件"""
        if isinstance(data, dict) and 'tag_id' in data:
            tag_id = data['tag_id']
            self.tag_updated.emit(tag_id)
    
    def _handle_tag_deleted(self, data: Any) -> None:
        """处理标签删除事件"""
        if isinstance(data, dict) and 'tag_id' in data:
            tag_id = data['tag_id']
            name = data.get('name', '')
            self.tag_deleted.emit(tag_id, name)
    
    # 信号槽
    def _on_tag_created(self, tag_id: int, name: str, color: str) -> None:
        """标签创建时的处理"""
        self.tag_list_changed.emit()
        self.emit_status_changed(f"标签创建成功: {name}")
    
    def _on_tag_updated(self, tag_id: int) -> None:
        """标签更新时的处理"""
        self.tag_list_changed.emit()
        self.emit_status_changed("标签更新成功")
    
    def _on_tag_deleted(self, tag_id: int, name: str) -> None:
        """标签删除时的处理"""
        self.tag_list_changed.emit()
        self.emit_status_changed(f"标签删除成功: {name}")
    
    def cleanup(self) -> None:
        """清理资源"""
        self._selected_tag_ids.clear()
        super().cleanup()