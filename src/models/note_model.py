#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔记数据模型
负责笔记的CRUD操作和业务逻辑
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from src.models.base_model import BaseModel, ModelEventType


class NoteModel(BaseModel):
    """笔记数据模型"""
    
    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """
        创建新笔记
        
        Args:
            data: 笔记数据，包含title, content等字段
        
        Returns:
            新笔记的ID，失败返回None
        """
        # 验证必需字段
        required_fields: list[str] = ['title']
        if not self.validate_data(data, required_fields):
            return None
        
        try:
            # 准备插入数据
            title = data.get('title', '').strip()
            content = data.get('content', '')
            current_time = self.get_current_timestamp()
            
            if not title:
                self.logger.warning("笔记标题不能为空")
                return None
            
            # 插入笔记记录
            sql = """
                INSERT INTO notes (title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """
            self.db.execute_query(
                sql, 
                (title, content, current_time, current_time), 
                fetch='none'
            )
            
            note_id = self.db.execute_query(
                "SELECT last_insert_rowid()",
                fetch='one'
            )[0]
            
            # 处理标签关联
            if 'tag_ids' in data and data['tag_ids']:
                self._add_note_tags(note_id, data['tag_ids'])
            
            self.logger.info(f"创建笔记成功: ID={note_id}, 标题={title}")
            
            # 通知观察者
            self.notify_observers(ModelEventType.NOTE_CREATED, {
                'note_id': note_id,
                'title': title
            })
            
            return note_id
            
        except Exception as e:
            self.log_error(e, "创建笔记失败")
            return None
    
    def get_by_id(self, note_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取笔记
        
        Args:
            note_id: 笔记ID
        
        Returns:
            笔记数据字典
        """
        try:
            sql = """
                SELECT id, title, content, created_at, updated_at, is_deleted
                FROM notes 
                WHERE id = ? AND is_deleted = 0
            """
            row = self.db.execute_query(sql, (note_id,), fetch='one')
            
            if row:
                note = dict(row)
                # 获取关联的标签
                note['tags'] = self._get_note_tags(note_id)
                return note
            
            return None
            
        except Exception as e:
            self.log_error(e, f"获取笔记失败: ID={note_id}")
            return None
    
    def update(self, note_id: int, data: Dict[str, Any]) -> bool:
        """
        更新笔记
        
        Args:
            note_id: 笔记ID
            data: 更新数据
        
        Returns:
            更新是否成功
        """
        try:
            # 检查笔记是否存在
            if not self.get_by_id(note_id):
                self.logger.warning(f"笔记不存在: ID={note_id}")
                return False
            
            # 构建更新SQL
            update_fields = []
            update_values = []
            
            if 'title' in data:
                title = data['title'].strip()
                if not title:
                    self.logger.warning("笔记标题不能为空")
                    return False
                update_fields.append("title = ?")
                update_values.append(title)
            
            if 'content' in data:
                update_fields.append("content = ?")
                update_values.append(data['content'])
            
            # 更新时间
            update_fields.append("updated_at = ?")
            update_values.append(self.get_current_timestamp())
            
            if not update_fields:
                self.logger.warning("没有需要更新的字段")
                return False
            
            # 执行更新
            update_values.append(note_id)
            sql = f"""
                UPDATE notes 
                SET {', '.join(update_fields)}
                WHERE id = ? AND is_deleted = 0
            """
            
            affected_rows = self.db.execute_query(sql, update_values, fetch='none')
            
            if affected_rows > 0:
                # 处理标签更新
                if 'tag_ids' in data:
                    self._update_note_tags(note_id, data['tag_ids'])
                
                self.logger.info(f"更新笔记成功: ID={note_id}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.NOTE_UPDATED, {
                    'note_id': note_id,
                    'updated_data': data
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"更新笔记失败: ID={note_id}")
            return False
    
    def delete(self, note_id: int) -> bool:
        """
        软删除笔记
        
        Args:
            note_id: 笔记ID
        
        Returns:
            删除是否成功
        """
        try:
            # 检查笔记是否存在
            note = self.get_by_id(note_id)
            if not note:
                self.logger.warning(f"笔记不存在: ID={note_id}")
                return False
            
            # 软删除笔记
            sql = """
                UPDATE notes 
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
            """
            
            affected_rows = self.db.execute_query(
                sql, 
                (self.get_current_timestamp(), note_id), 
                fetch='none'
            )
            
            if affected_rows > 0:
                # 删除标签关联
                self._clear_note_tags(note_id)
                
                self.logger.info(f"删除笔记成功: ID={note_id}, 标题={note['title']}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.NOTE_DELETED, {
                    'note_id': note_id,
                    'title': note['title']
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"删除笔记失败: ID={note_id}")
            return False
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取所有笔记
        
        Args:
            filters: 过滤条件，支持:
                - limit: 限制数量
                - offset: 偏移量
                - order_by: 排序字段
                - order_direction: 排序方向 (ASC/DESC)
                - tag_ids: 标签ID列表
                - search_keyword: 搜索关键词
        
        Returns:
            笔记列表
        """
        try:
            filters = filters or {}
            
            # 构建基础查询
            sql_parts = [
                "SELECT DISTINCT n.id, n.title, n.content, n.created_at, n.updated_at",
                "FROM notes n"
            ]
            where_conditions = ["n.is_deleted = 0"]
            query_params = []
            
            # 处理标签筛选
            if filters.get('tag_ids'):
                tag_ids = filters['tag_ids']
                if isinstance(tag_ids, (list, tuple)) and len(tag_ids) > 0:
                    placeholders = ','.join(['?' for _ in tag_ids])
                    sql_parts.append("JOIN note_tags nt ON n.id = nt.note_id")
                    where_conditions.append(f"nt.tag_id IN ({placeholders})")
                    query_params.extend(tag_ids)
            
            # 处理搜索关键词
            if filters.get('search_keyword'):
                keyword = f"%{filters['search_keyword']}%"
                where_conditions.append("(n.title LIKE ? OR n.content LIKE ?)")
                query_params.extend([keyword, keyword])
            
            # 组合WHERE条件
            if where_conditions:
                sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
            
            # 处理排序
            order_by = filters.get('order_by', 'updated_at')
            order_direction = filters.get('order_direction', 'DESC')
            if order_by in ['id', 'title', 'created_at', 'updated_at']:
                sql_parts.append(f"ORDER BY n.{order_by} {order_direction}")
            
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
            
            # 转换为字典列表并添加标签信息
            notes = []
            for row in rows:
                note = dict(row)
                note['tags'] = self._get_note_tags(note['id'])
                notes.append(note)
            
            return notes
            
        except Exception as e:
            self.log_error(e, "获取笔记列表失败")
            return []
    
    def search(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索笔记
        
        Args:
            keyword: 搜索关键词
            limit: 结果限制数量
        
        Returns:
            匹配的笔记列表
        """
        return self.get_all({
            'search_keyword': keyword,
            'limit': limit,
            'order_by': 'updated_at',
            'order_direction': 'DESC'
        })
    
    def get_by_tags(self, tag_ids: List[int]) -> List[Dict[str, Any]]:
        """
        根据标签获取笔记
        
        Args:
            tag_ids: 标签ID列表
        
        Returns:
            匹配的笔记列表
        """
        return self.get_all({
            'tag_ids': tag_ids,
            'order_by': 'updated_at',
            'order_direction': 'DESC'
        })
    
    def get_recent_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的笔记
        
        Args:
            limit: 数量限制
        
        Returns:
            最近的笔记列表
        """
        return self.get_all({
            'limit': limit,
            'order_by': 'updated_at',
            'order_direction': 'DESC'
        })
    
    def get_notes_count(self) -> int:
        """获取笔记总数"""
        try:
            sql = "SELECT COUNT(*) FROM notes WHERE is_deleted = 0"
            row = self.db.execute_query(sql, fetch='one')
            return row[0] if row else 0
        except Exception as e:
            self.log_error(e, "获取笔记数量失败")
            return 0
    
    def _get_note_tags(self, note_id: int) -> List[Dict[str, Any]]:
        """获取笔记的标签列表"""
        try:
            sql = """
                SELECT t.id, t.name, t.color
                FROM tags t
                JOIN note_tags nt ON t.id = nt.tag_id
                WHERE nt.note_id = ?
                ORDER BY t.name
            """
            rows = self.db.execute_query(sql, (note_id,), fetch='all')
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            self.log_error(e, f"获取笔记标签失败: note_id={note_id}")
            return []
    
    def _add_note_tags(self, note_id: int, tag_ids: List[int]) -> None:
        """为笔记添加标签"""
        if not tag_ids:
            return
        
        try:
            # 准备插入数据
            insert_data = [(note_id, tag_id) for tag_id in tag_ids]
            sql = "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)"
            
            self.db.execute_many(sql, insert_data)
            self.logger.debug(f"为笔记添加标签: note_id={note_id}, tag_ids={tag_ids}")
            
        except Exception as e:
            self.log_error(e, f"添加笔记标签失败: note_id={note_id}")
    
    def _update_note_tags(self, note_id: int, tag_ids: List[int]) -> None:
        """更新笔记的标签"""
        try:
            # 先清除现有标签
            self._clear_note_tags(note_id)
            
            # 添加新标签
            if tag_ids:
                self._add_note_tags(note_id, tag_ids)
            
            self.logger.debug(f"更新笔记标签: note_id={note_id}, tag_ids={tag_ids}")
            
        except Exception as e:
            self.log_error(e, f"更新笔记标签失败: note_id={note_id}")
    
    def _clear_note_tags(self, note_id: int) -> None:
        """清除笔记的所有标签"""
        try:
            sql = "DELETE FROM note_tags WHERE note_id = ?"
            self.db.execute_query(sql, (note_id,), fetch='none')
            self.logger.debug(f"清除笔记标签: note_id={note_id}")
            
        except Exception as e:
            self.log_error(e, f"清除笔记标签失败: note_id={note_id}")
    
    def add_tag_to_note(self, note_id: int, tag_id: int) -> bool:
        """
        为笔记添加单个标签
        
        Args:
            note_id: 笔记ID
            tag_id: 标签ID
        
        Returns:
            添加是否成功
        """
        try:
            # 检查笔记和标签是否存在
            if not self.get_by_id(note_id):
                self.logger.warning(f"笔记不存在: ID={note_id}")
                return False
            
            # 添加标签关联
            sql = "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)"
            affected_rows = self.db.execute_query(sql, (note_id, tag_id), fetch='none')
            
            if affected_rows > 0:
                self.logger.info(f"为笔记添加标签成功: note_id={note_id}, tag_id={tag_id}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.NOTE_TAG_ADDED, {
                    'note_id': note_id,
                    'tag_id': tag_id
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"添加笔记标签失败: note_id={note_id}, tag_id={tag_id}")
            return False
    
    def remove_tag_from_note(self, note_id: int, tag_id: int) -> bool:
        """
        从笔记中移除标签
        
        Args:
            note_id: 笔记ID
            tag_id: 标签ID
        
        Returns:
            移除是否成功
        """
        try:
            sql = "DELETE FROM note_tags WHERE note_id = ? AND tag_id = ?"
            affected_rows = self.db.execute_query(sql, (note_id, tag_id), fetch='none')
            
            if affected_rows > 0:
                self.logger.info(f"从笔记移除标签成功: note_id={note_id}, tag_id={tag_id}")
                
                # 通知观察者
                self.notify_observers(ModelEventType.NOTE_TAG_REMOVED, {
                    'note_id': note_id,
                    'tag_id': tag_id
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.log_error(e, f"移除笔记标签失败: note_id={note_id}, tag_id={tag_id}")
            return False