from . import main
from flask import redirect, url_for, render_template, request, flash, abort
from flask_login import login_required, current_user
from ..models import Department, User, permit_abbr, permission_o, default_position, Position, get_birth_date
import json
from datetime import date
from .. import db
import xlrd
import os
import hashlib
import base64
import random

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
    # dp_permit = {
    #     'hr': ,
    #     'sale': default_permission['销售部门管理'][0],
    #     'director': default_permission['管理员'][0],
    #     'manager': default_permission['总经理部门管理'][0],
    #     'finance': default_permission['财务部门管理'][0],
    #     'product': default_permission['生产部门管理'][0],
    #     'logistics': default_permission['后勤部门管理'][0],
    #     'purchase': default_permission['采购部门管理'][0],
    #     'admin': default_permission['行政部门管理'][0],
    #     'it': default_permission['IT部门管理'][0]
    # }
    try:
        if not current_user.verify_permission_p(permit_abbr[department]):
            flash('您的权限不足！')
            return redirect(url_for('main.index'))
    except KeyError:
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    # 获得筛选信息
    name = request.args.get('u_name', None)
    id = request.args.get('u_id',None,type=int)
    old_start = request.args.get('old_start',None,type=int)
    old_over = request.args.get('old_over', None, type=int)
    # 开始查找数据库
    depart = Department.query.filter_by(abbr=department).first()
    query = User.query.filter_by(department=depart)
    # 开始处理筛选
    if id:
        query = query.filter(User.id==id)
    if name:
        query = query.filter(User.name==name)
    if old_start and old_over:
        query = query.filter(User.old>=old_start,User.old<=old_over)

    pagination = query.paginate(page, per_page=per_page,error_out=False)
    p_users = pagination.items
    return render_template('/main/dp_staff.html', dp_staff=p_users, pagination=pagination, depart=depart, permit_o=permission_o, per_page=per_page)


@main.route('/batch_staff/getdepartandposition')
def getdp():
    return json.dumps(default_position)


@main.route('/batch_staff')
def batch_staff():
    return render_template('main/batch_staff.html')


@main.route('/add-to-sql',methods=['POST'])
def add_to_sql():
    json_list = request.form.get('json_list')
    list = json.loads(json_list)
    success_num = 0
    print(list)
    for x in list:
        name = x['姓名']
        department = x['部门']
        position = x['职位']
        address = x['家庭住址']
        phone = x['联系电话']
        birth = x['出生年月']
        # 处理出生日期
        try:
            birth = get_birth_date(birth)
        except:
            birth = date(2018, 1, 1)
        # 处理department 和 position
        # try:
        #     department = Department.query.filter_by(name=department).first()
        #     if department:
        #         position = Position.query.filter_by(department=department).filter_by(position.name).first()
        #         print('寻找到：' + position)
        #     else:
        #         department = Department.query.filter_by(name='生产部').first()
        #         position = Position.query.filter_by(department=department).filter_by(position.name).first()
        #
        # except:
        #     department = Department.query.filter_by(name='生产部').first()
        #     position = Position.query.filter_by(department=department).filter_by(position.name).first()

        # 获取部门
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
        if not current_user.verify_permission_p(
                permit_abbr[department.abbr] | permit_abbr[position.abbr]) or not current_user.verify_permission_p(
                permit_abbr[position.abbr]):
            continue
        else:
            u = User(name=name, department=department, position=position, address=address, phone=phone, birth=birth)
            db.session.add(u)
            success_num += 1

    db.session.commit()
    res = {'status': 1, 'success': success_num, 'false': len(list)-success_num, 'message': '提交成功！'}
    return json.dumps(res)



@main.route('/add-to-sql-by-excel', methods=['POST'])
def add_to_sql_by_excel():
    file_excel = request.files['file-excel']

    filename = os.path.join(os.getcwd()+'\\app\\static\\temp\\', str(random.random())[2:])  # 如果是linux需要修改
    # filename = url_for('static',filename='static/temp/'+str(random.random())[2:])

    file_excel.save(filename)
    # file_excel = BytesIO(file_excel.read())
    data = xlrd.open_workbook(filename)
    table = data.sheets()[0]
    nrows = table.nrows
    ncols = table.ncols
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
        birth = xlrd.xldate_as_datetime(birth,0).date()

        print(birth)
        # 处理出生日期
        # birth = get_birth_date(birth)

        # 处理department 和 position
        # try:
        #     department = Department.query.filter_by(name=department).first()
        #     if department:
        #         position = Position.query.filter_by(department=department).filter_by(position.name).first()
        #         print('寻找到：' + position)
        #     else:
        #         department = Department.query.filter_by(name='生产部').first()
        #         position = Position.query.filter_by(department=department).filter_by(position.name).first()
        #
        # except:
        #     department = Department.query.filter_by(name='生产部').first()
        #     position = Position.query.filter_by(department=department).filter_by(position.name).first()

        # 获取部门
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
        if not current_user.verify_permission_p(permit_abbr[department.abbr]|permit_abbr[position.abbr]) or not current_user.verify_permission_p(permit_abbr[position.abbr]):
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
    if os.path.exists(filename):
        os.remove(filename)

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
    d_abbr = u.department.abbr
    p_abbr = u.position.abbr
    # 权限检查
    if not current_user.verify_permission_p(permit_abbr[d_abbr]|permit_abbr[p_abbr]) or not current_user.verify_permission_o(permission_o.ADD_AND_REMOVE):
        return json.dumps({'status': 0, 'message': '权限不足！'})

    # 开始删除
    db.session.delete(u)
    db.session.commit()
    return json.dumps({'status': 1, 'message': '操作成功！'})


# @main.route('/filter',methods=['POST'])
# def filter():
#     # 规定传入参数：部门abbr、姓名、工号、年龄开始、年龄结束
#     dp_abbr = request.form.get('dp_abbr')
#     name = request.form.get('name')
#     id = request.form.get('id')
#     old_start = int(request.form.get('old_start'))
#     old_over = int(request.form.get('old_over'))
#     # 寻找部门
#     # 找到了部门：寻找符合条件的用户
#     # 没有找到部门：返回错误
#     d = Department.query.filter_by(abbr=dp_abbr)
#     if d:
#         query = User.query.filter_by(department=d)
#         if id:
#             query = query.filter_by(id=id)
#         if name:
#             query = query.filter_by(name=name)
#         # 获取到以上条件符合的user
#         # us = query.all()
#         # if us:
#         if old_start and old_over:
#             query = query.filter(User.old>=old_start,User.old<=old_over)
#
#         # 返回数据
#         us = query.all()
#
#         if us:
#
#
#
#     else:
#         res = {'status': 0, 'message': '无法找到部门！'}
#         return res

@main.route('/edit-staff/<int:id>')
@login_required
def edit_staff(id):
    u = User.query.get(id)

    if not u:
        abort(404)

    # 检查权限
    current_user.verify_permission_by_user(u)
    return render_template('edit_staff.html', user=u)
