#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序测试脚本
验证各个组件是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加src目录到路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """测试所有主要模块的导入"""
    try:
        print("测试模块导入...")
        
        # 测试工具类导入
        from utils.config_manager import ConfigManager
        from utils.logger import setup_logger
        print("✓ 工具类导入成功")
        
        # 测试模型导入
        from models.database_model import DatabaseManager
        from models.note_model import NoteModel
        from models.tag_model import TagModel
        from models.settings_model import SettingsModel
        print("✓ 模型类导入成功")
        
        # 测试控制器导入
        from controllers.base_controller import BaseController
        from controllers.note_controller import NoteController
        from controllers.tag_controller import TagController
        print("✓ 控制器类导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False

def test_database():
    """测试数据库功能"""
    try:
        print("\n测试数据库功能...")
        
        from models.database_model import DatabaseManager
        
        # 创建测试数据库
        test_db_path = project_root / "test_notes.db"
        if test_db_path.exists():
            test_db_path.unlink()  # 删除现有测试数据库
        
        db_manager = DatabaseManager(str(test_db_path))
        db_manager.initialize_database()
        
        # 测试数据库信息
        db_info = db_manager.get_database_info()
        print(f"✓ 数据库创建成功，表数量: {len(db_info.get('tables', []))}")
        
        db_manager.close()
        
        # 清理测试文件
        if test_db_path.exists():
            test_db_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False

def test_models():
    """测试模型功能"""
    try:
        print("\n测试模型功能...")
        
        from models.database_model import DatabaseManager
        from models.note_model import NoteModel
        from models.tag_model import TagModel
        
        # 创建测试数据库
        test_db_path = project_root / "test_notes.db"
        if test_db_path.exists():
            test_db_path.unlink()
        
        db_manager = DatabaseManager(str(test_db_path))
        db_manager.initialize_database()
        
        # 测试标签模型
        tag_model = TagModel(db_manager)
        tag_id = tag_model.create({'name': '测试标签', 'color': '#007ACC'})
        if tag_id:
            print("✓ 标签创建成功")
        else:
            print("✗ 标签创建失败")
            return False
        
        # 测试笔记模型
        note_model = NoteModel(db_manager)
        note_id = note_model.create({
            'title': '测试笔记',
            'content': '这是一条测试笔记',
            'tag_ids': [tag_id]
        })
        if note_id:
            print("✓ 笔记创建成功")
        else:
            print("✗ 笔记创建失败")
            return False
        
        # 测试查询功能
        note = note_model.get_by_id(note_id)
        if note and note['title'] == '测试笔记':
            print("✓ 笔记查询成功")
        else:
            print("✗ 笔记查询失败")
            return False
        
        db_manager.close()
        
        # 清理测试文件
        if test_db_path.exists():
            test_db_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ 模型测试失败: {e}")
        return False

def test_config():
    """测试配置管理"""
    try:
        print("\n测试配置管理...")
        
        from utils.config_manager import ConfigManager
        
        config = ConfigManager()
        
        # 测试读取配置
        app_name = config.get('app', 'name', '默认名称')
        print(f"✓ 配置读取成功: {app_name}")
        
        # 测试设置配置
        config.set('test', 'value', 'test_value')
        value = config.get('test', 'value')
        if value == 'test_value':
            print("✓ 配置设置成功")
        else:
            print("✗ 配置设置失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("轻量级Windows桌面笔记管理软件 - 组件测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理", test_config),
        ("数据库功能", test_database),
        ("模型功能", test_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✓ {name} 测试通过")
        else:
            print(f"✗ {name} 测试失败")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用程序组件工作正常。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关组件。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)