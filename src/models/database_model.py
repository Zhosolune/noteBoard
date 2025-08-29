#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器
负责SQLite数据库的连接、初始化和操作
"""

import sqlite3
import threading
from pathlib import Path
from typing import Any, List, Optional, Tuple, Dict, Union
from contextlib import contextmanager

from src.utils.logger import LoggerMixin


class DatabaseManager(LoggerMixin):
    """数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为项目根目录下的notes.db
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "notes.db"
        
        self.db_path = Path(db_path)
        self._local = threading.local()  # 线程本地存储
        self._initialized = False
        
        # 确保数据库目录存在
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.logger.info(f"数据库路径: {self.db_path}")
    
    @property
    def connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = self._create_connection()
        return self._local.connection
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建数据库连接"""
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            
            # 设置连接选项
            conn.row_factory = sqlite3.Row  # 支持字典式访问
            conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
            conn.execute("PRAGMA journal_mode = WAL")  # 使用WAL模式
            conn.execute("PRAGMA synchronous = NORMAL")  # 设置同步模式
            
            self.logger.debug("数据库连接创建成功")
            return conn
        
        except sqlite3.Error as e:
            self.logger.error(f"创建数据库连接失败: {e}")
            raise
    
    def initialize_database(self) -> None:
        """初始化数据库表结构"""
        if self._initialized:
            return
        
        try:
            self.logger.info("开始初始化数据库表结构")
            
            with self.get_cursor() as cursor:
                # 创建笔记表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT DEFAULT '',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_deleted INTEGER DEFAULT 0
                    )
                """)
                
                # 创建标签表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        color TEXT DEFAULT '#007ACC',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建笔记标签关联表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS note_tags (
                        note_id INTEGER,
                        tag_id INTEGER,
                        PRIMARY KEY (note_id, tag_id),
                        FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE,
                        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建设置表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建索引
                self._create_indexes(cursor)
                
            self._initialized = True
            self.logger.info("数据库初始化完成")
            
        except sqlite3.Error as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)",
            "CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notes_is_deleted ON notes(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)",
            "CREATE INDEX IF NOT EXISTS idx_note_tags_note_id ON note_tags(note_id)",
            "CREATE INDEX IF NOT EXISTS idx_note_tags_tag_id ON note_tags(tag_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """
        获取数据库游标上下文管理器
        
        Args:
            commit: 是否自动提交事务
        
        Yields:
            sqlite3.Cursor: 数据库游标
        """
        cursor = self.connection.cursor()
        try:
            yield cursor
            if commit:
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(
        self, 
        sql: str, 
        params: Optional[Union[Tuple, Dict]] = None, 
        fetch: str = 'all'
    ) -> Optional[Union[List[sqlite3.Row], sqlite3.Row, int]]:
        """
        执行SQL查询
        
        Args:
            sql: SQL语句
            params: 参数
            fetch: 获取模式 ('all', 'one', 'none', 'lastrowid')
        
        Returns:
            查询结果
        """
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                if fetch == 'all':
                    return cursor.fetchall()
                elif fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'none':
                    return cursor.rowcount
                elif fetch == 'lastrowid':
                    return cursor.lastrowid
                else:
                    return None
                    
        except sqlite3.Error as e:
            self.logger.error(f"执行SQL查询失败: {sql}, 错误: {e}")
            raise
    
    def execute_many(self, sql: str, params_list: List[Union[Tuple, Dict]]) -> int:
        """
        批量执行SQL语句
        
        Args:
            sql: SQL语句
            params_list: 参数列表
        
        Returns:
            影响的行数
        """
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(sql, params_list)
                return cursor.rowcount
                
        except sqlite3.Error as e:
            self.logger.error(f"批量执行SQL失败: {sql}, 错误: {e}")
            raise
    
    def get_last_insert_rowid(self) -> int:
        """获取最后插入的行ID"""
        # SQLite的lastrowid在cursor执行后可用
        # 我们需要从最近的cursor获取
        cursor = self.connection.cursor()
        return cursor.lastrowid if cursor.lastrowid else 0
    
    def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            备份是否成功
        """
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(exist_ok=True)
            
            # 创建备份连接
            with sqlite3.connect(str(backup_path)) as backup_conn:
                self.connection.backup(backup_conn)
            
            self.logger.info(f"数据库备份成功: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库备份失败: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            with self.get_cursor(commit=False) as cursor:
                # 获取表信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # 获取数据库大小
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                # 获取记录数量
                record_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    record_counts[table] = cursor.fetchone()[0]
                
                return {
                    'database_path': str(self.db_path),
                    'database_size': db_size,
                    'tables': tables,
                    'record_counts': record_counts
                }
                
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return {}
    
    def close(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
                delattr(self._local, 'connection')
                self.logger.debug("数据库连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭数据库连接失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()