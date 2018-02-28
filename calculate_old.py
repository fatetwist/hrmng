
from app.models import User
from app import create_app
import time
from datetime import date, timedelta

def output_log(ms):
    with open('outms.log', 'a',encoding='utf-8') as file:

        file.write(ms + '\n')

app = create_app('test')

with app.app_context():
    User.get_ages()


while True:
    t = time.localtime()
    date = date.today()
    h = t.tm_hour
    m = t.tm_min
    if h == 23 and m>= 50:
        User.get_ages()
        output_log(date.strftime('%Y/%m/%d'))
    if h == 0 and m <= 10:
        User.get_ages()
        d = timedelta(days=1)
        date = date - d
        output_log(date.strftime('%Y/%m/%d'))
    time.sleep(1)
