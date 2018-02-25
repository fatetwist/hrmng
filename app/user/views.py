from . import user
from flask import render_template, request, flash, redirect, url_for, abort
from ..models import User, Department, Position, get_birth_date, db, permit_abbr
from flask_login import login_user, current_user, logout_user, login_required
import json


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


@user.route('/', methods=['GET'])
@login_required
def logout():
    logout_user(current_user)
    flash('您已全身而退！')
    return redirect(url_for('user.login'))


@user.route('/edit-staff',methods=['POST','GET'])
@login_required
def edit_staff():
    if request.method == 'POST':
        id = request.args.get('id', None, type=int)
        if not id:
            flash('您输入的信息有误！')
            return redirect(url_for('user.edit_staff', id=id))
        name = request.form.get('name')
        department = request.form.get('department')
        position = request.form.get('position')
        birth = request.form.get('birth')
        address = request.form.get('address')
        phone = request.form.get('phone')
        login_permission = request.form.get('login_permission')
        password = request.form.get('password')
        # 开始处理表单信息
        user = User.query.get(id)
        department = Department.query.filter_by(name=department).first()
        position = Position.query.filter_by(name=position).first()
        if not user or not position:
            flash('您输入的信息有误！')
            return redirect(url_for('user.edit_staff', id=id))
        try:
            birth = get_birth_date(birth)
        except:
            flash('您输入的信息有误！')
            return redirect(url_for('user.edit_staff',id=id))
        if login_permission == 'on':
            login_permission = True
        else:
            login_permission = False
        # 检查权限（读）
        if not current_user.verify_permission_by_user(user):
            flash('您的权限不足！')
            return redirect(url_for('user.edit_staff', id=id))
        # 检查权限（写）
        if not current_user.verify_permission_p(permit_abbr[department.abbr]|permit_abbr[position.abbr]):
            flash('您的权限不足！')
            return redirect(url_for('user.edit_staff', id=id))
        # 开始修改信息
        user.name = name
        user.department = department
        user.position = position
        user.birth = birth
        user.phone = phone
        user.address = address
        user.login_permission = login_permission
        user.password = password
        db.session.commit()
        flash('工号%s信息修改成功！' % user.id)
        return redirect(url_for('user.edit_staff', id=id))
    else:
        id = request.args.get('id', None, type=int)
        u = User.query.get(id)
        if not u:
            abort(404)

        # 检查权限
        if not current_user.verify_permission_by_user(u):
            flash('您的权限不足！')
            return redirect(url_for('main.index'))
        return render_template('/user/edit_staff.html', u=u)


@user.route('/change_pssword', methods=['POST', 'GET'])
@login_required
def change_password():
    if not request.method == 'POST':
        return render_template('/user/change_password.html')
    else:
        # post 3个参数  id password new_pass
        u_id = request.form.get('id', type=int)
        password = request.form.get('password')
        verify_res = verify_password_2(u_id, password)
        # 验证旧密码
        if verify_res['status'] != 1:
            res = {'status': 0, 'message': '旧密码错误！'}
            return json.dumps(res)
        # 验证成功 开始 修改密码
        u = User.query.get(u_id)
        new_pass = request.form.get('new_pass')
        u.password = new_pass
        db.session.commit()
        res = {'status': 1, 'message': '密码修改成功！'}
        return json.dumps(res)

@user.route('/verify_pssword',methods=['POST'])
def verify_password():
    u_id = request.form.get('id',type=int)
    password = request.form.get('password')
    res = verify_password_2(u_id, password)
    return json.dumps(res)



def verify_password_2(u_id, password):
    u = User.query.get(u_id)
    if not u:
        res = {'status': 0, 'message': '无法找到用户！'}
        return json.dumps(res)
    if u.verify_password(password):
        res = {'status': 1, 'message': '验证通过！'}
    else:
        res = {'status': 0, 'message': '密码错误！'}

    return res