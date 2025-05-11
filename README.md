# AI Blog

一个使用 Flask 框架开发的现代化博客系统。

## 功能特点

- 用户认证（注册、登录、登出）
- 文章管理（创建、查看）
- 评论系统
- 响应式设计
- 分页功能
- 缓存支持

## 技术栈

- Python 3.11
- Flask 2.2.5
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Caching
- Bootstrap 5
- SQLite

## 安装说明

1. 克隆仓库：
```bash
git clone https://github.com/yutiepi/AI-blog.git
cd AI-blog
```

2. 创建并激活虚拟环境：
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
flask run
```

## 使用说明

1. 访问 http://localhost:5000 查看博客首页
2. 注册新用户或使用现有账号登录
3. 登录后可以创建新文章
4. 在文章页面可以查看和发表评论

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License 