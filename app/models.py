from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from . import login_manager


class Permission_p:
    # 部门
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
    #########################


class permission_o:  # 具体权限
    EVALUATE = 0x40  # 评价
    ADD_AND_REMOVE = 0x80  # 增加和删除

# 用户回调函数


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(64))
    position_id = db.Column(db.Integer,db.ForeignKey('positions.id'))
    department_id = db.Column(db.Integer,db.ForeignKey('departments.id'))
    address = db.Column(db.Text)
    birth = db.Column(db.Date)
    old = db.Column(db.Integer)
    phone = db.Column(db.String(11))
    login_permission = db.Column(db.Boolean, default=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'))
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('【错误】禁止读取密码')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(64),unique=True)
    users = db.relationship('User', backref='department', lazy='dynamic')
    positions = db.relationship('Position', backref='department',lazy='dynamic')

    @staticmethod
    def generate_default_department():
        for x in default_position:
            department = Department(name=x)
            db.session.add(department)
            db.session.commit()


class Position(db.Model):
    __tablename__ = 'positions'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    # db.Column(db.String(64))
    name = db.Column(db.String(64))
    users = db.relationship('User', backref='position', lazy='dynamic')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))

    @staticmethod
    def generate_default_position():
        for x in default_position:
            depart = Department.query.filter_by(name=x).first()
            if depart:
                for y in default_position[x]:
                    position = Position(name=y, department=depart)
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






default_position = {
    '董事会': ['董事长'],
    '总经办': ['经理', '员工'],
    '行政部': ['主管', '员工'],
    '财务部': ['经理', '员工'],
    '生产部': ['主管', '员工'],
    '销售部': ['主管', '员工'],
    '人力资源部': ['主管', '员工'],
    '采购部': ['主管', '员工'],
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
    '后勤部门管理': [0x17F, permission_o.EVALUATE|permission_o.ADD_AND_REMOVE]
}
