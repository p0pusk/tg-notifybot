import psycopg2
import datetime

from utils.notification import Notification


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class DataBase:
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
                    "INSERT INTO notifications (uid, date, time, text)"
                    "VALUES (%s, %s, %s, %s) RETURNING id"
                ),
                (
                    notification.uid,
                    notification.date,
                    notification.time,
                    notification.text,
                ),
            )
            notification.id = self.cur.fetchone()[0]
            print(f"NT id: {notification.id}")
            self.conn.commit()
        except Exception as e:
            print(e)

    def get_notifications_uid(self, uid: int):
        try:
            res: list[Notification] = []
            self.cur.execute("SELECT * from notifications WHERE uid = %s", (uid,))
            data = self.cur.fetchall()
            for nt in data:
                id: int = nt[0]
                date: datetime.date = nt[2]
                time: datetime.time = nt[3]
                text: str = nt[4]
                res.append(
                    Notification(id=id, uid=uid, date=date, time=time, text=text)
                )
            return res
        except Exception as e:
            print(e)

    def get_all_notifications(self):
        try:
            res: list[Notification] = []
            self.cur.execute("SELECT * from notifications")
            data = self.cur.fetchall()
            for nt in data:
                id: int = nt[0]
                uid: int = nt[1]
                date: datetime.date = nt[2]
                time: datetime.time = nt[3]
                text: str = nt[4]
                res.append(
                    Notification(id=id, uid=uid, date=date, time=time, text=text)
                )
            return res
        except Exception as e:
            print(e)

    def delete_notification(self, nt: Notification):
        try:
            self.cur.execute("DELETE from notifications where id = %s", (nt.id,))
            self.conn.commit()
        except Exception as e:
            print(e)
