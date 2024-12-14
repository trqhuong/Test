import re
from datetime import date
from warnings import catch_warnings
from flask import render_template, request, redirect, flash, session, url_for
from app import app, dao, login_manager
from flask_login import login_user, logout_user, current_user
from app.models import Role
import smtplib
import random
import math



@app.route('/')
def index():
    date_today = date.today().strftime('%Y-%m-%d')

    page = request.args.get('page', 1, type=int)

    rooms = dao.load_room(page=page)
    count_room = math.ceil(dao.count_room() / app.config["PAGE_SIZE"])
    return render_template('index.html', date_today=date_today, rooms=rooms, count_room=count_room)

@app.route('/login-admin',methods=['post'])
def login_admin_process():
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password,role=Role.ADMIN)
        if user:
            login_user(user=user)

        return redirect('/admin')

@app.route('/login', methods=['GET', 'POST'])
def login():
    err_message = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username, password)
        if user:
            login_user(user)
            # session['username'] = user.username
            if user.role==Role.ADMIN:
                return redirect('/admin')
            elif user.role==Role.RECEPTIONIST:
                return redirect('/nvxemphong')
            else:
                return redirect('/')
        else:
            err_message = 'username or password is incorrect'

    return render_template('login.html', err_message=err_message)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    regex_username = '^[a-zA-Z0-9]+$'
    error_message = {}
    if request.method.__eq__('POST'):
        name = request.form.get('name')
        username_value = request.form.get('username')
        identification_card = request.form.get('identification')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm')
        email_value = request.form.get('email')
        phone_value = request.form.get('phone')

        customer_type = request.form.get('type')
        gender = request.form.get('gender')

        if not (re.fullmatch(r'\d{12}', identification_card) or re.fullmatch(r'\d{9}', identification_card)
                or re.fullmatch(r'[a-z][a-z0-9]{7}', identification_card, re.IGNORECASE)):
            error_message['err_identification_card'] = 'Identification card is invalid.'

        if dao.existence_check('username', username_value):
            error_message['err_username'] = 'Username is already taken.'

        if not re.fullmatch(regex_username, username_value):
            error_message['err_format'] = 'Invalid username. Only letters and numbers'

        if not password.__eq__(confirm_password):
            error_message['err_password'] = 'Password and confirm password do not match.'

        if '@' not in email_value:
            error_message['err_email'] = 'Email is invalid.'
        elif dao.existence_check('email', email_value):
            error_message['err_email'] = 'Email is already taken.'

        if len(phone_value) < 7 or len(phone_value) > 15:
            error_message['err_phone'] = 'Phone number must be between 7-15 digits.'
        elif dao.existence_check('phone', phone_value):
            error_message['err_phone'] = 'Phone number is already taken.'

        if error_message:
            return render_template('register.html', identification_card=identification_card,
                                   error_message=error_message, name=name, username=username_value,
                                   email=email_value
                                   , phone=phone_value, customer_type=customer_type, gender=gender)
        else:
            data = request.form.copy()
            del data['confirm']
            avatar = request.files.get('avatar')
            dao.add_customer(avatar=avatar, **data)
            flash('Welcome ' + name + ' to Hotel', 'Registered successfully')
            return redirect('/login')

    return render_template('register.html', customer_type='domestic', gender='male')


@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    err_message = ''
    step = int(request.form.get('step', '1'))
    print(step)

    if request.method.__eq__('POST'):
        if step == 1:
            account = request.form.get('account')
            user = dao.get_customer_by_account(account)
            session['user_id'] = user.id
            if user:
                send_email(user)
                return render_template('forgotPassword.html', step=2)
            else:
                err_message = 'username or email do not exist'

        elif step == 2:
            otp_code = request.form.get('otp')
            otp_code_sent = session.get('otp_code')
            if int(otp_code.strip()) == int(otp_code_sent):
                print("success step 2")
                return render_template('forgotPassword.html', step=3)
            else:
                err_message = 'OTP code do not match'

        elif step == 3:
            print("start step 2")
            session.pop('otp_code', None)  # Giải phóng bộ nhớ
            user_id = session.get('user_id')
            print(user_id)
            password = request.form.get('password')
            confirm_password = request.form.get('confirm')
            if password.__eq__(confirm_password):
                dao.change_password(user_id=user_id, new_password=password)
                flash('Please login', 'Changed password successfully')
                return redirect('/login')
            else:
                err_message = 'Password and confirm password do not match'

    return render_template('forgotPassword.html', err_message=err_message, step=step)


def send_email(user):
    email_sender = 'lehuuhau005@gmail.com'
    session['otp_code'] = str(random.randint(100000, 999999))
    message = f"Hello {str(user.name)}\n\nVerification code:{session['otp_code']}\n\nThanks,"
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_sender, 'wsja hdjk nfvn boih')
        server.sendmail(email_sender, user.email, message.encode('utf-8'))
    except Exception as e:
        print("Send mail ERROR: ", e)
    finally:
        server.quit()


@app.route('/room-detail/')
def room_detail():
    room_id = request.args.get('room_id')
    room = dao.load_room(room_id=room_id)
    return render_template('roomdetail.html', room=room)


@app.route('/booking/')
def booking():
    room_id = request.args.get('room_id')
    room = dao.load_room(room_id=room_id)
    date_today = date.today().strftime('%Y-%m-%d')

    username = session.get('username')
    customer = dao.get_customer_by_account(username)

    list_customer_type = dao.get_customer_type()

    return render_template('booking.html', date_today=date_today, room=room, name=customer.name, identification_card=customer.identification_card
                           ,customer_type=customer.customer_type.type, list_customer_type=list_customer_type)


@app.route('/nvxemphong')
def nvxemphong():
    return render_template('employees/nvxemphong.html')


@app.route('/nvbook')
def nvbook():
    return render_template('employees/nvbook.html')


@app.route('/nvcheckin')
def nvcheckin():
    return render_template('employees/nvcheckin.html')


@app.route('/nvcheckout')
def nvcheckout():
    return render_template('employees/nvcheckout.html')


@app.route('/account')
def account():
    return render_template('account.html')


@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    error_message = {}
    if request.method == 'POST':
        name = request.form.getlist('name')
        identification_card = request.form.getlist('identification_card')
        customer_type = request.form.getlist('customer_type')

        room_id = request.args.get('room_id')
        room = dao.load_room(room_id=room_id)
        date_today = date.today().strftime('%Y-%m-%d')

        length = int(len(name))
        for i in range(0, length):
            if not (re.fullmatch(r'\d{12}', identification_card[i]) or re.fullmatch(r'\d{9}', identification_card[i])
                    or re.fullmatch(r'[a-z][a-z0-9]{7}', identification_card[i], re.IGNORECASE)):
                error_message['err_identification_card'] = 'Identification card is invalid.'
                break
        if not dao.existence_check('identification_card', identification_card[0]):
            error_message['err_not_exist'] = 'A customer with an account must exist in the system.'

        if error_message:
            return render_template('booking.html', error_message=error_message, room=room, date_today=date_today,
                                   name_check=name, identification_card_check=identification_card, customer_type_check=customer_type,
                                   length=length)

    return render_template('reservation.html')




if __name__ == '__main__':
    from app import admin
    app.run(debug=True)
