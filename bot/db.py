import psycopg2

from bot.utils.notification import Attachment, Notification


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
            sql = (
                "INSERT INTO users (id, username) VALUES (%s, %s) "
                "ON CONFLICT (id) DO NOTHING;"
            )
            self.cur.execute(sql, (id, username))
            self.conn.commit()
        except Exception as e:
            print(e)
            raise e

    def insert_notification(self, notification: Notification):
        try:
            sql = (
                "INSERT INTO notifications (uid, date, time, description,"
                " creation_date, creation_time, is_periodic, period, is_done) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"
            )

            self.cur.execute(
                sql,
                (
                    notification.uid,
                    notification.date,
                    notification.time,
                    notification.description,
                    notification.creation_date,
                    notification.creation_time,
                    notification.is_periodic,
                    notification.period,
                    notification.is_done,
                ),
            )
            notification.id = self.cur.fetchone()[0]

            for obj in notification.attachments_id:
                sql = (
                    "INSERT INTO attachments (notification_id, file_id, file_type)"
                    " VALUES (%s, %s, %s)"
                )
                self.cur.execute(sql, (notification.id, obj.file_id, obj.file_type))

            self.conn.commit()
        except Exception as e:
            print(e)
            raise e

    def get_notifications_uid(self, uid: int):
        try:
            res: list[Notification] = []
            self.cur.execute("SELECT * from notifications WHERE uid = %s", (uid,))
            data = self.cur.fetchall()
            for nt in data:
                notification = Notification(
                    id=nt[0],
                    uid=nt[1],
                    description=nt[2],
                    date=nt[2],
                    time=nt[3],
                    is_periodic=nt[4],
                    period=nt[5],
                    creation_date=nt[6],
                    creation_time=nt[7],
                    is_done=nt[8],
                )
                self.cur.execute(
                    (
                        "SELECT file_id, file_type FROM attachments "
                        "WHERE  notification_id = %s"
                    ),
                    (notification.id,),
                )
                data = self.cur.fetchall()
                for row in data:
                    notification.attachments_id.append(Attachment(row[0], row[1]))

                res.append(notification)
            return res
        except Exception as e:
            print(e)
            raise e

    def get_all_notifications(self):
        try:
            res: list[Notification] = []
            self.cur.execute("SELECT * from notifications")
            data = self.cur.fetchall()
            for nt in data:
                notification = Notification(
                    id=nt[0],
                    uid=nt[1],
                    description=nt[2],
                    date=nt[3],
                    time=nt[4],
                    is_periodic=nt[5],
                    period=nt[6],
                    creation_date=nt[7],
                    creation_time=nt[8],
                    is_done=nt[9],
                )

                self.cur.execute(
                    (
                        "SELECT file_id, file_type FROM attachments "
                        "WHERE  notification_id = %s"
                    ),
                    (notification.id,),
                )
                data = self.cur.fetchall()

                for row in data:
                    notification.attachments_id.append(Attachment(row[0], row[1]))

                res.append(notification)
            self.conn.commit()
            return res
        except Exception as e:
            print(e)
            raise e

    def get_pending(self, uid: int | None = None):
        try:
            res: list[Notification] = []
            if not uid:
                sql = (
                    "SELECT * from notifications WHERE is_done=FALSE OR"
                    " is_periodic=TRUE"
                )
                self.cur.execute(sql)
            else:
                sql = (
                    "SELECT * from notifications WHERE (is_done=FALSE OR"
                    " is_periodic=TRUE) AND uid = %s"
                )
                self.cur.execute(sql, (uid,))

            data = self.cur.fetchall()
            for nt in data:
                notification = Notification(
                    id=nt[0],
                    uid=nt[1],
                    description=nt[2],
                    date=nt[3],
                    time=nt[4],
                    is_periodic=nt[5],
                    period=nt[6],
                    creation_date=nt[7],
                    creation_time=nt[8],
                    is_done=nt[9],
                )

                self.cur.execute(
                    (
                        "SELECT file_id, file_type FROM attachments "
                        "WHERE  notification_id = %s"
                    ),
                    (notification.id,),
                )
                data = self.cur.fetchall()

                for row in data:
                    notification.attachments_id.append(Attachment(row[0], row[1]))

                res.append(notification)
            self.conn.commit()
            return res
        except Exception as e:
            print(e)
            raise e

    def get_done(self, uid: int):
        try:
            res: list[Notification] = []
            sql = "SELECT * from notifications WHERE is_done=TRUE AND uid = %s"
            self.cur.execute(sql, (uid,))

            data = self.cur.fetchall()
            for nt in data:
                notification = Notification(
                    id=nt[0],
                    uid=nt[1],
                    description=nt[2],
                    date=nt[3],
                    time=nt[4],
                    is_periodic=nt[5],
                    period=nt[6],
                    creation_date=nt[7],
                    creation_time=nt[8],
                    is_done=nt[9],
                )

                self.cur.execute(
                    (
                        "SELECT file_id, file_type FROM attachments "
                        "WHERE  notification_id = %s"
                    ),
                    (notification.id,),
                )
                data = self.cur.fetchall()

                for row in data:
                    notification.attachments_id.append(Attachment(row[0], row[1]))

                res.append(notification)
            self.conn.commit()
            return res
        except Exception as e:
            print(e)
            raise e

    def mark_done(self, nt: Notification):
        try:
            self.cur.execute(
                "UPDATE notifications SET is_done = TRUE WHERE id = %s",
                (nt.id,),
            )
            self.conn.commit()
        except Exception as e:
            print(e)
            raise e

    def delete_notification(self, nt: Notification):
        try:
            self.cur.execute("DELETE from notifications where id = %s", (nt.id,))
            self.conn.commit()
        except Exception as e:
            print(e)
            raise e
