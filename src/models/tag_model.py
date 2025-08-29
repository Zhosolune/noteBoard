#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签数据模型
负责标签的CRUD操作和业务逻辑
"""

from typing import Any, Dict, List, Optional
from src.models.base_model import BaseModel, ModelEventType


class TagModel(BaseModel):
    """标签数据模型"""
    
    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """
        创建新标签
        
        Args:
            data: 标签数据，包含name, color等字段
        
        Returns:
            新标签的ID，失败返回None
        """
        # 验证必需字段
        required_fields = ['name']
        if not self.validate_data(data, required_fields):
            return None
        
        try:
            # 准备插入数据
            name = data.get('name', '').strip()
            color = data.get('color', '#007ACC')
            current_time = self.get_current_timestamp()
            
            if not name:
                self.logger.warning("标签名称不能为空")
                return None
            
            # 检查标签名是否已存在
            if self.get_by_name(name):
                self.logger.warning(f"标签名称已存在: {name}")
                return None
            
            # 验证颜色格式
            if not self._validate_color(color):
                self.logger.warning(f"无效的颜色格式: {color}")
                color = '#007ACC'  # 使用默认颜色
            
            # 插入标签记录
            sql = """
                INSERT INTO tags (name, color, created_at)
                VALUES (?, ?, ?)
            """
            self.db.execute_query(
                sql, 
                (name, color, current_time), 
                fetch='none'
            )
            
            tag_id = self.db.execute_query(
                "SELECT last_insert_rowid()",
                fetch='one'
            )[0]
            
            self.logger.info(f"创建标签成功: ID={tag_id}, 名称={name}")
            
            # 通知观察者
            self.notify_observers(ModelEventType.TAG_CREATED, {
                'tag_id': tag_id,
                'name': name,
                'color': color
            })
            
            return tag_id
            
        except Exception as e:
            self.log_error(e, "创建标签失败")
            return None
    
    def get_by_id(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取标签
        
        Args:
            tag_id: 标签ID
        
        Returns:
            标签数据字典
        """
        try:
            sql = """
                SELECT id, name, color, created_at
                FROM tags 
                WHERE id = ?
            """
            row = self.db.execute_query(sql, (tag_id,), fetch='one')
            
            if row:
                tag = dict(row)
                # 获取使用此标签的笔记数量
                tag['note_count'] = self._get_tag_note_count(tag_id)
                return tag
            
            return None
            
        except Exception as e:
            self.log_error(e, f"获取标签失败: ID={tag_id}")
            return None
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取标签
        
        Args:
            name: 标签名称
        
        Returns:
            标签数据字典
        """
        try:
            sql = """
                SELECT id, name, color, created_at
                FROM tags 
                WHERE name = ?
            """
            row = self.db.execute_query(sql, (name.strip(),), fetch='one')
            
            if row:
                tag = dict(row)
                tag['note_count'] = self._get_tag_note_count(tag['id'])
                return tag
            
            return None
            
        except Exception as e:
            self.log_error(e, f"根据名称获取标签失败: {name}")
            return None
    
    def update(self, tag_id: int, data: Dict[str, Any]) -> bool:
        """
        更新标签
        
        Args:
            tag_id: 标签ID
            data: 更新数据
        
        Returns:
            更新是否成功
        """
        try:
            # 检查标签是否存在
            existing_tag = self.get_by_id(tag_id)
            if not existing_tag:
                self.logger.warning(f"标签不存在: ID={tag_id}")
                return False
            
            # 构建更新SQL
            update_fields = []
            update_values = []
            
            if 'name' in data:
                name = data['name'].strip()
                if not name:
                    self.logger.warning("标签名称不能为空")
                    return False
                
                # 检查名称是否与其他标签冲突
                existing_by_name = self.get_by_name(name)
                if existing_by_name and existing_by_name['id'] != tag_id:
                    self.logger.warning(f"标签名称已存在: {name}")
                    return False
                
                update_fields.append("name = ?")
                update_values.append(name)
            
            if 'color' in data:
                color = data['color']
                if not self._validate_color(color):
                    self.logger.warning(f"无效的颜色格式: {color}")
                    return False
                
                update_fields.append("color = ?")
                update_values.append(color)
            
            if not update_fields:
                self.logger.warning("没有需要更新的字段")
                return False
            
            # 执行更新
            update_values.append(tag_id)
            sql = f"""
                UPDATE tags 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            
            affected_rows = self.db.execute_query(sql, update_values, fetch='none')
            
            if affected_rows > 0:
                self.logger.info(f"更新标签成功: ID={tag_id}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.TAG_UPDATED, {
                    'tag_id': tag_id,
                    'updated_data': data
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"更新标签失败: ID={tag_id}")
            return False
    
    def delete(self, tag_id: int) -> bool:
        """
        删除标签
        
        Args:
            tag_id: 标签ID
        
        Returns:
            删除是否成功
        """
        try:
            # 检查标签是否存在
            tag = self.get_by_id(tag_id)
            if not tag:
                self.logger.warning(f"标签不存在: ID={tag_id}")
                return False
            
            # 检查是否有笔记使用此标签
            note_count = self._get_tag_note_count(tag_id)
            if note_count > 0:
                self.logger.warning(f"标签正在使用中，无法删除: ID={tag_id}, 使用数量={note_count}")
                return False
            
            # 删除标签
            sql = "DELETE FROM tags WHERE id = ?"
            affected_rows = self.db.execute_query(sql, (tag_id,), fetch='none')
            
            if affected_rows > 0:
                self.logger.info(f"删除标签成功: ID={tag_id}, 名称={tag['name']}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.TAG_DELETED, {
                    'tag_id': tag_id,
                    'name': tag['name']
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"删除标签失败: ID={tag_id}")
            return False
    
    def force_delete(self, tag_id: int) -> bool:
        """
        强制删除标签（包括相关联的笔记标签关系）
        
        Args:
            tag_id: 标签ID
        
        Returns:
            删除是否成功
        """
        try:
            # 检查标签是否存在
            tag = self.get_by_id(tag_id)
            if not tag:
                self.logger.warning(f"标签不存在: ID={tag_id}")
                return False
            
            # 先删除标签关联关系
            self.db.execute_query(
                "DELETE FROM note_tags WHERE tag_id = ?", 
                (tag_id,), 
                fetch='none'
            )
            
            # 删除标签
            sql = "DELETE FROM tags WHERE id = ?"
            affected_rows = self.db.execute_query(sql, (tag_id,), fetch='none')
            
            if affected_rows > 0:
                self.logger.info(f"强制删除标签成功: ID={tag_id}, 名称={tag['name']}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.TAG_DELETED, {
                    'tag_id': tag_id,
                    'name': tag['name'],
                    'force_delete': True
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"强制删除标签失败: ID={tag_id}")
            return False
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取所有标签
        
        Args:
            filters: 过滤条件，支持:
                - limit: 限制数量
                - offset: 偏移量
                - order_by: 排序字段
                - order_direction: 排序方向 (ASC/DESC)
                - include_unused: 是否包含未使用的标签
        
        Returns:
            标签列表
        """
        try:
            filters = filters or {}
            
            # 构建基础查询
            sql_parts = [
                "SELECT t.id, t.name, t.color, t.created_at",
                "FROM tags t"
            ]
            where_conditions = []
            query_params = []
            
            # 处理未使用标签过滤
            if not filters.get('include_unused', True):
                sql_parts.append("JOIN note_tags nt ON t.id = nt.tag_id")
                sql_parts = [
                    "SELECT DISTINCT t.id, t.name, t.color, t.created_at",
                    "FROM tags t",
                    "JOIN note_tags nt ON t.id = nt.tag_id"
                ]
            
            # 组合WHERE条件
            if where_conditions:
                sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
            
            # 处理排序
            order_by = filters.get('order_by', 'name')
            order_direction = filters.get('order_direction', 'ASC')
            if order_by in ['id', 'name', 'created_at']:
                sql_parts.append(f"ORDER BY t.{order_by} {order_direction}")
            
            # 处理分页
            if filters.get('limit'):
                sql_parts.append("LIMIT ?")
                query_params.append(filters['limit'])
                
                if filters.get('offset'):
                    sql_parts.append("OFFSET ?")
                    query_params.append(filters['offset'])
            
            # 执行查询
            sql = ' '.join(sql_parts)
            rows = self.db.execute_query(sql, query_params, fetch='all')
            
            # 转换为字典列表并添加使用数量信息
            tags = []
            for row in rows:
                tag = dict(row)
                tag['note_count'] = self._get_tag_note_count(tag['id'])
                tags.append(tag)
            
            return tags
            
        except Exception as e:
            self.log_error(e, "获取标签列表失败")
            return []
    
    def get_by_note(self, note_id: int) -> List[Dict[str, Any]]:
        """
        获取笔记的所有标签
        
        Args:
            note_id: 笔记ID
        
        Returns:
            标签列表
        """
        try:
            sql = """
                SELECT t.id, t.name, t.color, t.created_at
                FROM tags t
                JOIN note_tags nt ON t.id = nt.tag_id
                WHERE nt.note_id = ?
                ORDER BY t.name
            """
            rows = self.db.execute_query(sql, (note_id,), fetch='all')
            
            tags = []
            for row in rows:
                tag = dict(row)
                tag['note_count'] = self._get_tag_note_count(tag['id'])
                tags.append(tag)
            
            return tags
            
        except Exception as e:
            self.log_error(e, f"获取笔记标签失败: note_id={note_id}")
            return []
    
    def get_unused_tags(self) -> List[Dict[str, Any]]:
        """获取未使用的标签"""
        return self.get_all({'include_unused': False})
    
    def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门标签（按使用频率排序）
        
        Args:
            limit: 返回数量限制
        
        Returns:
            热门标签列表
        """
        try:
            sql = """
                SELECT t.id, t.name, t.color, t.created_at, COUNT(nt.note_id) as note_count
                FROM tags t
                JOIN note_tags nt ON t.id = nt.tag_id
                GROUP BY t.id, t.name, t.color, t.created_at
                ORDER BY note_count DESC, t.name ASC
                LIMIT ?
            """
            rows = self.db.execute_query(sql, (limit,), fetch='all')
            
            return [dict(row) for row in rows] if rows else []
            
        except Exception as e:
            self.log_error(e, "获取热门标签失败")
            return []
    
    def search_tags(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索标签
        
        Args:
            keyword: 搜索关键词
            limit: 结果限制数量
        
        Returns:
            匹配的标签列表
        """
        try:
            sql = """
                SELECT id, name, color, created_at
                FROM tags
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """
            keyword_pattern = f"%{keyword}%"
            rows = self.db.execute_query(sql, (keyword_pattern, limit), fetch='all')
            
            tags = []
            for row in rows:
                tag = dict(row)
                tag['note_count'] = self._get_tag_note_count(tag['id'])
                tags.append(tag)
            
            return tags
            
        except Exception as e:
            self.log_error(e, f"搜索标签失败: keyword={keyword}")
            return []
    
    def get_tags_count(self) -> int:
        """获取标签总数"""
        try:
            sql = "SELECT COUNT(*) FROM tags"
            row = self.db.execute_query(sql, fetch='one')
            return row[0] if row else 0
        except Exception as e:
            self.log_error(e, "获取标签数量失败")
            return 0
    
    def _get_tag_note_count(self, tag_id: int) -> int:
        """获取使用指定标签的笔记数量"""
        try:
            sql = """
                SELECT COUNT(DISTINCT nt.note_id) 
                FROM note_tags nt
                JOIN notes n ON nt.note_id = n.id
                WHERE nt.tag_id = ? AND n.is_deleted = 0
            """
            row = self.db.execute_query(sql, (tag_id,), fetch='one')
            return row[0] if row else 0
        except Exception as e:
            self.log_error(e, f"获取标签使用数量失败: tag_id={tag_id}")
            return 0
    
    def _validate_color(self, color: str) -> bool:
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
    
    def get_or_create_tag(self, name: str, color: str = '#007ACC') -> Optional[Dict[str, Any]]:
        """
        获取或创建标签
        
        Args:
            name: 标签名称
            color: 标签颜色
        
        Returns:
            标签数据字典
        """
        # 先尝试获取现有标签
        existing_tag = self.get_by_name(name)
        if existing_tag:
            return existing_tag
        
        # 创建新标签
        tag_id = self.create({'name': name, 'color': color})
        if tag_id:
            return self.get_by_id(tag_id)
        
        return None
