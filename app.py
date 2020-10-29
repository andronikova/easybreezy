from flask import Flask, request, render_template, session, redirect
from flask_migrate import Migrate
import os

from helpers import load_savings, logged, load_expenses, money_distribution, load_user_info, update_progress, \
    save_in_history,load_history

app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY_easybreezy')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                      "postgresql://postgres:1111111@localhost:5432/easybreezy"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# load databases
from models import db, user_db, savings_db, expenses_db, history_expenses_db, history_accounts_db, history_salary_db

# database settings and creation of tables
with app.app_context():
    db.init_app(app)
    migrate = Migrate(app,db)



@app.route('/', methods=['GET','POST'])
# @login_required  #TODO
def input():
    # session['userid'] = 1

    if request.method == "GET":

        if logged() is False:
            return render_template('welcome.html')

        # load info from db and save it in session
        load_savings(session.get('userid'), savings_db)
        load_expenses(session.get('userid'),expenses_db)

        load_user_info(session.get('userid'),user_db)

        return render_template('input.html',
                               savings=session.get('savings'),
                               expenses=session.get('expenses'),
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

        #save updated info in session
        session['expenses'] = expenses
        session['savings'] = savings

        print(f'\n\n-----USER INPUT processed and saved in session\n\nexpenses: {expenses} \n\nsavings:{savings}\n\nsalary:{session.get("salary")}')
        return redirect('/output')


@app.route('/output', methods=['GET','POST'])
def output():
    if request.method == "GET":
        # DEF: calculate all payments using info from session, show it to user
        logged()
        # load all info from session
        salary = session.get('salary')
        expenses = session.get('expenses')
        savings = session.get('savings')
        user_info = session.get('user_info')

        # check that there is enough money
        returned_dict = money_distribution(salary, expenses, savings, user_info['reserve_account'])

        savings = returned_dict['savings']
        remain = returned_dict['remain']
        message = returned_dict['message']


        return render_template('output.html',
                               salary=salary,
                               expenses=expenses,
                               savings = returned_dict['savings'],
                               remain=returned_dict['remain'],
                               message=returned_dict['message'],
                               user_info=user_info
                               )

    if request.method == "POST":
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


if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()
