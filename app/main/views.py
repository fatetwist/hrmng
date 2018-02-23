from . import main
from flask import redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user
from ..models import Department, User, permit_abbr, permission_o, default_position, Position
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

def get_birth_date(birth):
    birth = birth.split('/')
    year = birth[0]
    month = birth[1]
    day = birth[2]
    birth_date = date(year, month, day)
    return birth_date

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
    depart = Department.query.filter_by(abbr=department).first()
    query = User.query.filter_by(department=depart)
    pagination = query.paginate(page, per_page=per_page,error_out=False)
    p_users = pagination.items
    return render_template('/main/dp_staff.html', dp_staff=p_users, pagination=pagination, depart=depart, permit_o=permission_o)


@main.route('/batch_staff/getdepartandposition')
def getdp():
    return json.dumps(default_position)


@main.route('/batch_staff')
def batch_staff():
    return render_template('main/batch_staff.html')

@login_required
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
    for i in range(1, nrows):
        rowvalues = table.row_values(i)
        name = rowvalues[0]
        department = rowvalues[1]
        position = rowvalues[2]
        address = rowvalues[3]
        phone = rowvalues[4]
        birth = rowvalues[5]

        try:
            birth = get_birth_date(birth)
        except:
            birth = date(2018, 1, 1)
        try:
            department = Department.query.filter_by(name=department).first()
            if department:
                position = Position.query.filter_by(department=department,name=position).first()
            else:
                department = Department.query.filter_by(name='生产部').first()
                position = Position.query.filter_by(department=department,name=position).first()
        except:
            department = Department.qeury.filter_by(name='生产部').first()
            position = Position.query.filter_by(department=department, name=position).first()

        # 权限验证
        if not current_user.verify_permission_p(permit_abbr[department.abbr]|permit_abbr[position.abbr]) or not current_user.verify_permission_o(permit_abbr[position.abbr]):
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


@main.route('/add-to-sql',methods=['POST'])
def add_to_sql():
    json_list = request.form.get('json_list')
    list = json.loads(json_list)
    success_num = 0
    false_num = 0
    for x in list:
        name = x['姓名']
        department = x['部门']
        position = x['职位']
        address = x['家庭住址']
        phone = x['联系电话']
        birth = x['出生年月']
        try:
            birth = get_birth_date(birth)
        except:
            birth = date(2018, 1, 1)
    # name = request.data.get('name')
    # department = request.data.get('department')
    # position = request.data.get('position')
    # address = request.data.get('address')
    # phone = request.data.get('phone')
    # birth = request.data.get('birth')
        # 获取部门
        try:
            department = Department.query.filter_by(name=department).first()
        except:
            department = Department.query.filter_by(name='生产部').first()

        # 获取职位
        try:
            position = Position.query.filter_by(name=position).first()
        except:
            position = Position.query.filter_by(name='员工').filter_by(department=department).first()


        print('正在录入信息：',name, department, position, address, phone, birth)
        try:
            u = User(name=name, department=department, position=position, address=address, phone=phone, birth=birth)
            db.session.add(u)
            db.session.commit()
            success_num += 1
        except:
            false_num += 1
    res = {'status': 1, 'success': success_num, 'false': false_num, 'message': '提交成功！'}
    return json.dumps(res)
