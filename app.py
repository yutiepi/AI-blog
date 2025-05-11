from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Post, Comment
from forms import LoginForm, RegistrationForm, ChangePasswordForm, PostForm, CommentForm
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from datetime import datetime
from flask_caching import Cache
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# 使用绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 添加数据库连接池配置
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置缓存
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5分钟缓存
cache = Cache(app)

# 添加自定义过滤器
@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return s.replace('\n', '<br>')

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(id):
    try:
        return User.query.get(int(id))
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

@app.route("/")
def index():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10  # 每页显示10篇文章
        pagination = Post.query.order_by(desc(Post.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False)
        posts = pagination.items
        return render_template('index.html', posts=posts, pagination=pagination)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash('加载页面时发生错误，请稍后重试', 'error')
        return render_template('index.html', posts=[], pagination=None)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('用户名或密码错误', 'error')
                return redirect(url_for('login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            flash('登录成功！', 'success')
            return redirect(next_page)
        except Exception as e:
            logger.error(f"Error in login route: {str(e)}")
            flash('登录时发生错误，请稍后重试', 'error')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录！', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('用户名或邮箱已存在，请选择其他。', 'error')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in register route: {str(e)}")
            flash('注册时发生错误，请稍后重试', 'error')
    return render_template('register.html', form=form)

@app.route("/logout")
@login_required
def logout():
    try:
        logout_user()
        flash('已成功退出登录', 'success')
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        flash('退出登录时发生错误', 'error')
    return redirect(url_for('index'))

@app.route("/profile")
@login_required
def profile():
    try:
        form = ChangePasswordForm()
        return render_template('profile.html', form=form)
    except Exception as e:
        logger.error(f"Error in profile route: {str(e)}")
        flash('加载个人资料时发生错误', 'error')
        return redirect(url_for('index'))

@app.route("/change-password", methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            if not current_user.check_password(form.current_password.data):
                flash('当前密码错误', 'error')
                return redirect(url_for('profile'))
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('密码已更新', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in change_password route: {str(e)}")
            flash('更改密码时发生错误', 'error')
    return render_template('profile.html', form=form)

@app.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        try:
            post = Post(title=form.title.data, content=form.content.data, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('文章已发布！', 'success')
            return redirect(url_for('post', post_id=post.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in create_post route: {str(e)}")
            flash('发布文章时发生错误', 'error')
    return render_template('create_post.html', form=form)

@app.route("/post/<int:post_id>")
def post(post_id):
    try:
        post = Post.query.get_or_404(post_id)
        # 增加浏览量
        post.views += 1
        db.session.commit()
        
        form = CommentForm()
        page = request.args.get('page', 1, type=int)
        per_page = 10
        pagination = post.comments.order_by(desc(Comment.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False)
        comments = pagination.items
        return render_template('post.html', post=post, form=form, 
                             comments=comments, pagination=pagination)
    except Exception as e:
        logger.error(f"Error in post route: {str(e)}")
        flash('加载文章时发生错误', 'error')
        return redirect(url_for('index'))

@app.route("/post/<int:post_id>/comment", methods=['POST'])
def add_comment(post_id):
    try:
        post = Post.query.get_or_404(post_id)
        form = CommentForm()
        if form.validate_on_submit():
            try:
                comment = Comment(
                    content=form.content.data,
                    display_name=form.display_name.data,
                    email=form.email.data,
                    post=post,
                    timestamp=datetime.utcnow()
                )
                db.session.add(comment)
                db.session.commit()
                flash('评论已成功添加！', 'success')
                return redirect(url_for('post', post_id=post.id))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error adding comment: {str(e)}")
                flash('添加评论时发生错误，请稍后重试。', 'error')
                return redirect(url_for('post', post_id=post.id))
        
        # 如果表单验证失败，显示错误信息
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
        
        # 获取评论列表
        page = request.args.get('page', 1, type=int)
        per_page = 10
        pagination = post.comments.order_by(desc(Comment.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False)
        comments = pagination.items
        
        return render_template('post.html', post=post, form=form, 
                             comments=comments, pagination=pagination)
    except Exception as e:
        logger.error(f"Error in add_comment route: {str(e)}")
        flash('处理评论时发生错误', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)