from . import user
from flask import render_template, request, flash, redirect, url_for, abort
from ..models import User, Department, Position, get_birth_date, db, permit_u, Permission
from flask_login import login_user, current_user, logout_user, login_required
import json

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
        id = request.form.get('id', None, type=int)
        name = request.form.get('n')
        department = request.form.get('d', None, type=int)
        position = request.form.get('p', None, type=int)
        birth = request.form.get('b')
        address = request.form.get('a')
        phone = request.form.get('ph')
        login_permission = request.form.get('l')
        password = request.form.get('password')
        # 开始处理表单信息
        user = User.query.get(id)
        department = Department.query.get(department)
        position = Position.query.get(position)
        if not user or not position:
            res = {'status': 0, 'message': '找不到用户对象！'}
            return json.dumps(res)
        try:
            birth = get_birth_date(birth)
        except:
            flash('您输入的信息有误！')
            return redirect(url_for('user.edit_staff', id=id))
        if login_permission == 'on':
            login_permission = True
        else:
            login_permission = False
        # 检查权限（读）
        # 检查权限（写）
        if not current_user.can(department.permit, position.permit, permit_u.ADD_AND_REMOVE):
            res = {'status': 0, 'message': '权限不足，无法修改！'}
            return json.dumps(res)
        # 开始修改信息

        user.name = name
        user.department = department
        user.position = position
        user.birth = birth
        user.phone = phone
        user.address = address
        user.login_permission = login_permission
        if password:
            user.password = password
        db.session.commit()
        res = {'status': 1, 'message': '工号%s信息修改成功' % user.id}
        return json.dumps(res)
    else:
        id = request.args.get('id', None, type=int)
        u = User.query.get(id)
        if not u:
            abort(404)

        # 检查权限
        if not current_user.can(u.department.permit,u.position.permit,permit_u.ADD_AND_REMOVE):
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


@user.route('/permit')
def permit():
    return render_template('/user/permit.html')


@user.route('/permit/new')
def permit_new():
    return render_template('/user/permit_new.html')


@user.route('/permit/old')
def permit_old():
    permissions = Permission.query.all()

    return render_template('/user/permit_old.html', ps=permissions)


@user.route('/permit/edit_post', methods=['post'])
def permit_edit_post():
    p_id = request.form.get('id', type=int)
    d = json.loads(request.form.get('d'))
    p = json.loads(request.form.get('p'))
    u = request.form.get('u', type=int)
    # 寻找权限
    permission = Permission.query.get(p_id)
    if not permission:
        res = {'status': 0, 'message': '无法找到该权限组！'}
        return json.dumps(res)
    permit_d = 0
    permit_p = 0
    permit_u = u
    for k in d:
        if d[k] == 'true':
            department = Department.query.get(int(k))
            if not department:
                res = {'status': 0, 'message': '提交信息有误！无法找到部门权限！'}
                return json.dumps(res)
            permit_d = permit_d|department.permit




    for k in p:
        if p[k]=='true':
            position = Position.query.get(int(k))
            if not position:
                res = {'status': 0, 'message': '提交信息有误！无法找到职位权限！'}
                return json.dumps(res)
            permit_p = permit_p|position.permit

    permission.permit_p = permit_p
    permission.permit_d = permit_d
    permission.permit_u = permit_u
    db.session.commit()
    res = {'status': 1, 'message': '权限修改成功！'}
    return json.dumps(res)


@user.route('/permit/edit', methods=['post', 'get'])
def permit_edit():

    id = request.args.get('id', None,type=int)
    if not id:
        abort(404)
    permission = Permission.query.get(id)
    ds = Department.query.all()
    ps = Position.query.all()
    # 剔除重复
    t = set()
    ps_2 = []

    for p in ps:
        if not p.name in t:
            ps_2.append(p)
        t.add(p.name)
    return render_template('/user/permit_edit.html', permit=permission, permit_u=permit_u, ds=ds, ps=ps_2)

