# Flask Blog

一个基于 Flask 的博客系统，具有以下功能：

- 用户注册和登录
- 文章发布和管理
- 评论系统
- 用户头像（基于 Gravatar）
- 文章浏览量统计
- 响应式设计

## 功能特点

- 用户认证系统
- 文章管理
- 评论系统
- 用户头像
- 文章浏览量统计
- 响应式布局
- 错误处理页面
- 分页功能

## 技术栈

- Python 3.x
- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Bootstrap 5
- Gravatar

## 安装和运行

1. 克隆仓库：
```bash
git clone [repository-url]
cd flasky
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 初始化数据库：
```bash
python init_db.py
```

5. 运行应用：
```bash
flask run --port=5001
```

访问 http://localhost:5001 即可使用。

## 项目结构

```
flasky/
├── app.py              # 主应用文件
├── models.py           # 数据模型
├── forms.py            # 表单类
├── init_db.py          # 数据库初始化脚本
├── requirements.txt    # 项目依赖
├── instance/          # 实例文件夹
│   └── app.db        # SQLite 数据库
└── templates/         # 模板文件夹
    ├── base.html     # 基础模板
    ├── index.html    # 首页模板
    ├── login.html    # 登录页面
    ├── register.html # 注册页面
    ├── post.html     # 文章页面
    ├── 404.html      # 404错误页面
    └── 500.html      # 500错误页面
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License 