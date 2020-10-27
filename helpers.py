from flask import session, render_template


def load_savings(userid, savings_db):
    datas = savings_db.query.filter_by(userid=userid).all()

    savings = {}
    for row in datas:
        progress = round(100 * row.value / row.goal)
        savings[row.name] = {'goal':row.goal, 'value':row.value,
                             'percent':row.percent,
                             'progress':progress, 'for_bar':'width:'+ str( progress) +'%;'}

    print(f" savings info is loaded and saved in dict: \n{savings}")

    # save in session
    session['savings'] = savings


def load_expenses(userid, expenses_db):
    expenses = {}
    datas = expenses_db.query.filter_by(userid=userid).all()

    for row in datas:
        expenses[row.name] = {'value':row.value}

    print(f" expenses info is loaded and saved in dict: \n{expenses}")

    # save in session
    session['expenses'] = expenses


def money_distribution(salary,expenses,savings):
    remain = salary

    # subtract monthly fixed expenses
    for key in expenses:
        remain -= expenses[key]['value']

    # calculate values to save in savings
    for key in savings:
        # calculate payments using percent info
        to_pay = remain * savings[key]['percent'] / 100

        # check that we do not achieve goal for this savings
        # calculate insufficient sum
        insuf = savings[key]['goal'] - savings[key]['value']

        if insuf <= 0:  # we achieve the goal, pay nothing
            to_pay = 0
        else: # we don't achieve goal
            if insuf < to_pay: # if insufficient sum less than sum to pay - pay only insufficient sum
                to_pay = insuf

        savings[key].update({'to_pay': to_pay})

    # subtract 'to pay' values in savings from remains
    for key in savings:
        remain -= savings[key]['to_pay']

    # return remain, which could be used for living during this month
    return remain


def logged():
    if session.get('userid') is None:
        return render_template('welcome.html')

    return True