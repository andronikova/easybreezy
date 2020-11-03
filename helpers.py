from flask import session, render_template
import datetime

from dateutil import relativedelta

from collections import OrderedDict

def load_savings(userid, savings_db):
    datas = savings_db.query.filter_by(userid=userid).all()

    savings = {}
    for row in datas:
        progress = round(100 * row.value / row.goal)
        if progress < 0 : progress = 0

        savings[row.name] = {
                             'goal':row.goal, 'value':row.value,
                             'percent':row.percent,
                             'progress':progress,
                             'for_bar':'width:'+ str( progress) +'%;' ,
                             'to_pay': 0
                             }

    print(f" savings info is loaded and saved in dict: \n{savings}")

    # save in session
    session['savings'] = savings


def load_expenses(userid, expenses_db):
    expenses = {}
    datas = expenses_db.query.filter_by(userid=userid).all()

    for row in datas:
        expenses[row.name] = {'value':row.value}



    # save in session
    session['expenses'] = expenses

    print(f"\nexpenses info is loaded and saved in dict: \n{session.get('expenses')}")


def load_user_info(userid, user_db):
    # def: load user info and save it in sesion
    datas = user_db.query.filter_by(userid=userid).all()

    if len(datas) == 0:
        return error('There is no such user.')
    elif len(datas) > 1:
        return error('There are few such user.')

    user_info = {
                    'reserve_account': datas[0].reserve_account
                 }

    session['user_info'] = user_info

    print(f"\nuser info is loaded and saved in dict:\n{user_info}")


def load_goals(userid, goals_db):
    goals = {}
    today = datetime.date.today()

    datas = goals_db.query.filter_by(userid=userid).all()

    for row in datas:
        #TODO chack that goal is not achieved

        # This will find the difference between the two dates
        difference = relativedelta.relativedelta(row.date, today)
        months = difference.months

        # calculate payments based on date and goal
        to_pay = (row.goal - row.value) / months

        # if date of goal passed
        if months < 0:
            to_pay = 0

        progress = round(100 * row.value / row.goal)

        goals[row.name] = {
            'value' : row.value,
            'goal' : row.goal,
            'date' : row.date.strftime('%Y-%m-%d'),
            'to_pay' : to_pay,
            'progress' : progress,
            'for_bar':'width:' + str(progress) + '%;'
        }

    print(f"\ngoals info is loaded and saved in dict: \n{goals} \n{len(goals)}")

    session['goals'] = goals


def money_distribution(userid):
    # DEF: calculate all payments taking in account salary value
    # 1 case: salary is not enough to cover expenses and sum to live -> take insufficient money from reserve account, don't pay savings and goals
    # 2 case: salary is enough to pay expenses, sum to live and some savings account -> distribute payments in saving account proportionally
    # 3 case: salary is not enough to pay all goals: distribute remain proportionally between all goals
    # 4 case: after all payments there are still remains: ask user what to do with it
    salary = session.get('salary')
    expenses = session.get('expenses')
    savings = session.get('savings')
    goals = session.get('goals')

    reserve = session.get('user_info')['reserve_account']

    # calculate saving payments using salary info
    savings = calc_payments_for_saving(savings, salary)

    remain = salary

    # subtract monthly fixed expenses
    for key in expenses:
        remain -= expenses[key]['value']

    # check that salary is enough for expenses
    if remain <= 0: #salary doesn't enough
        # took money from reserve account
        savings[reserve]['value'] += remain
        savings = update_progress(savings, reserve)
        remain = 0

        # put zero to pay value in savings and goals
        savings = put_zero_to_pay(savings)
        goals = put_zero_to_pay(goals)

        # generate message
        if savings[reserve]['value'] >= 0 : # we have enough money in reserves
            message = "Your salary isn't enough to cover expenses and living cost. We took money from reserve account ("\
                      + reserve + "). \nNo money went to savings and goals. "

        else: # we have not enough money in reserves
            message = "Your salary isn't enough to cover expenses and living cost. Your reserve account (" \
                      + reserve + ") also is not enough. :( Change your expenses and/or sum for living. "

        # end function
        return {'remain': remain, 'savings': savings, 'goals': goals,'message': message}

    # remain > 0 => salary is enough to cover expenses
    # now we can calculate payments for saving account

    # calculate sum of all saving payments
    savings_to_pay_sum = sum_of_paymetns(savings)

    # check for case 2 : salary is enough to pay expenses and some savings account
    if savings_to_pay_sum > remain: # we don't have enough money to pay all savings => should reduce payments
        # recalculate payments in savings
        savings = calc_payments_using_remains(remain,savings_to_pay_sum,savings)

        # update remain and goals
        remain = 0
        goals = put_zero_to_pay(goals)

        message = "Your income covers expenses, living sum and partially savings. " \
                  "Payments to saving accounts calculated proportionally from remain." \
                  "You don't have money to pay goals."

        # break function
        return {'remain': remain, 'savings': savings, 'goals': goals, 'message': message}

    elif savings_to_pay_sum == remain:
        # update remain and goals
        remain = 0
        goals = put_zero_to_pay(goals)

        message = "Your income covers expenses, living sum and all savings. \nBut you don't have money to pay goals."

        # break function
        return {'remain': remain, 'savings': savings, 'goals': goals, 'message': message}


    # case: income - expenses - living - savings > 0
    remain -= savings_to_pay_sum

    # calculate sum of all payments in goals
    goals_to_pay_sum = sum_of_paymetns(goals)

    if remain < goals_to_pay_sum: # salary is not enough to pay all goals -> distribute money proportionally (case 3)
        # recalculate payments in goals
        goals = calc_payments_using_remains(remain,goals_to_pay_sum, goals)

        remain = 0
        message = "Your income covers expenses, living sum, all savings. \n" \
                  "But you don't have money to pay full goals. " \
                  "\nWe distribute remains proportionally between all your goals."

    else: # salary is enough to pay all goals
        remain -= goals_to_pay_sum

        message = "You have enough money to pay expenses, living sum and all savings. You also have remains " \
              + str(remain) + "Please, add this remains whenever you want (we recommend add it to reserve account)."


    return {'remain': remain, 'savings': savings, 'goals': goals, 'message': message}



def update_progress(account, key):
    # DEF: using value recalculates progress and generates string for bar
    progress = round(100 * account[key]['value'] / account[key]['goal'])

    if progress < 0:
        progress = 0

    account[key]['progress'] = progress
    account[key]['for_bar'] = 'width:' + str(progress) + '%;'

    if progress >= 100: # for correct displaying
        account[key]['for_bar'] = 'width:' + str(100) + '%;'

    return account


def sum_of_paymetns(account):
    # DEF : to calculate sum of all payments for this account type
    sum_to_pay = 0

    for key in account:
        sum_to_pay += account[key]['to_pay']

    return sum_to_pay


def calc_payments_for_saving(savings, salary):
    # DEF: calculate payments for each saving account
    for key in savings:
        # check that we do not achieve goal for this savings
        # calculate insufficient sum
        insuf = savings[key]['goal'] - savings[key]['value']

        if insuf <= 0:  # we achieve the goal, pay nothing
            to_pay = 0

        else: # we don't achieve goal
            # calculate payments using percent info
            to_pay = round(salary * savings[key]['percent'] / 100)

            if insuf < to_pay: # if insufficient sum less than sum to pay - pay only insufficient sum
                to_pay = insuf

        savings[key].update({'to_pay': to_pay})

        return savings


def put_zero_to_pay(account):
    for key in account:
        account[key]['to_pay'] = 0

    return account

def calc_payments_using_remains(remains, to_pay_sum, account):
    # DEF : to recalculate to_pay proportionally for all item in account
    # proportion: to_pay / sum_to_pay = new_to_pay / remains
    sum_tmp = 0  # tmp variable to control rounding

    # for each saving account calculate proportion to take from remain
    for key in account:
        proportion = account[key]['to_pay'] / to_pay_sum
        account[key]['to_pay'] = round(proportion * remains)

        sum_tmp += account[key]['to_pay']

        last_key = kwy

    if sum_tmp != remains:  # we have rounding problem, compensate it by last account
        account[last_key]['to_pay'] += remains - sum_tmp

    return account




def save_in_history(db, history_expenses_db, history_accounts_db, history_salary_db):
    savings = session.get('savings')
    expenses = session.get('expenses')
    salary = session.get('salary')

    userid = session.get('userid')

    date = datetime.datetime.now().date()

    # load from some db rows with this date
    datas = history_expenses_db.query.filter_by(userid=userid,date=date).all()

    if len(datas) != 0 : # there are rows with the same date => dbs have been updated already today
        # save expenses
        for key in expenses:
            ret = history_expenses_db.query.filter_by(userid=userid, date=date, name=key).update(
                { 'to_pay': expenses[key]['value'] } )

            if ret == 0:  # row with name==key doesn't exist
                new_row = history_expenses_db(userid=userid, date=date, name=key, to_pay=expenses[key]['value']                                               )

                db.session.add(new_row)

        # save savings
        for key in savings:
            ret = history_accounts_db.query.filter_by(userid=userid, date=date, name=key).update(
                {
                    'to_pay': savings[key]['to_pay'],
                    'value' : savings[key]['value'] + savings[key]['to_pay']
                  }
            )

            if ret == 0: # row with name==key doesn't exist
                new_row = history_accounts_db(userid=userid,
                                              name=key,
                                              to_pay=savings[key]['to_pay'],
                                              value=savings[key]['value'] + savings[key]['to_pay'],
                                              date=date
                                              )
                db.session.add(new_row)

        # save salary
        ret = history_salary_db.query.filter_by(userid=userid, date=date).update({'value':salary})
        print(f"for salsary ret is {ret}")

        if ret == 0:
            new_row = history_salary_db(userid=userid, date=date, value=salary)
            db.session.add(new_row)

    else: # case when there is no record in db for this date
        # expenses
        for key in expenses:
            new_row = history_expenses_db(userid=userid,
                                         name=key,
                                         to_pay=expenses[key]['value'],
                                         date =date
                                         )
            db.session.add(new_row)

        # savings
        for key in savings:
            new_row = history_accounts_db(userid=userid,
                                          name=key,
                                          to_pay=savings[key]['to_pay'],
                                          value=savings[key]['value'] + savings[key]['to_pay'],
                                          date=date
                                          )
            db.session.add(new_row)

        # salary
        new_row = history_salary_db(userid=userid, date=date, value=salary)
        db.session.add(new_row)

    db.session.commit()

    return True


def load_history(history_salary_db, history_accounts_db,history_expenses_db):
    # DEF function to load all history dbs and save it in dictionary
    userid=session.get('userid')

    history = OrderedDict()

    data_salary = history_salary_db.query.filter_by(userid=userid).order_by(history_salary_db.date.desc()).all()

    for row in data_salary:
        history[row.date] = {'salary': row.value}

    data_expenses = history_expenses_db.query.filter_by(userid=userid).all()
    for row in data_expenses:
        history[row.date].update({row.name : row.to_pay})

    data_accounts = history_accounts_db.query.filter_by(userid=userid).all()
    for row in data_accounts:
        history[row.date].update({row.name: {'to_pay': row.to_pay, 'value': row.value}})

    print(f"history is {history}")
    return history


def logged():
    if session.get('userid') is None:
        return False

    return True


def error(message):

    return render_template('error_page.html', message=message)