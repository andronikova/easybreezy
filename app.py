from flask import Flask, request, render_template, session, redirect
from flask_migrate import Migrate
import os

from helpers import load_savings, logged, load_expenses, money_distribution

app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY_rebalanceme')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                      "postgresql://postgres:1111111@localhost:5432/easybreezy"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# load databases
from models import db, user_db, savings_db, expenses_db

# database settings and creation of tables
with app.app_context():
    db.init_app(app)
    migrate = Migrate(app,db)



@app.route('/', methods=['GET','POST'])
# @login_required  #TODO
def input():
    session['userid'] = 1

    if request.method == "GET":

        logged()

        # call functions that save info in session
        load_savings(session.get('userid'), savings_db)
        load_expenses(session.get('userid'),expenses_db)

        return render_template('input.html',
                               savings=session.get('savings'),
                               expenses=session.get('expenses'))


    if request.method == "POST":
        # save salary
        session['salary'] = request.form.get('salary')

        #for all saving types load current value from input page
        savings = session.get('savings')
        for key in savings:
            new_value = request.form.get(key)
            # save this value in session
            savings[key]['value'] = new_value

        # for all expenses load value from input page
        expenses = session.get('expenses')
        for key in expenses:
            new_value = request.form.get(key)
            # save new value in the session
            expenses[key]['value'] = new_value

        return  redirect('/output')


@app.route('/output', methods=['GET','POST'])
def output():
    if request.method == "GET":
        logged()
        # load all info from session
        salary = session.get('salary')
        expenses = session.get('expenses')
        savings = session.get('expenses')

        # check that there is enough money
        remain = money_distribution(salary, expenses, savings)

        # if not - ask, what to do
        # if there is excess  -ask what to do
        # final calulation

        return render_template('output.html')

    if request.method == "POST":
        # save new values in session

        # go to page with calculation
        return  redirect('/output')



if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()
