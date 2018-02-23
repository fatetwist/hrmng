from . import user
from flask import render_template, request, flash, redirect, url_for
from ..models import User
from flask_login import login_user, current_user, logout_user, login_required


@user.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # try:
        # 获取表单信息
        username = request.form['username']
        password = request.form['password']

        # 获得数据库对象
        try:
            user = User.query.filter_by(id=username).first()
        except:
            # 数据库查找出错
            flash('工号有误！请重新登陆！')
            return redirect(url_for('user.login'))

        if user:
            # 开始验证账号密码
            if user.verify_password(password):
                login_user(user)
                return redirect(url_for('main.hrmanage'))
            else:
                flash('密码有误！请重新登陆！')
                return redirect(url_for('user.login'))
        else:
            # 无法找到数据库对象
            flash('工号有误！请重新登陆！')
            return redirect(url_for('user.login'))
        # except:
        #     flash('登陆信息有误！请重新登录！')
        #     return redirect(url_for('user.login'))

    else:
        return render_template('user/login.html')


@login_required
@user.route('/', methods=['GET'])
def logout():
    logout_user(current_user)
    flash('您已退出登陆！')
    return redirect(url_for('user.login'))