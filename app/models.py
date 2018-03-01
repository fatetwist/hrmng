# coding=utf-8
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import UserMixin, AnonymousUserMixin,current_user
from . import login_manager
from datetime import date
class AnonymousUser(AnonymousUserMixin):
    def can(self, *args,**kwargs):
        return False

    def is_admin(self):
        return False


login_manager.anonymous_user = AnonymousUser


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


# 定义用户具体权限
class permit_u:  # 具体权限
    EVALUATE = 2  # 评价
    ADD_AND_REMOVE = 1  # 增加和删除
    EDIT = 4  # 编辑用户


# 定义默认数据
default_position = {
    'director': ['董事长'],
    'manager': ['经理', '员工'],
    'admin': ['经理', '员工'],
    'finance': ['经理', '员工'],
    'product': ['经理', '员工'],
    'sale': ['经理', '员工'],
    'hr': ['经理', '员工'],
    'purchase': ['经理', '员工'],
    'logistics': ['经理', '员工'],
    'it': ['经理', '员工']
}


default_permission = {
    '董事会管理权':(1,3,7),
    '总经办管理权':(2,3,7),
    '行政部管理权': (4, 3, 7),
    '生产部管理权': (16,3,7),
    '财务部管理权': (8,3,7),
    '销售部管理权': (32,3,7),
    '人力资源部管理权': (64,3,7),
    '采购部管理权': (128,3,7),
    '后勤部管理权': (256,3,7),
    'it部管理权': (512,3,7),
    '系统管理员': (0xFFFF, 0xFFFF, 0xFFFF)
}


default_apartment = {
    'director': ['董事会', 1],
    'admin': ['行政部',4],
    'manager': ['总经办',2],
    'product': ['生产部',16],
    'finance': ['财务部',8],
    'sale': ['销售部',32],
    'hr': ['人力资源部',64],
    'purchase': ['采购部',128],
    'logistics': ['后勤部', 256],
    'it':['it部', 512]
}


# 用户回调函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



u_permits = db.Table('u_permits',
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id')))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(64), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    address = db.Column(db.Text)
    birth = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    login_permission = db.Column(db.Boolean, default=False)
    old = db.Column(db.Integer)
    password_hash = db.Column(db.String(128))
    permissions = db.relationship('Permission', secondary=u_permits, backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
    evaluations = db.relationship('Evaluation', backref='user', lazy='dynamic')

    def get_evaluation(self):
        try:
            e = self.evaluations.all()[-1]
            d = date.today()
            if not(e.date.year == d.year and e.date.month == d.month):
                e = None
        except IndexError:
            e = None
        return e

    def clear_permissions(self):
        for p in self.permissions:
            self.permissions.remove(p)
        db.session.commit()

    def can(self, d=None, p=None, u=None):   # 输入3种权限值
        for x in self.permissions:
            if d and not (x.permit_d & d) == d:
                continue
            if p and not (x.permit_p & p) == p:
                continue
            if u and not (x.permit_u & u) == u:
                continue
            return True
        return False

    def is_admin(self):
        p = Permission.query.filter_by(name='系统管理员').first()
        if p:
            return self.can(p.permit_d, p.permit_p, p.permit_u)
        else:
            return self.can(65535, 65535, 65535)

    @staticmethod
    def get_ages():
        us = User.query.all()
        for u in us:
            u.old = calculate_age(u.birth)
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('【错误】禁止读取密码')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)



    @staticmethod
    def re_old():
        us = User.query.all()
        for u in us:
            u.old = calculate_age(u.birth)
        db.session.commit()


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    abbr = db.Column(db.String(64))
    name = db.Column(db.String(64),unique=True)
    users = db.relationship('User', backref='department', lazy='dynamic')
    positions = db.relationship('Position', backref='department', lazy='dynamic')
    permit = db.Column(db.Integer, nullable=False)

    @staticmethod
    def generate_departments():
        for x in default_apartment:
            t = default_apartment[x]
            d = Department(abbr=x,name=t[0], permit=t[1])
            db.session.add(d)
        db.session.commit()


class Position(db.Model):
    __tablename__ = 'positions'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    # db.Column(db.String(64))
    name = db.Column(db.String(64))
    abbr = db.Column(db.String(64))
    permit = db.Column(db.Integer, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    users = db.relationship('User', backref='position', lazy='dynamic')

    @staticmethod
    def generate_positions():
        for x in default_position:
            t = default_position[x]
            d = Department.query.filter_by(abbr=x).first()
            if not d:
                print('【错误】没有找到部门%s，无法产生默认职位！' % x)
                continue
            for y in t:
                if y == '董事长':
                    d_abbr = 'd_director'
                    permit = 4
                elif y == '经理':
                    d_abbr = 'd_manager'
                    permit = 1
                else:
                    d_abbr = 'd_staff'
                    permit = 2
                p = Position(permit=permit, name=y, abbr=d_abbr, department=d)
                db.session.add(p)
        db.session.commit()


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(64), unique=True)
    permit_d = db.Column(db.Integer, nullable=False)
    permit_p = db.Column(db.Integer, nullable=False)
    permit_u = db.Column(db.Integer, nullable=False)

    def can(self, d=None, p=None, u=None):
        if d and not (self.permit_d & d) == d:
            return False
        if p and not (self.permit_p & p) == p:
            return False
        if u and not (self.permit_u & u) == u:
            return False
        return True


    @staticmethod
    def generate_default_permission():
        for x in default_permission:
            p = default_permission[x]
            permission = Permission(name=x, permit_d=p[0], permit_p=p[1], permit_u=p[2])
            db.session.add(permission)
        db.session.commit()


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    remark = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

