from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Post, Comment
from forms import LoginForm, RegistrationForm, ChangePasswordForm, PostForm, CommentForm
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from datetime import datetime
from flask_caching import Cache

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

# 配置缓存
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5分钟缓存
cache = Cache(app)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route("/")
@cache.cached(timeout=300)  # 缓存首页5分钟
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10篇文章
    pagination = Post.query.order_by(desc(Post.timestamp)).paginate(
        page=page, per_page=per_page, error_out=False)
    posts = pagination.items
    return render_template('index.html', posts=posts, pagination=pagination)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('index'))
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
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists. Please choose different ones.')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}')
    return render_template('register.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/profile")
@login_required
def profile():
    form = ChangePasswordForm()
    return render_template('profile.html', form=form)

@app.route("/change-password", methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect')
            return redirect(url_for('profile'))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been updated')
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form)

@app.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        # 清除首页缓存
        cache.delete_memoized(index)
        flash('Your post has been created!')
        return redirect(url_for('post', post_id=post.id))
    return render_template('create_post.html', form=form)

@app.route("/post/<int:post_id>")
@cache.memoize(timeout=300)  # 缓存文章页面5分钟
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条评论
    pagination = post.comments.order_by(desc(Comment.timestamp)).paginate(
        page=page, per_page=per_page, error_out=False)
    comments = pagination.items
    return render_template('post.html', post=post, form=form, 
                         comments=comments, pagination=pagination)

@app.route("/post/<int:post_id>/comment", methods=['POST'])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            display_name=form.display_name.data,
            email=form.email.data,
            post=post
        )
        db.session.add(comment)
        db.session.commit()
        # 清除相关缓存
        cache.delete_memoized(post, post_id)
        flash('Your comment has been added!')
        return redirect(url_for('post', post_id=post.id))
    comments = post.comments.order_by(desc(Comment.timestamp)).all()
    return render_template('post.html', post=post, form=form, comments=comments)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)