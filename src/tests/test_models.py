#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试套件
使用pytest测试框架对核心功能进行测试
"""

import pytest
import tempfile
import os

from src.models.database_model import DatabaseManager
from src.models.note_model import NoteModel
from src.models.tag_model import TagModel
from src.models.settings_model import SettingsModel


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    yield db_manager
    
    db_manager.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestDatabaseManager:
    """测试数据库管理器"""
    
    def test_database_initialization(self, temp_db):
        """测试数据库初始化"""
        db_info = temp_db.get_database_info()
        assert 'tables' in db_info
        assert len(db_info['tables']) >= 4  # notes, tags, note_tags, settings
    
    def test_execute_query(self, temp_db):
        """测试SQL查询执行"""
        result = temp_db.execute_query("SELECT 1 as test", fetch='one')
        assert result['test'] == 1


class TestTagModel:
    """测试标签模型"""
    
    def test_create_tag(self, temp_db):
        """测试创建标签"""
        tag_model = TagModel(temp_db)
        
        tag_id = tag_model.create({
            'name': '测试标签',
            'color': '#007ACC'
        })
        
        assert tag_id is not None
        assert tag_id > 0
    
    def test_get_tag_by_id(self, temp_db):
        """测试根据ID获取标签"""
        tag_model = TagModel(temp_db)
        
        # 创建标签
        tag_id = tag_model.create({
            'name': '测试标签2',
            'color': '#28A745'
        })
        
        # 获取标签
        tag = tag_model.get_by_id(tag_id)
        assert tag is not None
        assert tag['name'] == '测试标签2'
        assert tag['color'] == '#28A745'
    
    def test_update_tag(self, temp_db):
        """测试更新标签"""
        tag_model = TagModel(temp_db)
        
        # 创建标签
        tag_id = tag_model.create({
            'name': '原标签名',
            'color': '#007ACC'
        })
        
        # 更新标签
        success = tag_model.update(tag_id, {
            'name': '新标签名',
            'color': '#DC3545'
        })
        
        assert success is True
        
        # 验证更新
        tag = tag_model.get_by_id(tag_id)
        assert tag['name'] == '新标签名'
        assert tag['color'] == '#DC3545'
    
    def test_delete_tag(self, temp_db):
        """测试删除标签"""
        tag_model = TagModel(temp_db)
        
        # 创建标签
        tag_id = tag_model.create({
            'name': '待删除标签',
            'color': '#FFC107'
        })
        
        # 删除标签
        success = tag_model.delete(tag_id)
        assert success is True
        
        # 验证删除
        tag = tag_model.get_by_id(tag_id)
        assert tag is None


class TestNoteModel:
    """测试笔记模型"""
    
    def test_create_note(self, temp_db):
        """测试创建笔记"""
        note_model = NoteModel(temp_db)
        
        note_id = note_model.create({
            'title': '测试笔记',
            'content': '这是测试内容'
        })
        
        assert note_id is not None
        assert note_id > 0
    
    def test_get_note_by_id(self, temp_db):
        """测试根据ID获取笔记"""
        note_model = NoteModel(temp_db)
        
        # 创建笔记
        note_id = note_model.create({
            'title': '测试笔记2',
            'content': '测试内容2'
        })
        
        # 获取笔记
        note = note_model.get_by_id(note_id)
        assert note is not None
        assert note['title'] == '测试笔记2'
        assert note['content'] == '测试内容2'
    
    def test_update_note(self, temp_db):
        """测试更新笔记"""
        note_model = NoteModel(temp_db)
        
        # 创建笔记
        note_id = note_model.create({
            'title': '原标题',
            'content': '原内容'
        })
        
        # 更新笔记
        success = note_model.update(note_id, {
            'title': '新标题',
            'content': '新内容'
        })
        
        assert success is True
        
        # 验证更新
        note = note_model.get_by_id(note_id)
        assert note['title'] == '新标题'
        assert note['content'] == '新内容'
    
    def test_note_with_tags(self, temp_db):
        """测试笔记与标签关联"""
        note_model = NoteModel(temp_db)
        tag_model = TagModel(temp_db)
        
        # 创建标签
        tag_id = tag_model.create({
            'name': '测试标签',
            'color': '#007ACC'
        })
        
        # 创建带标签的笔记
        note_id = note_model.create({
            'title': '带标签的笔记',
            'content': '内容',
            'tag_ids': [tag_id]
        })
        
        # 验证标签关联
        note = note_model.get_by_id(note_id)
        assert len(note['tags']) == 1
        assert note['tags'][0]['name'] == '测试标签'
    
    def test_search_notes(self, temp_db):
        """测试搜索笔记"""
        note_model = NoteModel(temp_db)
        
        # 创建多条笔记
        note_model.create({
            'title': 'Python学习笔记',
            'content': 'Python是一门编程语言'
        })
        
        note_model.create({
            'title': 'Java学习笔记', 
            'content': 'Java也是一门编程语言'
        })
        
        # 搜索包含Python的笔记
        results = note_model.search('Python')
        assert len(results) == 1
        assert 'Python' in results[0]['title']
        
        # 搜索包含编程语言的笔记
        results = note_model.search('编程语言')
        assert len(results) == 2


class TestSettingsModel:
    """测试设置模型"""
    
    def test_set_and_get_setting(self, temp_db):
        """测试设置和获取配置"""
        settings_model = SettingsModel(temp_db)
        
        # 设置配置
        success = settings_model.set_setting('test_key', 'test_value')
        assert success is True
        
        # 获取配置
        value = settings_model.get_setting('test_key')
        assert value == 'test_value'
    
    def test_boolean_setting(self, temp_db):
        """测试布尔类型设置"""
        settings_model = SettingsModel(temp_db)
        
        # 设置布尔值
        settings_model.set_setting('bool_key', True)
        value = settings_model.get_setting('bool_key')
        assert value is True
        
        # 设置False
        settings_model.set_setting('bool_key', False)
        value = settings_model.get_setting('bool_key')
        assert value is False
    
    def test_number_setting(self, temp_db):
        """测试数值类型设置"""
        settings_model = SettingsModel(temp_db)
        
        # 整数
        settings_model.set_setting('int_key', 123)
        value = settings_model.get_setting('int_key')
        assert value == 123
        
        # 浮点数
        settings_model.set_setting('float_key', 123.45)
        value = settings_model.get_setting('float_key')
        assert value == 123.45


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])