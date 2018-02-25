# coding=utf-8
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import UserMixin
from . import login_manager
from datetime import date


def calculate_age(born):
    today = date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError:
    # raised when birth date is February 29
    # and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def get_birth_date(birth):
    birth = birth.split('/')
    year = int(birth[0])
    month = int(birth[1])
    day = int(birth[2])
    birth_date = date(year, month, day)
    return birth_date



class permission_p:
    # 部门
    IT = 0x20000  # IT部
    DIRECTOR = 0x10000  # 董事会
    MANAGER = 0x8000  # 总经办
    ADMIN = 0x4000  # 行政部
    FINANCE = 0x2000  # 财务部
    PRODUCT = 0x1000  # 生产部
    SALE = 0x800  # 销售部
    HR = 0x400  # 人力资源部
    PURCHASE = 0x200  # 采购部
    LOGISTICS = 0x100  # 后勤部
    # 职位 : 主管、经理、副经理、组长、员工
    D_MANAGER = 0x80  # 经理和主管
    D_MANAGER_F = 0x40  # 副经理
    D_GROUP_LEADER = 0x20  # 组长
    D_EMPLOYEE = 0x10  # 员工
    D_DIRECTOR = 0x08
    #########################


permit_abbr = {
	'it':permission_p.IT, # it部
	'director':permission_p.DIRECTOR, # 董事会
	'manager':permission_p.MANAGER, # 总经办
	'admin':permission_p.ADMIN, # 行政部
	'sale':permission_p.SALE,
	'purchase':permission_p.PURCHASE,
	'product':permission_p.PRODUCT,
	'logistics':permission_p.LOGISTICS,
	'hr':permission_p.HR,
	'finance':permission_p.FINANCE,
    'd_manager':permission_p.FINANCE,
    'd_manager_f': permission_p.D_MANAGER_F,
    'd_group_leader': permission_p.D_GROUP_LEADER,
    'd_employee': permission_p.D_EMPLOYEE,
    'd_director': permission_p.D_DIRECTOR
}


class permission_o:  # 具体权限
    EVALUATE = 0x40  # 评价
    ADD_AND_REMOVE = 0x80  # 增加和删除

# 用户回调函数


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    def get_age(self):
        return calculate_age(self.birth)

    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(64),nullable=False)
    position_id = db.Column(db.Integer,db.ForeignKey('positions.id'))
    department_id = db.Column(db.Integer,db.ForeignKey('departments.id'))
    address = db.Column(db.Text)
    birth = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(11),nullable=False)
    login_permission = db.Column(db.Boolean, default=True)
    old = db.Column(db.Integer)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'))
    password_hash = db.Column(db.String(128))



    # @property
    # def old(self):
    #     return calculate_age(self.birth)

    @property
    def password(self):
        raise AttributeError('【错误】禁止读取密码')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def generate_test_users():
        for x in test_users:
            depart = Department.query.filter_by(name=x['department']).first()
            position = None
            # 开始寻找position
            for y in depart.positions:
                if y.name == x['position']:
                    position = y
            if not position:
                position = depart.positions[0]  # 默认取第一个
            u = User(name=x['name'], position=position, department=depart, phone=x['phone'], old=x['old'])
            db.session.add(u)
            db.session.commit()

    @staticmethod
    def re_old():
        us = User.query.all()
        for u in us:
            u.old = calculate_age(u.birth)
        db.session.commit()


    def verify_permission_by_user(self,u):
        dp = permit_abbr[u.department.abbr]|permit_abbr[u.position.abbr]
        if not self.verify_permission_p(dp):
            return False

        if not self.verify_permission_o(permission_o.ADD_AND_REMOVE|permission_o.EVALUATE):
            return False
        else:
            return True

    def verify_permission_p(self, p):
        return self.permission is not None and (self.permission.permission_p & p) == p

    def verify_permission_o(self, p):
        return self.permission is not None and (self.permission.permission_o & p) == p


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    abbr = db.Column(db.String(64))
    name = db.Column(db.String(64),unique=True)
    users = db.relationship('User', backref='department', lazy='dynamic')
    positions = db.relationship('Position', backref='department',lazy='dynamic')

    @staticmethod
    def generate_default_department():
        for x in default_position:
            department = Department(name=x,abbr=department_abbr[x])
            db.session.add(department)
            db.session.commit()


class Position(db.Model):
    __tablename__ = 'positions'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    # db.Column(db.String(64))
    name = db.Column(db.String(64))
    abbr = db.Column(db.String(64))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    users = db.relationship('User', backref='position', lazy='dynamic')

    @staticmethod
    def generate_default_position():
        for x in default_position:
            depart = Department.query.filter_by(name=x).first()
            if depart:
                for y in default_position[x]:
                    position = Position(name=y, department=depart,abbr=position_abbr[y])
                    db.session.add(position)
                    db.session.commit()
            else:
                print('【错误】%s职位无法添加，不能找到部门信息。' % x)


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(64), unique=True)
    permission_p = db.Column(db.Integer)
    permission_o = db.Column(db.Integer)
    users = db.relationship('User', backref='permission', lazy='dynamic')

    @staticmethod
    def generate_default_permission():
        for x in default_permission:
            p = default_permission[x]
            permission = Permission(name=x, permission_p=p[0], permission_o=p[1])
            db.session.add(permission)
            db.session.commit()


department_abbr = {
    '董事会': 'director',
    '总经办': 'manager',
    '行政部': 'admin',
    '财务部': 'finance',
    '生产部': 'product',
    '销售部': 'sale',
    '人力资源部': 'hr',
    '采购部': 'purchase',
    '后勤部': 'logistics',
    'IT部': 'it'
}

position_abbr ={
    '经理': 'd_manager',
    '主管': 'd_manager',
    '副经理': 'd_manager_f',
    '员工': 'd_employee',
    '董事长': 'd_director'
}

default_position = {
    '董事会': ['董事长'],
    '总经办': ['经理', '员工'],
    '行政部': ['经理', '员工'],
    '财务部': ['经理', '员工'],
    '生产部': ['经理', '员工'],
    '销售部': ['经理', '员工'],
    '人力资源部': ['经理', '员工'],
    '采购部': ['经理', '员工'],
    '后勤部': ['经理', '员工'],
    'IT部': ['经理', '员工']
}


default_permission = {

    '管理员': [0x1FFF, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '总经理部门管理': [0x8070, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '行政部门管理': [0x407F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '财务部门管理': [0x207F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '生产部门管理': [0x107F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '销售部门管理': [0x87F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '人力资源部门管理': [0x47F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '采购部门管理': [0x27F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    '后勤部门管理': [0x17F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE],
    'IT部门管理': [0x2000, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE]
}


test_users = [
    {'name': '张三', 'department': '董事会', 'phone': '010123456', 'old': 18, 'position': '董事长'},
    {'name': '李四', 'department': 'IT部', 'phone': '010123456', 'old': 18, 'position': '经理'},
    {'name': '张一', 'department': '人力资源部', 'phone': '010123456', 'old': 18, 'position': '经理'},
    {'name': '张二', 'department': '采购部', 'phone': '010123456', 'old': 18, 'position': '经理'},
    {'name': '张四', 'department': '销售部', 'phone': '010123456', 'old': 18, 'position': '经理'},
    {'name': '张五', 'department': '生产部', 'phone': '010123456', 'old': 18, 'position': '经理'},
    {'name': '张六', 'department': '生产部', 'phone': '010123456', 'old': 18, 'position': '经理'},
    {'name': '张七', 'department': '生产部', 'phone': '010123456', 'old': 18, 'position': '经理'},
    {'name': '张八', 'department': '生产部', 'phone': '010123456', 'old': 18, 'position': '经理'}
]



