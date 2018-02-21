import os
basedir = os.path.dirname(os.path.abspath(__file__))


class Config:
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True


username = 'root'
password = '123456'
host = 'localhost'
database = 'hrmanage'


class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://%s:%s@%s/%s' % (username, password, host, database)


config = {
    'development': Development,
    'default': Development
}