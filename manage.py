from flask_script import Manager, Shell
from app import db
from app import create_app
from app.models import Permission, User, Position, Department
from flask_migrate import MigrateCommand, Migrate


app = create_app('development')
manager = Manager(app)
migrate = Migrate(app, db)


def initialize():
    # 该方法会初始化项目系统，创建一个系统管理员，创建部门、职位、权限等默认数据
    print('正在初始化......')
    import pymysql
    sql = pymysql.connect('localhost', 'root', '123456')
    cu = sql.cursor()
    # 创建数据库
    try:
        print('正在创建数据库...')
        cu.execute('create database hrmanage')
    except pymysql.err.ProgrammingError:
        print('数据库已存在，跳过创建')
    # 初始化表
    db.create_all()
    # 修改表编码
    cu.execute('use hrmanage')
    cu.execute('alter table users convert to character set utf8')
    cu.execute('alter table departments convert to character set utf8')
    cu.execute('alter table positions convert to character set utf8')
    cu.execute('alter table permissions convert to character set utf8')
    cu.execute('alter table evaluations convert to character set utf8')
    cu.execute('alter table u_permits convert to character set utf8')
    u = User(name='admin', password='123456')
    db.session.add(u)
    db.session.commit()
    print('成功创建管理员')
    print('id: %s  |  name: %s  |  password: 123456' % (u.id, u.name))
    print('正在创建默认部门...')
    Department.generate_departments()
    print('正在创建默认职位...')
    Position.generate_positions()
    print('正在创建默认权限...')
    Permission.generate_default_permission()
    u.permissions.append(Permission.query.filter_by(name='系统管理员').first())
    db.session.commit()
    print('一切工作准备完毕! 初始化已完成, 请使用管理员账号登陆管理系统.')
    print('请退出该交互系统后运行\n'
          'python manage.py runserver  启动本地服务器\n'
          'python manage.py -h 0.0.0.0 -p 80 --processes 24 --threaded 启动局域网服务器')
    print('输入 exit() 按回车退出交互系统')


def make_shell_context():
    return dict(db=db, Permission=Permission, User=User, Position=Position, Department=Department, initialize=initialize)



manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()

