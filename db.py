import psycopg2
import datetime

from utils.notification import Notification
from config import dbconfig


class _DataBase:
    def __init__(self, dbname: str, user: str, password: str, host: str):
        try:
            self.conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host
            )
        except:
            raise Exception("Can`t establish connection to database")

        self.cur = self.conn.cursor()

    def insert_user(self, id: str, username: str):
        try:
            self.cur.execute(
                "INSERT INTO users (id, username) VALUES (%s, %s)", (id, username)
            )
            self.conn.commit()
        except Exception as e:
            print(e)

    def insert_notification(self, notification: Notification):
        try:
            self.cur.execute(
                (
                    "INSERT INTO notifications (uid, date, time, text) "
                    "VALUES (%s, %s, %s, %s)"
                ),
                (
                    notification.uid,
                    notification.date,
                    notification.time,
                    notification.text,
                ),
            )
            self.conn.commit()
        except Exception as e:
            print(e)

    def get_notifications_id(self, uid: int):
        try:
            res: list[Notification] = []
            self.cur.execute("SELECT * from notifications WHERE uid = %s", (uid,))
            data = self.cur.fetchall()
            for nt in data:
                date: datetime.date = nt[2]
                time: datetime.time = nt[3]
                text: str = nt[4]
                res.append(Notification(uid=uid, date=date, time=time, text=text))
            return res
        except Exception as e:
            print(e)

    def get_all_notifications(self):
        try:
            res: list[Notification] = []
            self.cur.execute("SELECT * from notifications")
            data = self.cur.fetchall()
            for nt in data:
                uid: int = nt[1]
                date: datetime.date = nt[2]
                time: datetime.time = nt[3]
                text: str = nt[4]
                res.append(Notification(uid=uid, date=date, time=time, text=text))
            return res
        except Exception as e:
            print(e)


db = _DataBase(
    user=dbconfig["USERNAME"],
    password=dbconfig["PASSWORD"],
    dbname=dbconfig["DB"],
    host=dbconfig["HOST"],
)
