from flask import session, render_template, redirect
import datetime

from dateutil import relativedelta

from collections import OrderedDict

def load_savings(userid, savings_db):
    datas = savings_db.query.filter_by(userid=userid).all()

    savings = {}
    for row in datas:
        # convert to dollar and cents
        goal = row.goal / 100
        value = row.value / 100

        progress = round(100 * value / goal)
        if progress < 0 : progress = 0

        savings[row.name] = {
                             'goal': goal,
                                'value':value,
                             'percent':row.percent,
                             'progress':progress,
                             'progress_tooltip': '{0:.0f}'.format(value) + '/' + '{0:.0f}'.format(goal)   ,
                             'for_bar':'width:'+ str( progress) +'%;' ,
                             'to_pay': 0
                             }

    print(f" savings info is loaded and saved in dict: \n{savings}")

    # save in session
    session['savings'] = savings


def load_goals(userid, goals_db):
    # def: load goals info and save it in session
    goals = {}

    datas = goals_db.query.filter_by(userid=userid).all()

    for row in datas:
        # This will find the difference between the two dates
        difference = relativedelta.relativedelta(row.date, datetime.date.today())
        years = difference.years
        months = difference.months + 12 * years

        # convert to dollar and cents
        goal = row.goal / 100
        value = row.value / 100

        # calculate payments based on date and goal
        if months <= 0 or (goal - value) < 0: # date of goal passed or goal has been achieved
            to_pay = 0
        else:
            to_pay = round(100 * (goal - value) / months) / 100

        progress = round(100 * value / goal)

        goals[row.name] = {
            'value' : value,
            'goal' : goal,
            'date' : row.date.strftime('%Y-%m-%d'),
            'to_pay' : to_pay,
            'progress' : progress,
            'for_bar':'width:' + str(progress) + '%;' ,
            'progress_tooltip': '{0:.0f}'.format(value) + '/' + '{0:.0f}'.format(goal),
            'to_pay_to_achieve': to_pay   # sum you have to pay to achieve goal
        }

    print(f"\ngoals info is loaded and saved in dict: \n{goals} \n{len(goals)}")

    session['goals'] = goals



def load_expenses(userid, expenses_db):
    expenses = {}
    datas = expenses_db.query.filter_by(userid=userid).all()

    for row in datas:
        # division by 100 to convert to euro and cents (in db values are saved as integer)
        expenses[row.name] = {'value':row.value / 100}

    # save in session
    session['expenses'] = expenses

    print(f"\nexpenses info is loaded and saved in dict: \n{session.get('expenses')}")


def load_user_info(userid, user_db):
    # def: load user info and save it in session
    datas = user_db.query.filter_by(userid=userid).all()

    if len(datas) == 0:
        session['error_message'] = 'There is no such user.'
        return False
    elif len(datas) > 1:
        session['error_message'] = 'There are few such user.'
        return False

    user_info = {
                    'reserve_account': datas[0].reserve_account,
                    'email' : datas[0].email
                 }

    session['user_info'] = user_info

    print(f"\nuser info is loaded and saved in dict:\n{user_info}")


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
    if remain < 0: #salary doesn't enough
        # took money from reserve account

        #check, that reserve account  is real account in savings
        if reserve not in savings:
            error_message = "Your income is less than your expenses. In this situation you can take missing  value from reserve account. But you don't choose reserve account. Please, go to settings -> change accounts parameters."
            session['error_message'] = error_message
            print('XXXXX: error message: {}'.format(error_message))
            return False

        savings[reserve]['value'] += remain
        savings = update_progress(savings, reserve)
        remain = 0

        # put zero to pay value in savings and goals
        savings = put_zero_to_pay(savings)
        goals = put_zero_to_pay(goals)

        # generate message
        if savings[reserve]['value'] >= 0 : # we have enough money in reserves
            message = "Your salary isn't enough to cover expenses and living cost. We took money from reserve account ("\
                      + reserve + "). \nNo money for savings and goals. "

        else: # we have not enough money in reserves
            error_message = "Your salary isn't enough to cover expenses and living cost. Your reserve account (" \
                      + reserve + ") also is not enough. :( Change your expenses and/or sum for living. "
            session['error_message'] = error_message
            print('XXXXX: error message: {}'.format(error_message))
            return False

        # end function
        return {'remain': remain, 'savings': savings, 'goals': goals,'message': message}

    # remain > 0 => salary is enough to cover expenses

    # now we can calculate payments for saving account
    for key in savings:
        # check that goal is not achieved
        if savings[key]['goal'] > savings[key]['value']:
            savings[key]['to_pay'] = savings[key]['percent'] * salary / 100
        else:
            savings = put_zero_to_pay(savings)

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

        message = "You have enough money to pay all your accounts. You also have nonzero remains. Add it whenever you want."


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

        last_key = key

    if sum_tmp != remains:  # we have rounding problem, compensate it by last account
        account[last_key]['to_pay'] += remains - sum_tmp

    return account


def save_in_history(db, history_db,expenses,savings, goals, salary):
    # in db i save sums in integer format, to obtain float format (euro + cents) you should divide by 100
    # db / 100 = euro+cents; euro+cents * 100 = db format
    userid = session.get('userid')
    today_date = datetime.datetime.now().date()

    # for expenses: create lists of names and and values
    expenses_name, expenses_value = [],[]
    for key in expenses:
        expenses_name.append(key)
        expenses_value.append(expenses[key]['value'] * 100)

    # for savings: create lists of names, to_pay and values
    savings_name, savings_to_pay, savings_value = [],[],[]
    for key in savings:
        savings_name.append(key)
        savings_to_pay.append( savings[key]['to_pay'] * 100)
        savings_value.append(savings[key]['value'] * 100)

    # for goals: create lists of name, to_pay and values
    goals_name, goals_value, goals_to_pay = [],[],[]
    for key in goals:
        goals_name.append(key)
        goals_to_pay.append(goals[key]['to_pay'] * 100)
        goals_value.append(goals[key]['value'] * 100)

    # check that this date doesn't exist in db
    datas = history_db.query.filter_by(userid=userid,date=today_date).all()

    if len(datas) == 0: # there is no such date in history = > add new row
        # find out last id in db
        if len(history_db.query.all()) == 0: # db is empty
            max_id = 0
        else:
            max_id = history_db.query.order_by(history_db.id.desc()).first().id

        new_row = history_db(id=max_id + 1 ,
                             userid=userid,
                             salary=salary * 100,
                             savings_name=savings_name, savings_to_pay=savings_to_pay, savings_value=savings_value,
                             goals_name=goals_name, goals_to_pay=goals_to_pay, goals_value=goals_value,
                             expenses_name=expenses_name, expenses_value=expenses_value,
                             date=today_date
                             )

        db.session.add(new_row)
        print('new row is added to history_db')

    elif len(datas) == 1: # there is such date in the history => rewrite
        ret = history_db.query.filter_by(userid=userid, date=today_date).update({
            'salary' : salary * 100,
            'savings_name' : savings_name, 'savings_to_pay':savings_to_pay, 'savings_value' : savings_value,
            'goals_name':goals_name,       'goals_to_pay':goals_to_pay,     'goals_value' : goals_value,
            'expenses_name' : expenses_name, 'expenses_value':expenses_value
        })
        print('rewrite row for this date in history_db')

    db.session.commit()

    return True


def load_history(history_db):
    # DEF function to load all history dbs and save it in dictionary
    userid=session.get('userid')

    history = OrderedDict()

    datas = history_db.query.filter_by(userid=userid).order_by(history_db.date.desc()).all()

    for row in datas:
        history[row.date] = { 'salary' : row.salary / 100}

        expenses_name = row.expenses_name

        print('expenses in history: {}'.format(row.expenses_name))
        if expenses_name is not None:
            for i in range(len(expenses_name)):
                print(i, expenses_name[i])
                history[row.date][expenses_name[i]] = {'value': row.expenses_value[i] / 100}


        savings_name = row.savings_name
        if savings_name is not None:
            for i in range(len(savings_name)):
                history[row.date][savings_name[i]] = { 'value': row.savings_value[i] / 100, 'to_pay':row.savings_to_pay[i] / 100}

        goals_name = row.goals_name
        if goals_name is not None:
            for i in range(len(goals_name)):
                history[row.date][goals_name[i]] = { 'value': row.goals_value[i] / 100, 'to_pay':row.goals_to_pay[i] / 100}


    print(f"\n\n history is \n{history}")
    return history


def create_ids_dict(ids, account, tag_list):
    # DEF : to create dictionary of account names and tags
    for key in account:
        ids.update({key:{}})

        for tag in tag_list:
            ids[key].update({tag: tag + '_' + key} )

    return ids


def logged():
    if session.get('userid') is None:
        return False

    return True


