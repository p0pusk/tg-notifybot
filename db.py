import psycopg2
import json

from utils.notification import Notification


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


_config = json.load(open("./config.json"))
db = _DataBase(
    user=_config["DATABASE"]["USERNAME"],
    password=_config["DATABASE"]["PASSWORD"],
    dbname=_config["DATABASE"]["DB"],
    host=_config["DATABASE"]["HOST"],
)
