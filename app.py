from flask import Flask, request, render_template, session, redirect
from flask_migrate import Migrate
import os, secrets
from werkzeug.security import check_password_hash, generate_password_hash

from flask_mail import Mail, Message


from helpers import load_savings, logged, load_expenses, load_goals, money_distribution, load_user_info, \
    update_progress, save_in_history,load_history, create_ids_dict

app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY_easybreezy')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                      "postgresql://postgres:1111111@localhost:5432/easybreezy"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# for mail
app.config['MAIL_SERVER'] = 'smtp.yandex.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'andronikova.daria@ya.ru'
app.config['MAIL_DEFAULT_SENDER'] = 'andronikova.daria@ya.ru'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')


# load databases
from models import db, user_db, savings_db, expenses_db, goals_db, history_db


# database settings and creation of tables
with app.app_context():
    db.init_app(app)
    migrate = Migrate(app,db)
    db.app = app # don't touch to create new db
    db.create_all()
    db.session.commit()



@app.route('/', methods=['GET','POST'])
# @login_required  #TODO
def input():
    # session['userid'] = 1

    if request.method == "GET":

        if logged() is False:
            return render_template('welcome.html')

        userid = session.get('userid')

        # load info from db and save it in session
        load_savings(userid, savings_db)
        load_expenses(userid, expenses_db)
        load_goals(userid, goals_db)

        if load_user_info(userid, user_db) is False:
            return redirect('/error')

        return render_template('input.html',
                               savings=session.get('savings'),
                               expenses=session.get('expenses'),
                               goals=session.get('goals'),
                               user_info=session.get('user_info')
                               )

    if request.method == "POST":
        # DEF: saving all info from input page to session
        # save salary
        session['salary'] = float(request.form.get('salary'))

        # preload accounts from session
        savings = session.get('savings')
        expenses = session.get('expenses')
        goals = session.get('goals')

        #for all saving types load current value from input page
        for key in savings:
            savings[key]['value'] = float(request.form.get(key))

            #change progress info
            savings = update_progress(savings, key)

        # for all expenses load value from input page
        for key in expenses:
            expenses[key]['value'] = float(request.form.get(key))

        # for all goal load current value
        for key in goals:
            goals[key]['value'] = float(request.form.get(key))

            # change progress info
            goals = update_progress(goals, key)


        #save updated info in session
        session['expenses'] = expenses
        session['savings'] = savings
        session['goals'] = goals

        print(f'\n\n-----USER INPUT processed and saved in session\n\nexpenses: {expenses} \n\nsavings:{savings}\n\ngoals: {goals} \n\nsalary:{session.get("salary")}')
        return redirect('/output')


@app.route('/output', methods=['GET','POST'])
def output():
    if request.method == "GET":
        # DEF: calculate all payments using info from session, show it to user
        logged()

        # calculate payments using info from user, saved in session
        returned_dict = money_distribution(userid=session.get('userid'))

        if returned_dict is False:
            return redirect('/error')

        return render_template('output.html',
                               salary=session.get('salary'),
                               expenses=session.get('expenses'),
                               savings = returned_dict['savings'],
                               goals=returned_dict['goals'],
                               remain=returned_dict['remain'],
                               message=returned_dict['message'],
                               user_info=session.get('user_info')
                               )

    if request.method == "POST":
        # DEF load all info and save it in history and accounts db
        userid = session.get('userid')

        savings = session.get('savings')
        expenses = session.get('expenses')
        goals = session.get('goals')

        # load salary
        salary = float(request.form.get('salary'))

        # for all expenses load value from input page
        for key in expenses:
            expenses[key]['value'] = float(request.form.get(key))
            # nothing to save in db

        # for all saving types load current value from input page
        for key in savings:
            savings[key]['to_pay'] = float(request.form.get(key))
            savings[key]['value'] += savings[key]['to_pay']

            # save update value in db
            savings_db.query.filter_by(userid=userid, name=key).update({ 'value': savings[key]['value'] * 100 })

        for key in goals:
            goals[key]['to_pay'] = float(request.form.get(key))
            goals[key]['value'] += goals[key]['to_pay']

            # save update value in db
            goals_db.query.filter_by(userid=userid, name=key).update({ 'value': goals[key]['value'] * 100 })


        save_in_history(db, history_db,expenses,savings, goals, salary)


        return  redirect('/history')



@app.route('/history', methods=['GET','POST'])
def history():
    if request.method == 'GET':
        history = load_history(history_db)

        return render_template('history.html',
                               history=history,
                               expenses=session.get('expenses'),
                               savings=session.get('savings'),
                               goals=session.get('goals')
                               )


@app.route('/help', methods=['GET','POST'])
def help():
    if request.method == 'GET':
        logged = 1

        if session.get('userid') is None:
            logged = 0

        return render_template('help.html', logged=logged)



@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == 'GET':

        return render_template('settings.html',
                               expenses=session.get('expenses'),
                               savings=session.get('savings'),
                               goals=session.get('goals'),
                               user_info=session.get('user_info')
                               )

    if request.method == 'POST':
        if request.form.get("delete_account") is not None:
            # delete one of money account
            userid = session.get('userid')

            #load name of account
            key = request.form.get('delete_account')

            # find there this key
            if key in session.get('expenses'):
                # update db
                expenses_db.query.filter_by(userid=userid,name=key).delete(synchronize_session='evaluate')

                # reload session
                load_expenses(userid, expenses_db)

            # the same if key from savings
            elif key in session.get('savings'):
                savings_db.query.filter_by(userid=userid,name=key).delete(synchronize_session='evaluate')
                load_savings(userid, savings_db)

            # the same if key from goals
            elif key in session.get('goals'):
                goals_db.query.filter_by(userid=userid,name=key).delete(synchronize_session='evaluate')

                # reload session
                load_goals(userid, goals_db)

            db.session.commit()

            return redirect('/settings')

        if request.form.get("delete") is not None: # delete user
            userid = session.get('userid')

            # clear user_db
            user_db.query.filter_by(userid=userid).delete(synchronize_session='evaluate')

            # clear accounts db
            expenses_db.query.filter_by(userid=userid).delete(synchronize_session='evaluate')
            savings_db.query.filter_by(userid=userid).delete(synchronize_session='evaluate')
            goals_db.query.filter_by(userid=userid).delete(synchronize_session='evaluate')

            # clear history
            history_db.query.filter_by(userid=userid).delete(synchronize_session='evaluate')

            db.session.commit()

            print(f'user number {userid} deleted')

            # clear session
            session.clear()

            return redirect('/')


@app.route('/settings_change', methods=['GET','POST'])
def settings_change():
    if request.method == 'GET':
        expenses = session.get('expenses')
        savings = session.get('savings')
        goals = session.get('goals')

        #create id for each input
        id_name = {}
        id_name = create_ids_dict(id_name, expenses, ['name', 'value'])
        id_name = create_ids_dict(id_name, savings, ['name', 'percent', 'value', 'goal','reserve'])
        id_name = create_ids_dict(id_name, goals, ['name', 'value', 'goal', 'date'])


        print(f"\ndictionary for ids and names : {id_name}")

        return render_template('settings_change.html',
                               expenses=expenses,
                               savings=savings,
                               goals=goals,
                               id_name=id_name,
                               user_info=session.get('user_info')
                               )

    if request.method == 'POST':
        # load all necessary info from session
        userid = session.get('userid')

        expenses = session.get('expenses')
        savings = session.get('savings')
        goals = session.get('goals')

        # save change in expenses
        for key in expenses:
            newname = request.form.get('name_' + key)
            newvalue = float(request.form.get('value_' + key))

            # check uniqueness of new name if it is really new
            if newname != key:
                if check_name_uniqueness(newname) is False:
                    return redirect('/error')

            # update db
            expenses_db.query.filter_by(userid=userid, name=key).update({ 'name': newname, 'value': newvalue * 100 })

        # update session info
        load_expenses(userid, expenses_db)

        # ---------------------------------------------
        # save change in savings
        for key in savings:
            newname = request.form.get('name_' + key)
            newreserve = request.form.get('reserve_' + key)

            # check uniqueness of new name if it's new name
            if newname != key:
                if check_name_uniqueness(newname) is False:
                    return redirect('/error')

            # if this is reserve account
            if newreserve == 'on':
                # update user_db and session
                user_db.query.filter_by(userid=userid).update({'reserve_account': newname})
                session['user_info']['reserve_account'] = newname

            # update db
            savings_db.query.filter_by(userid=userid, name=key).update\
                    ({
                        'name': newname,
                        'value': 100 * float(request.form.get('value_' + key)),
                        'goal' : 100 * float(request.form.get('goal_' + key)) ,
                        'percent' : int(request.form.get('percent_' + key))
                    })

        # update session
        load_savings(userid, savings_db)

        # ---------------------------------------------
        # save changes in goals
        for key in goals:
            newname = request.form.get('name_' + key)

            # check uniqueness of new name if it is new name
            if newname != key:
                if check_name_uniqueness(newname) is False:
                    return redirect('/error')

            # update db
            goals_db.query.filter_by(userid=userid, name=key).update \
                    ({
                    'name': newname,
                    'value': 100 * float(request.form.get('value_' + key)),
                    'goal': 100 * float(request.form.get('goal_' + key)),
                    'date': request.form.get('date_' + key)
                })

        # update session
        load_goals(userid, goals_db)

        db.session.commit()

        return redirect ('/settings')


def check_name_uniqueness(newname):
    print('\ncheck name for uniqueness')
    expenses = session.get('expenses')
    savings = session.get('savings')
    goals = session.get('goals')

    # check that this name doesn't exist in any accounts
    if newname in expenses.keys():
        session['error_message'] = 'Please, use unique name.\nName ' + newname + ' is used in expenses already.'
        return False

    if newname in savings:
        session['error_message'] = 'Please, use unique name.\nName ' + newname + ' is used in savings already.'
        return False

    if newname in goals:
        session['error_message'] = 'Please, use unique name.\nName ' + newname + ' is used in goals already.'
        return False

    return True

def check_space_in_the_name(name):
    if ' ' in name:
        session['error_message'] = "Please, don't use space in the name"
        return True

    return False

@app.route('/add_expenses', methods=['GET','POST'])
def add_expenses():
    if request.method == 'GET':

        return render_template( 'add_expenses.html' )

    if request.method == 'POST':
        # load new values
        newname = request.form.get('newname')
        newvalue = float(request.form.get('value'))

        # check uniqueness of new name
        if check_name_uniqueness(newname) is not True:
            return redirect('/error')

        # check space in the name
        if check_space_in_the_name(newname):
            return redirect('/error')

        # load last id from db and put new id by hand (to avoid IntegrityError duplicate key violates unique-constraint)
        if len(expenses_db.query.all()) == 0: # db is empty
            max_id = 0
        else:
            max_id = expenses_db.query.order_by(expenses_db.id.desc()).first().id

        # update db
        newrow = expenses_db(id=max_id + 1, userid=session.get('userid'), name=newname, value=100 *newvalue)
        db.session.add(newrow)
        db.session.commit()

        # update session info
        load_expenses(session.get('userid'), expenses_db)

        return redirect('/settings')


@app.route('/add_savings', methods=['GET','POST'])
def add_savings():
    if request.method == 'GET':

        return render_template( 'add_savings.html' )

    if request.method == 'POST':
        # load new values
        newname = request.form.get('newname')
        newvalue = float(request.form.get('value'))
        newgoal = float(request.form.get('goal'))
        newpercent = float(request.form.get('percent'))

        # check uniqueness of new name
        if check_name_uniqueness(newname) is not True:
            return redirect('/error')

        # check space in the name
        if check_space_in_the_name(newname):
            return redirect('/error')


        # load last id from db and put new id by hand (to avoid IntegrityError duplicate key violates unique-constraint)
        if len(savings_db.query.all()) == 0: # db is empty
            max_id = 0
        else:
            max_id = savings_db.query.order_by(savings_db.id.desc()).first().id

        # update db
        newrow = savings_db(id=max_id + 1, userid=session.get('userid'),
                            name=newname,
                            value= 100 * newvalue,
                            goal= 100 * newgoal,
                            percent=newpercent
                            )
        db.session.add(newrow)
        db.session.commit()

        # update session info
        load_savings(session.get('userid'), savings_db)

        return redirect('/settings')



@app.route('/add_goals', methods=['GET','POST'])
def add_goals():
    if request.method == 'GET':

        return render_template( 'add_goals.html' )

    if request.method == 'POST':
        # load new values
        newname = request.form.get('newname')
        newvalue = float(request.form.get('value'))
        newgoal = float(request.form.get('goal'))
        newdate= request.form.get('date')

        # check uniqueness of new name
        if check_name_uniqueness(newname) is not True:
            return redirect('/error')

        # check space in the name
        if check_space_in_the_name(newname):
            return redirect('/error')

        # load last id from db and put new id by hand (to avoid IntegrityError duplicate key violates unique-constraint)
        if len(goals_db.query.all()) == 0:  # db is empty
            max_id = 0
        else:
            max_id = goals_db.query.order_by(goals_db.id.desc()).first().id

        # update db
        newrow = goals_db(id=max_id + 1, userid=session.get('userid'),
                            name=newname,
                            value= 100 * newvalue,
                            goal= 100 * newgoal,
                            date=newdate
                            )
        db.session.add(newrow)
        db.session.commit()

        # update session info
        load_goals(session.get('userid'), goals_db)

        return redirect('/settings')


@app.route('/change_email', methods=['GET','POST'])
def change_email():
    if request.method == "GET":
        return render_template('change_email.html')

    if request.method == "POST":
        newemail = request.form.get("email")

        # change session info
        user_info = session.get('user_info')
        user_info['email'] = newemail
        session['user_info'] = user_info

        # change db
        user_db.query.filter_by(userid=session.get('userid')).update( {'email':newemail} )
        db.session.commit()

        return redirect('/settings')


@app.route('/change_password', methods=['GET','POST'])
def change_password():
    if request.method == "GET":
        return render_template('change_password.html')

    if request.method == "POST":
        userid = session.get('userid')
        datas = user_db.query.filter_by(userid=userid).all()

        # check old password
        if check_password_hash(datas[0].hash, request.form.get("old")) is False:
            session['error_message'] = 'Your old password is not correct.'
            return error()

        # save new hashed password
        user_db.query.filter_by(userid=userid).update(
            {
                'hash':generate_password_hash(request.form.get("new"))
            })
        db.session.commit()

        return redirect('/')


@app.route('/registration', methods=['GET','POST'])
def registration():
    if request.method == "GET":
        # Forget any user_id
        session.clear()

        return render_template('registration.html')

    if request.method == "POST":
        email = request.form.get("email")

        # hash password
        hashed = generate_password_hash(request.form.get("password"))

        # Query database for email
        datas = user_db.query.filter_by(email=email).all()

        if len(datas) != 0:
            session['error_message'] = "User with email " + email + " already exists."
            return redirect('/error')

        # load last id from user_db
        if len(user_db.query.all()) == 0:  # db is empty
            max_id = 0
        else:
            max_id = user_db.query.order_by(user_db.userid.desc()).first().userid

        userid = max_id + 1
        print(f'userid is {userid}')

        # create new row in user_db
        new_user = user_db(userid=userid, email=email, hash=hashed, reserve_account='default')
        db.session.add(new_user)

        # save in user in session
        session["userid"] = userid

        db.session.commit()

        return redirect('/')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        # Forget any user_id
        session.clear()

        return render_template('login.html')

    if request.method == "POST":
        email = request.form.get("email")

        # Query database for username
        datas = user_db.query.filter_by(email=email).all()

        # Ensure username exists and password is correct
        if len(datas) != 1 or not check_password_hash(datas[0].hash, request.form.get("password")):
            session['error_message'] = "invalid username and/or password"
            return redirect('/wrong_login_or_password')

        # Remember which user has logged in
        session["userid"] = datas[0].userid


        return redirect('/')




@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == "GET":
        return render_template('forgot_password.html')

    if request.method == "POST":
        # check that this email in user_db
        email = request.form.get("email")
        datas = user_db.query.filter_by(email=email).all()
        if len(datas) == 0:
            session['error_message'] = 'There is no user with email ' + email
            return error()

        # generate new password
        new_password = secrets.token_hex(16)

        # send password to user
        text = 'Dear EasyBreezy user,\nhere is your new password:\n' + new_password
        text += '\nPlease, change this password as soon as possible. \n\nEasyBreezy'
        topic = 'EasyBreezy: your new password'

        with app.app_context():
            mail = Mail()
            mail.init_app(app)

            message = Message(topic, recipients=[email])

            message.body = text

            ret = mail.send(message)


        print(f"new password has been created and send to {email}\n ret is {ret}")

        # save this password in user_db
        user_db.query.filter_by(email=email).update({
            'hash' : generate_password_hash(new_password)
        })
        db.session.commit()

        return redirect('/login')


@app.route('/error')
def error():
    return render_template('error_page.html', message=session.get('error_message'))

@app.route('/wrong_login_or_password')
def wrong_login_or_password():
    return render_template('wrong_login_or_password.html', message=session.get('error_message'))


if __name__ == "__main__":
    app.run(debug=True)