import os
basedir = os.path.dirname(os.path.abspath(__file__))


class Config:
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SECRET_KEY = os.urandom(16)




class Development(Config):
    DEBUG = True
    username = 'root'
    password = '123456'
    host = 'localhost'
    database = 'hrmanage'
    SQLALCHEMY_DATABASE_URI = 'mysql://%s:%s@%s/%s' % (username, password, host, database)


class test(Config):
    DEBUG = True
    username = 'root'
    password = '123456'
    host = 'localhost'
    database = 'hrmanage_test'
    SQLALCHEMY_DATABASE_URI = 'mysql://%s:%s@%s/%s' % (username, password, host, database)


config = {
    'development': Development,
    'default': Development,
    'test': test
}

