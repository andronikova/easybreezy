from flask import Flask, request, render_template, session, redirect
from flask_migrate import Migrate
import os

from helpers import load_savings, logged, load_expenses

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
def input():
    session['userid'] = 1

    if request.method == "GET":
        logged()

        savings = load_savings(session.get('userid'), savings_db)
        expenses = load_expenses(session.get('userid'),expenses_db)

        return render_template('input.html',
                               savings=savings)


    if request.method == "POST":


        return  redirect('/output')


@app.route('/output', methods=['GET','POST'])
def output():
    if request.method == "GET":
        logged()

        return render_template('output.html')



if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()
