from flask import session, render_template
import datetime

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

    print(f" expenses info is loaded and saved in dict: \n{expenses}")

    # save in session
    session['expenses'] = expenses


def load_user_info(userid, user_db):
    # def: load user info and save it in sesion
    datas = user_db.query.filter_by(userid=userid).all()

    if len(datas) == 0:
        return error('There is no such user.')
    elif len(datas) > 1:
        return error('There are few such user.')

    user_info = {
                    'sum_to_live': datas[0].sum_to_live,
                    'reserve_account': datas[0].reserve_account
                 }

    session['user_info'] = user_info

    print(f"\nuser info is loaded and saved in dict:\n{user_info}")


def money_distribution(salary,expenses,savings,sum_to_live, reserve):
    # DEF: calculate all payments taking in account salary value
    # 1 case: salary is not enough to cover expenses and sum to live -> take insufficient money from reserve account, don't pay savings and goals
    # 2 case: salary is enough to pay expenses, sum to live and some savings account -> distribute payments in saving account proportionally
    # 3 case: salary is not enough to pay all goals: distribute remain proportionally between all goals
    # 4 case: after all payments there are still remains: ask user what to do with it

    remain = salary
    message=''

    # subtract monthly fixed expenses
    for key in expenses:
        remain -= expenses[key]['value']

    # subtract sum for living
    remain -= sum_to_live

    # check that salary is enough
    if remain <= 0: #salary doesn't enough
        # took money from reserve account
        savings[reserve]['value'] += remain
        savings = update_progress(savings,reserve)
        remain = 0

        # put zero to pay value in savings
        for key in savings:
            savings[key].update({'to_pay': 0})

        # generate message
        if savings[reserve]['value'] >= 0 : # we have enough money in reserves
            message = "Your salary isn't enough to cover expenses and living cost. We took money from reserve account ("\
                      + reserve + "). \nNo money went to savings and goals. "

        else: # we have not enough money in reserves
            message = "Your salary isn't enough to cover expenses and living cost. Your reserve account (" \
                      + reserve + ") also is not enough. :( Change your expenses and/or sum for living. "

        # end function
        return {'remain': remain, 'savings': savings, 'message': message}


    # remain > 0 => salary is enough to cover expenses, sum_to_live and some savings
    # calculate payments to savings account
    for key in savings:
        # calculate payments using percent info
        to_pay = round(salary * savings[key]['percent'] / 100)

        # check that we do not achieve goal for this savings
        # calculate insufficient sum
        insuf = savings[key]['goal'] - savings[key]['value']

        if insuf <= 0:  # we achieve the goal, pay nothing
            to_pay = 0
        else: # we don't achieve goal
            if insuf < to_pay: # if insufficient sum less than sum to pay - pay only insufficient sum
                to_pay = insuf

        savings[key].update({'to_pay': to_pay})

    # calculate sum of all saving payments
    savings_to_pay_sum = 0
    for key in savings:
        savings_to_pay_sum += savings[key]['to_pay']

    # check for case 2
    if savings_to_pay_sum > remain: # we don't have enough money to pay all savings => should reduce payments
        sum_tmp = 0 # tmp variable to control rounding

        # for each saving account calculate proportion to take from remain
        for key in savings:
            proportion = savings[key]['to_pay'] / savings_to_pay_sum
            savings[key]['to_pay'] = round(proportion * remain)
            sum_tmp += savings[key]['to_pay']

        if sum_tmp != remain: # we have rounding problem, compensate it by reserve account
            savings[reserve]['to_pay'] += remain - sum_tmp

        # update remain
        remain = 0
        message = "Your income covers expenses, living sum and partially savings. " \
                  "Payments to saving accounts calculated proportionally from remain." \
                  "You don't have money to pay goals."

        # end function
        return {'remain': remain, 'savings': savings, 'message': message}

    elif savings_to_pay_sum == remain:
        remain = 0
        message = "Your income covers expenses, living sum and all savings. But you don't have money to pay goals."

        # end function
        return {'remain': remain, 'savings': savings, 'message': message}


    # income - expenses - living - savings > 0
    remain -= savings_to_pay_sum

    message = "You have enough money to pay expenses, living sum and all savings. You also have remains " \
              + str(remain) + "Please, add this remains whenever you want (we reccomend add it to reserve account)."

    # return remain, which could be used for living during this month
    return {'remain':remain,'savings':savings,'message':message}




def update_progress(savings,key):
    # DEF: using value recalculates progress and generates string for bar
    progress = round(100 * savings[key]['value'] / savings[key]['goal'])

    if progress < 0:
        progress = 0

    savings[key]['progress'] = progress
    savings[key]['for_bar'] = 'width:' + str(progress) + '%;'

    if progress >= 100: # for correct displaying
        savings[key]['for_bar'] = 'width:' + str(100) + '%;'

    return savings


def save_in_history(db, history_expenses_db, history_accounts_db):
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

    else: # case when there is no record in db for this date
        for key in expenses:
            new_row = history_expenses_db(userid=userid,
                                         name=key,
                                         to_pay=savings[key]['value'],
                                         date =date
                                         )
            db.session.add(new_row)

        for key in savings:
            new_row = history_accounts_db(userid=userid,
                                          name=key,
                                          to_pay=savings[key]['to_pay'],
                                          value=savings[key]['value'] + savings[key]['to_pay'],
                                          date=date
                                          )
            db.session.add(new_row)

    db.session.commit()

    return True



def logged():
    if session.get('userid') is None:
        return render_template('welcome.html')

    return True


def error(message):

    return render_template('error_page.html', message=message)