from flask_script import Manager, Shell
from app import db
from app import create_app
from app.models import Permission, User, Position, Department
from flask_migrate import MigrateCommand, Migrate


app = create_app('test')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(db=db, Permission=Permission, User=User, Position=Position, Department=Department)


manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == '__main__':

    manager.run()
