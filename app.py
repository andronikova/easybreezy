from flask import Flask, request, render_template, session, redirect
from flask_migrate import Migrate
import os

from helpers import load_savings, logged, load_expenses, load_goals, money_distribution, load_user_info, update_progress, save_in_history,load_history

app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY_easybreezy')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                      "postgresql://postgres:1111111@localhost:5432/easybreezy"

# print(f" \nX\nX\nX\nX  DATABASE_URL  from os.environ  {os.environ.get('DATABASE_URL')} \nX\nX\nX\n")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# load databases
from models import db, user_db, savings_db, expenses_db, goals_db, \
    history_expenses_db, history_accounts_db, history_salary_db


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
    session['userid'] = 1

    if request.method == "GET":

        if logged() is False:
            return render_template('welcome.html')

        userid = session.get('userid')
        # load info from db and save it in session
        load_savings(userid, savings_db)
        load_expenses(userid, expenses_db)
        load_goals(userid, goals_db)

        load_user_info(userid, user_db)

        return render_template('input.html',
                               savings=session.get('savings'),
                               expenses=session.get('expenses'),
                               goals=session.get('goals'),
                               user_info=session.get('user_info')
                               )

    if request.method == "POST":
        # DEF: saving all info from input page to session
        # save salary
        session['salary'] = int(request.form.get('salary'))

        #for all saving types load current value from input page
        savings = session.get('savings')
        for key in savings:
            new_value = int(request.form.get(key))

            if new_value != savings[key]['value']: # if user change value
                savings[key]['value'] = new_value

                #change progress info
                savings = update_progress(savings, key)

        # for all expenses load value from input page
        expenses = session.get('expenses')
        for key in expenses:
            new_value = int(request.form.get(key))

            # save new value in the session
            expenses[key]['value'] = new_value

        # for all goal load current value
        goals = session.get('goals')
        for key in goals:
            new_value = int(request.form.get(key))

            goals[key]['value'] = new_value

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


        return render_template('output.html',
                               salary=session.get('salary'),
                               expenses=session.get('expenses'),
                               savings = returned_dict['savings'],
                               remain=returned_dict['remain'],
                               message=returned_dict['message'],
                               user_info=session.get('user_info')
                               )

    if request.method == "POST":
        # DEF load all info and save it in history and accounts db
        # save new values in session
        session['salary'] = float(request.form.get('salary'))

        # for all saving types load current value from input page
        savings = session.get('savings')

        for key in savings:
            new_to_pay = float(request.form.get(key))

            if new_to_pay != savings[key]['to_pay']:  # if user change value
                savings[key]['to_pay'] = new_to_pay

                # change progress info
                savings = update_progress(savings, key)

        # for all expenses load value from input page
        expenses = session.get('expenses')
        for key in expenses:
            new_value = int(request.form.get(key))

            # save new value in the session
            expenses[key]['value'] = new_value

        # save updated info in session
        session['expenses'] = expenses
        session['savings'] = savings

        save_in_history(db, history_expenses_db, history_accounts_db, history_salary_db)

        # go to page with calculation
        return  redirect('/history')



@app.route('/history', methods=['GET','POST'])
def history():
    if request.method == 'GET':
        salary_history = history_salary_db.query.filter_by(userid=session.get('userid')).order_by(history_salary_db.date.desc()).all()
        history = load_history(history_salary_db, history_accounts_db,history_expenses_db)

        savings_list, expenses_list = [],[]
        for row in session.get('savings'):
            savings_list.append(row)

        for row in session.get('expenses'):
            expenses_list.append(row)

        return render_template('history.html',
                               history=history,
                               savings_list=savings_list,
                               expenses_list=expenses_list
                               )


@app.route('/help', methods=['GET','POST'])
def help():
    if request.method == 'GET':

        return render_template('help.html')


@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == 'GET':

        return render_template('settings.html',
                               expenses=session.get('expenses'),
                               savings=session.get('savings'),
                               goals=session.get('goals'),
                               user_info=session.get('user_info')
                               )



@app.route('/settings_change', methods=['GET','POST'])
def settings_change():
    if request.method == 'GET':
        expenses = session.get('expenses')
        savings = session.get('savings')
        goals = session.get('goals')

        #create name for each input
        id_name = {}

        for key in expenses:
            id_name[key] = {
                'name': key + '_' + 'name' ,
                'value': key + '_' +'value'
                            }

        tag_savings = ['name', 'percent', 'value', 'goal','reserve']
        for key in savings:
            for tag in tag_savings:
                id_name.update({key:  { tag: tag + '_' + key } } )


        tag_goals = ['name', 'value', 'goal', 'date']
        for key in goals:
            for tag in tag_goals:
                id_name.update({key: {tag: tag + '_' + key} } )
        #
        print(f"\ndictionary for ids and names : {id_name}")

        return render_template('settings_change.html',
                               expenses=expenses,
                               savings=savings,
                               goals=goals,
                               id_name=id_name,
                               user_info=session.get('user_info')
                               )

    if request.method == 'POST':
        # check uniqness of all names

        return redirect ('/settings')

if __name__ == "__main__":
    app.run(debug=True)