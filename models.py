from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class user_db(db.Model):
    userid = db.Column(db.Integer(),primary_key=True)
    email = db.Column(db.String(64))
    hash = db.Column(db.String(128))
    sum_to_live = db.Column(db.Integer())
    reserve_account = db.Column(db.String(64))

    def __repr__(self):
        return '<user_db {}>'.format(self.name)


class savings_db(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    userid = db.Column(db.Integer())
    name = db.Column(db.String(128))
    goal = db.Column(db.Integer())  # goal sum
    date = db.Column(db.Date())  # date when goal sum should be accumulated
    # term = db.Column(db.Boolean())  # False for unlimited time for savings, True - for savings with finish date
    value = db.Column(db.Integer())  # current value
    percent = db.Column(db.Integer()) #

    def __repr__(self):
        return '<savings_db {}>'.format(self.name)


class expenses_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    name = db.Column(db.String(128))
    value = db.Column(db.Integer())

    def __repr__(self):
        return '<expenses_db {}>'.format(self.name)


class history_expenses_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    name = db.Column(db.String(128))
    to_pay = db.Column(db.Integer())
    value = db.Column(db.Integer())
    date = db.Column(db.Date())

    def __repr__(self):
        return '<history_expenses_db {}>'.format(self.name)