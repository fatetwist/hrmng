from . import main
from flask import redirect, url_for
from flask_login import login_required


@login_required
@main.route('/')
def index():
    return redirect(url_for('main.hrmanage'))


@main.route('/hrmanage')
def hrmanage():
    return '人员管理主界面'


@main.route('/hrmanage/<department>')
def dp_staff():
    return '部门人员信息'



