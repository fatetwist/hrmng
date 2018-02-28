from . import user
from flask import render_template, request, flash, redirect, url_for, abort
from ..models import User, Department, Position, get_birth_date, db, permit_u, Permission, Evaluation
from flask_login import login_user, current_user, logout_user, login_required
import json
from datetime import date
from ..decorators import admin_required


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


@user.route('/')
def index():
    return redirect(url_for('login'))


@user.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # try:
        # 获取表单信息
        username = request.form['username']
        password = request.form['password']

        # 获得数据库对象

        user = User.query.filter_by(id=username).first()
        # 数据库查找出错
        if not user:
            flash('工号有误！请重新登陆！')
            return redirect(url_for('user.login'))

        if user:
            if not user.password_hash:
                flash('该账号未设置密码，禁止登陆！')
                return redirect(url_for('user.login'))
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


@user.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('您已全身而退！')
    return redirect(url_for('user.login'))


@user.route('/edit-staff',methods=['POST','GET'])
@login_required
def edit_staff():
    if request.method == 'POST':
        # 获取表单信息
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
        if login_permission == '1':
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
        # 管理员修改权限

        if current_user.is_admin():
            permissions = json.loads(request.form.get('permissions'))
            print(permissions)
            user.clear_permissions()

            for i in permissions:
                p = Permission.query.get(int(i))
                # 检查重复
                if p in user.permissions:
                    continue
                # 添加权限
                user.permissions.append(p)

        # 修改密码
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
        # 获取权限对象
        ps = Permission.query.all()

        return render_template('/user/edit_staff.html', u=u, ps=ps)


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
@admin_required
def permit():

    return render_template('/user/permit.html')


@user.route('/permit/new')
@admin_required
def permit_new():
    ds = Department.query.all()
    # 获得position
    ps = Position.query.all()
    # 剔除重复
    t = set()
    ps_2 = []
    for p in ps:
        if not p.name in t:
            ps_2.append(p)
        t.add(p.name)

    return render_template('/user/permit_new.html', ds=ds, ps=ps_2, permit_u=permit_u)


@user.route('/permit/new_post', methods=['post'])
@admin_required
def permit_new_post():
    name = request.form.get('name')
    d = json.loads(request.form.get('d'))
    p = json.loads(request.form.get('p'))
    u = request.form.get('u', type=int)

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

    # 开始创建permission
    p_new = Permission(name=name, permit_d=permit_d,permit_p=permit_p,permit_u=permit_u)
    db.session.add(p_new)
    db.session.commit()
    res = {'status': 1, 'message': '新的权限创建成功！'}
    return json.dumps(res)


@user.route('/permit/old')
@admin_required
def permit_old():
    ps = Permission.query.all()

    return render_template('/user/permit_old.html', ps=ps)


@user.route('/permit/delete', methods=['post'])
@admin_required
def permit_delete():
    p_id = request.form.get('p_id')
    p = Permission.query.get(p_id)
    if not p:
        res = {'status': 0, 'message': '没有找到该权限组！'}
        return json.dumps(res)
    db.session.delete(p)
    db.session.commit()
    res = {'status': 1, 'message': '删除成功！'}
    return json.dumps(res)


@user.route('/permit/edit_post', methods=['post'])
@admin_required
@login_required
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


@user.route('/permit/edit')
@admin_required
@login_required
def permit_edit():
    id = request.args.get('id', None,type=int)
    if not id:
        abort(404)
    permission = Permission.query.get(id)
    ds = Department.query.all()
    # 获得position
    ps = Position.query.all()
    # 剔除重复
    t = set()
    ps_2 = []
    for p in ps:
        if not p.name in t:
            ps_2.append(p)
        t.add(p.name)
    return render_template('/user/permit_edit.html', permit=permission, permit_u=permit_u, ds=ds, ps=ps_2)


@user.route('/permit/has_permit', methods=['get'])
@admin_required
@login_required
def has_permit():
    permit_id = request.args.get('permit_id', None, type=int)
    if not permit_id:
        abort(404)
    # 查找数据库permissions
    p = Permission.query.get(permit_id)
    if not p:
        abort(404)
    return render_template('user/has_permit_user.html', p=p)



@user.route('/evaluate', methods=['POST', 'GET'])
@login_required
def evaluate():
    if request.method == 'POST':
        # 获取表单信息
        u_id = request.form.get('id', type=int)
        rank = request.form.get('rank', type=int)
        remark = request.form.get('remark')
        # 寻找用户
        u = User.query.get(u_id)
        if not u_id:
            res = {'status': 0, 'message': '没有找到用户！'}
            return json.dumps(res)
        # 验证本月是否评价
        es = u.evaluations
        t = date.today()
        for e in es:
            d = e.date
            if d.year == t.year and d.month == t.month:
                res = {'status': 0, 'message': '本月已经评价过！'}
                return json.dumps(res)

        # 处理数据并提交到数据库
        d = date.today()
        e = Evaluation(rank=rank, remark=remark, user=u, date=d)
        db.session.add(e)
        db.session.commit()
        res = {'status': 1, 'message': '提交成功！'}
        return json.dumps(res)


    else:
        u_id = request.args.get('id', None, type=int)
        if not u_id:
            abort(404)
        u = User.query.get(u_id)
        if not u:
            abort(404)
        es = u.evaluations
        t = date.today()
        m = ''
        for e in es:
            d = e.date
            if d.year == t.year and d.month == t.month:
                m = '本月已评价过'
        if not m:
            m = t.strftime('%Y-%m')
        return render_template('user/evaluate.html', es=es, m=m, u=u)


@user.route('/evaluation', methods=['post'])
@login_required
def evaluation():
    e_id = request.form.get('id', type=int)
    e = Evaluation.query.get(e_id)
    if not e:
        res = {'status': 0, 'message': '无法找到该评价！'}
        return json.dumps(res)
    res = {'status': 1, 'message': '获取成功！', 'data': {'rank': e.rank, 'remark': e.remark}}
    return json.dumps(res)


