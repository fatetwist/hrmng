from app import create_app
from flask_script import Manager,Shell
from app import db
from flask_migrate import MigrateCommand,Migrate
from app.models import Permission,User,Position,Department

app = create_app('default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(db=db, Permission=Permission, User=User, Position=Position, Department=Department)


manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    manager.run()



