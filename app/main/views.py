from . import main
from flask import redirect, url_for, render_template, request, flash, abort
from flask_login import login_required, current_user
from ..models import Department, User,  permit_u,  Position, get_birth_date
from ..decorators import admin_required
import json
from datetime import date
from .. import db
import xlrd
import os
import hashlib
import base64
import random
import shutil
import platform


'''
sha1 file with filename (SHA1)
'''


def calculate_sha1(f, block_size=64 * 1024):
    sha1 = hashlib.sha1()
    while True:
        data = f.read(block_size)
        if not data:
            break
        sha1.update(data)
    retsha1 = base64.b64encode(sha1.digest())
    return retsha1


def md5sum(fd):

    fcont = fd.r
    fd.close()
    fmd5 = hashlib.md5(fcont)
    return fmd5


@main.route('/')
@login_required
def index():
    return redirect(url_for('main.hrmanage'))


@main.route('/hrmanage')
@login_required
def hrmanage():
    return render_template('main/index.html')


@main.route('/hrmanage/<department>')
@login_required
def dp_staff(department):
    d = Department.query.filter_by(abbr=department).first()
    if not d:
        abort(404)
    if not current_user.can(d.permit):
        flash('您的权限不足！')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    # 获得筛选信息
    name = request.args.get('u_name', None)
    id = request.args.get('u_id',None,type=int)
    old_start = request.args.get('old_start',None,type=int)
    old_over = request.args.get('old_over', None, type=int)
    # 开始查找数据库
    query = User.query.filter_by(department=d)
    # 开始处理筛选
    if id:
        query = query.filter(User.id==id)
    if name:
        query = query.filter(User.name==name)
    if old_start and old_over:
        query = query.filter(User.old>=old_start,User.old<=old_over)

    pagination = query.paginate(page, per_page=per_page,error_out=False)
    p_users = pagination.items
    return render_template('/main/dp_staff.html', dp_staff=p_users, pagination=pagination, depart=d, permit_u=permit_u, per_page=per_page)


@main.route('/batch_staff/getdepartandposition')
def getdp():
    ds = Department.query.all()
    positions = []
    for x in ds:
        ps = x.positions
        p = []
        for y in ps:
            p_dict = {}
            p_dict['name'] = y.name
            p_dict['id'] = y.id
            p.append(p_dict)
        t = {'id': x.id, 'name':x.name, 'position':p}
        positions.append(t)
    return json.dumps(positions)


@main.route('/batch_staff')
@login_required
def batch_staff():
    return render_template('main/batch_staff.html')


@main.route('/add-to-sql',methods=['POST'])
@login_required
def add_to_sql():
    json_list = request.form.get('json_list')
    list = json.loads(json_list)
    success_num = 0
    for x in list:
        name = x['n']
        print(x['d'])
        department = int(x['d'])
        position = int(x['p'])
        address = x['a']
        phone = x['ph']
        birth = x['b']
        # 处理出生日期
        try:
            birth = get_birth_date(birth)
        except:
            birth = date(2018, 1, 1)
        department = Department.query.get(department)
        if not department:
            continue

        # 获取职位
        position = Position.query.get(position)
        if not position:
            continue
        # 权限验证
        if not current_user.can(department.permit, position.permit, permit_u.ADD_AND_REMOVE):
            continue
        else:
            u = User(name=name, department=department, position=position, address=address, phone=phone, birth=birth)
            db.session.add(u)
            success_num += 1

    db.session.commit()
    res = {'status': 1, 'success': success_num, 'false': len(list)-success_num, 'message': '提交成功！'}
    return json.dumps(res)


@main.route('/add-to-sql-by-excel', methods=['POST'])
@login_required
def add_to_sql_by_excel():
    file_excel = request.files['file-excel']
    if platform.system()=='Windows':
        # windows系统
        filename = os.path.join(os.getcwd()+'\\app\\static\\temp\\', str(random.random())[2:])  # 如果是linux需要修改
    else:
        # 其他系统
        filename = os.path.join(os.getcwd()+'/app/static/temp', str(random.random())[2:])

    file_excel.save(filename)
    data = xlrd.open_workbook(filename)
    table = data.sheets()[0]
    nrows = table.nrows
    # ncols = table.ncols
    success_num = 0
    user_list = []

    for x in range(1, nrows):

        rowvalues = table.row_values(x)
        name = rowvalues[0]
        department = rowvalues[1]
        position = rowvalues[2]
        address = rowvalues[3]
        phone = rowvalues[4]
        birth = rowvalues[5]
        birth = xlrd.xldate_as_datetime(birth, 0).date()

        try:
            department = Department.query.filter_by(name=department).first()
            if not department:
                department = Department.query.filter_by(name='生产部').first()
        except:
            department = Department.query.filter_by(name='生产部').first()

        # 获取职位
        try:
            position = Position.query.filter_by(name=position).first()
            if not position:
                position = Position.query.filter_by(name='员工').filter_by(department=department).first()
        except:
            position = Position.query.filter_by(name='员工').filter_by(department=department).first()

        # 权限验证
        if not current_user.can(department.permit, position.permit, permit_u.ADD_AND_REMOVE):
            continue
        else:
            u = User(name=name, department=department, position=position, address=address, phone=phone, birth=birth)
            db.session.add(u)
            success_num += 1
            res_dict = {
                'name': name,
                'department': department.name,
                'position': position.name,
                'address': address,
                'phone': phone,
                'birth': str(birth).replace('-', '/')
            }
            user_list.append(res_dict)

    db.session.commit()
    shutil.rmtree(os.path.dirname(filename))
    os.mkdir(os.path.dirname(filename))

    res_json = {
        'status': 1,
        'success': success_num,
        'error': nrows-1-success_num,
        'user_list': user_list
    }
    return json.dumps(res_json)


@main.route('/remove_staff', methods=['POST'])
@login_required
def remove_staff():
    u_id = int(request.form.get('id'))
    u = User.query.get(u_id)
    department = u.department
    position = u.position
    # 权限检查
    if not current_user.can(department.permit, position.permit, permit_u.ADD_AND_REMOVE):
        return json.dumps({'status': 0, 'message': '权限不足！'})

    # 开始删除
    db.session.delete(u)
    db.session.commit()
    return json.dumps({'status': 1, 'message': '操作成功！'})


@main.route('/edit-staff/<int:id>')
@login_required
def edit_staff(id):
    u = User.query.get(id)

    if not u:
        abort(404)

    # 检查权限
    current_user.verify_permission_by_user(u)
    return render_template('edit_staff.html', user=u)


@main.route('/options')
@admin_required
def options():
    return render_template('main/options.html')


