from . import user
from flask import render_template, request, flash, redirect, url_for
from ..models import User
from flask_login import login_user


@user.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(id=username).first()
            if user:
                if user.verify_password(password):
                    login_user(user)
                    return redirect(url_for('main.hrmanage'))
                else:
                    flash('密码有误！请重新登陆！')
                    return redirect(url_for('user.login'))
            else:
                flash('工号有误！请重新登录！')
                return redirect(url_for('user.login'))
        except:
            flash('登陆信息有误！请重新登录！')
            return redirect(url_for('user.login'))

    else:
        return render_template('user/login.html')

