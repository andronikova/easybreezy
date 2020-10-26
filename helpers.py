from flask import session, render_template


def load_savings(userid, savings_db):
    datas = savings_db.query.filter_by(userid=userid).all()

    savings = {}
    for row in datas:
        progress = round(100 * row.value / row.goal)
        savings[row.name] = {'goal':row.goal, 'value':row.value,
                             'progress':progress, 'for_bar':'width:'+ str( progress) +'%;'}

    print(f" savings info is loaded and saved in dict: \n{savings}")

    return savings


def load_expenses(userid, expenses_db):
    expenses = {}
    datas = expenses_db.query.filter_by(userid=userid).all()

    for row in datas:
        expenses[row.name] = {'value':row.value}

    return expenses


def logged():
    if session.get('userid') is None:
        return render_template('welcome.html')

    return True