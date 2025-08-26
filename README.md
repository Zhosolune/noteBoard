# 轻量级Windows桌面笔记管理软件

一款基于PySide6和PyQt-Fluent-Widgets的现代化笔记管理应用。

## ✨ 特性

- 🎨 **现代化UI**: 基于Fluent Design的精美界面
- 📝 **笔记管理**: 创建、编辑、删除、搜索笔记
- 🏷️ **标签系统**: 灵活的标签分类管理
- 🖱️ **边缘唤起**: 鼠标移至屏幕边缘自动显示
- 📌 **窗口置顶**: 支持固定在屏幕最上层
- 🔍 **全文搜索**: 快速查找笔记内容
- 💾 **本地存储**: 使用SQLite本地数据库
- 🚀 **轻量级**: 启动快速，资源占用小

## 🏗️ 架构设计

项目采用经典的MVC (Model-View-Controller) 架构模式：

```
src/
├── models/          # 数据模型层
│   ├── base_model.py
│   ├── note_model.py
│   ├── tag_model.py
│   └── database_model.py
├── views/           # 视图层
│   ├── main_window.py
│   ├── note_interface.py
│   ├── tag_interface.py
│   └── search_interface.py
├── controllers/     # 控制器层
│   ├── base_controller.py
│   ├── main_controller.py
│   ├── note_controller.py
│   └── window_controller.py
└── utils/          # 工具类
    ├── config_manager.py
    └── logger.py
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows 10/11
- 2GB+ RAM
- 100MB+ 磁盘空间

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

## 📦 技术栈

| 组件 | 技术选择 | 版本要求 |
|------|---------|---------|
| GUI框架 | PySide6 | ≥6.5.0 |
| UI组件库 | PyQt-Fluent-Widgets | 最新版 |
| 数据库 | SQLite | Python内置 |
| 系统集成 | pynput | ≥1.7.6 |
| 日志记录 | loguru | ≥0.7.0 |
| 打包工具 | PyInstaller | ≥5.13.0 |

## 🎯 核心功能

### 笔记管理
- ✅ 创建新笔记
- ✅ 编辑笔记内容
- ✅ 删除笔记（软删除）
- ✅ 笔记列表显示
- ✅ 笔记详情查看

### 标签系统
- ✅ 创建标签
- ✅ 为笔记添加标签
- ✅ 标签颜色设置
- ✅ 按标签筛选笔记

### 窗口管理
- ✅ 边缘隐藏功能
- ✅ 鼠标唤起机制
- ✅ 窗口置顶模式
- ✅ 多显示器支持

### 搜索功能
- ✅ 全文搜索
- ✅ 标签筛选
- ✅ 搜索结果高亮
- ✅ 模糊搜索

## 🔧 配置说明

配置文件: `config.ini`

```ini
[window]
default_width = 1200
default_height = 800
edge_trigger_width = 5
hide_delay_ms = 2000

[ui]
theme = auto
language = zh_CN

[features]
auto_save = true
auto_save_interval = 30
```

## 🧪 测试

运行单元测试:
```bash
pytest src/tests/
```

运行覆盖率测试:
```bash
pytest --cov=src src/tests/
```

## 📦 打包发布

使用PyInstaller打包为exe文件:
```bash
pyinstaller --windowed --onefile --name="轻量笔记管理器" main.py
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者

**Kiro** - [GitHub](https://github.com/kiro)

## 🙏 致谢

- [PySide6](https://wiki.qt.io/Qt_for_Python) - 强大的GUI框架
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - 精美的Fluent Design组件库
- [loguru](https://github.com/Delgan/loguru) - 优雅的Python日志库