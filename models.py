from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class user_db(db.Model):
    userid = db.Column(db.Integer(),primary_key=True)
    email = db.Column(db.String(64))
    hash = db.Column(db.String(128))
    reserve_account = db.Column(db.String(64))

    def __repr__(self):
        return '<user_db {}>'.format(self.name)


class savings_db(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    userid = db.Column(db.Integer())
    name = db.Column(db.String(128))
    goal = db.Column(db.Integer())  # goal sum
    value = db.Column(db.Integer())  # current value
    percent = db.Column(db.Integer()) # percent of income to pay monthly

    def __repr__(self):
        return '<savings_db {}>'.format(self.name)


class expenses_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    name = db.Column(db.String(128))
    value = db.Column(db.Integer())

    def __repr__(self):
        return '<expenses_db {}>'.format(self.name)

class goals_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    name = db.Column(db.String(128))
    value = db.Column(db.Integer()) # current value
    goal = db.Column(db.Integer()) # goal value
    date = db.Column(db.Date())  # date when goal sum should be accumulated

    def __repr__(self):
        return '<goals_db {}>'.format(self.name)



class history_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    salary = db.Column(db.Integer())

    expenses_name = db.Column(db.ARRAY(db.String()))
    expenses_value = db.Column(db.ARRAY(db.Integer()))

    savings_name = db.Column(db.ARRAY(db.String()))
    savings_to_pay = db.Column(db.ARRAY(db.Integer()))
    savings_value = db.Column(db.ARRAY(db.Integer()))

    goals_name = db.Column(db.ARRAY(db.String()))
    goals_to_pay = db.Column(db.ARRAY(db.Integer()))
    goals_value = db.Column(db.ARRAY(db.Integer()))


    date = db.Column(db.Date())

    def __repr__(self):
        return '<history_db {}>'.format(self.date)
