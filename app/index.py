import re
from datetime import date, datetime
from warnings import catch_warnings
from flask import render_template, request, redirect, flash, session, jsonify, url_for
from sqlalchemy import table
from sqlalchemy.orm import joinedload
from app.models import Guest, RoomReservationForm, Customer, Role, User, RoomRentalForm, BookingStatus, Comment, Bill
from app import app, dao, login_manager, utils, VNPAY_CONFIG, db
from flask_login import login_user, logout_user, login_required, current_user
import smtplib
import random
import math
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from app.dao import cancel_form

from app.utils import total_price


@app.route('/')
def index():
    current_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M')
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')
    room_type = request.args.get('room-type')
    popup = False
    if 'act' in session:
        session.pop('act')

    if checkin:
        checkin = datetime.strptime(checkin, '%Y-%m-%dT%H:%M')
    if checkout:
        checkout = datetime.strptime(checkout, '%Y-%m-%dT%H:%M')

    if checkin and checkout:
        if checkin > checkout:
            popup = True

    page = request.args.get('page', 1, type=int)

    rooms, length = dao.load_room(checkin=checkin, checkout=checkout, page=page, room_type=room_type)
    count_room = math.ceil(length / app.config["PAGE_SIZE"])

    return render_template('index.html', popup=popup, current_datetime=current_datetime, rooms=rooms,
                           count_room=count_room
                           , checkin=checkin, checkout=checkout, room_type=room_type)


@app.route('/login', methods=['GET', 'POST'])
def login():
    err_message = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username, password)
        if user:
            login_user(user)
            session['username'] = user.username
            if user.role == Role.ADMIN:
                return redirect('/admin')
            elif user.role == Role.RECEPTIONIST:
                return redirect('/nvcheckin')
            else:
                return redirect('/')
        else:
            err_message = 'username or password is incorrect'

    return render_template('login.html', err_message=err_message)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/login-admin', methods=['post'])
def login_admin_process():
    username = request.form.get('username')
    password = request.form.get('password')
    user = dao.auth_user(username=username, password=password, role=Role.ADMIN)
    if user:
        login_user(user=user)

    return redirect('/admin')


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

        if dao.existence_check(Customer, 'username', username_value):
            error_message['err_username'] = 'Username is already taken.'

        if not re.fullmatch(regex_username, username_value):
            error_message['err_format'] = 'Invalid username. Only letters and numbers'

        if not password.__eq__(confirm_password):
            error_message['err_password'] = 'Password and confirm password do not match.'

        if '@' not in email_value:
            error_message['err_email'] = 'Email is invalid.'
        elif dao.existence_check(Customer, 'email', email_value):
            error_message['err_email'] = 'Email is already taken.'

        if len(phone_value) < 7 or len(phone_value) > 15:
            error_message['err_phone'] = 'Phone number must be between 7-15 digits.'
        elif dao.existence_check(Customer, 'phone', phone_value):
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
    # chưa lấy lại được tài khoản User
    if request.method.__eq__('POST'):
        if step == 1:
            account = request.form.get('account')
            user = dao.get_customer_by_account(User, account)
            if user:
                session['user_id'] = user.id
                send_email(user)
                return render_template('forgotPassword.html', step=2)
            else:
                err_message = 'username or email do not exist'

        elif step == 2:
            otp_code = request.form.get('otp')
            otp_code_sent = session.get('otp_code')
            if int(otp_code.strip()) == int(otp_code_sent):
                return render_template('forgotPassword.html', step=3)
            else:
                err_message = 'OTP code do not match'

        elif step == 3:
            session.pop('otp_code', None)  # Giải phóng bộ nhớ
            user_id = session.get('user_id')
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


def send_form(user_id=None, form=None, form_id=None):
    email_sender = 'lehuuhau005@gmail.com'

    room = None
    price = ""
    if form and form == 'Reservation':
        room = dao.get_form(table=RoomReservationForm)

        price = f"""
                    <!-- Total Price -->
                    <div style="margin-top: 20px; font-size: 16px;">
                        <p><strong>Total Price:</strong> {'{:,.0f}'.format(room.total_amount)} VNĐ</p>
                        <p style="color: green;"><strong>Paid:</strong> {'{:,.0f}'.format(room.deposit)} VNĐ</p>
                    </div>
            """
    elif form and form == 'Rental':
        room = dao.get_form(table=RoomRentalForm)
    elif form and form == 'Bill' and form_id:
        room = dao.get_form(table=RoomRentalForm, form_id=form_id)
        price = f"""
                    <!-- Total Price -->
                    <div style="margin-top: 20px; font-size: 16px;">
                        <p style="color: green;"><strong>Paid:</strong> {'{:,.0f}'.format(room.total_amount)} VNĐ</p>
                    </div>
            """
    if room:
        guests = room.guest
        customer = room.customer
        table_guest = ""
        for idx, guest in enumerate(guests, start=2):
            table_guest += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 10px;">{idx}</td>
                    <td style="border: 1px solid #ddd; padding: 10px;">{guest.name}</td>
                    <td style="border: 1px solid #ddd; padding: 10px;">{guest.customer_type.type}</td>
                    <td style="border: 1px solid #ddd; padding: 10px;">{guest.identification_card}</td>
                </tr>
            """

        table_customer = f"""
            <!-- Customer Table -->
                <h3 style="margin-top: 20px; color: #333;">Customer Details</h3>
                <table style="width: 100%; border-collapse: collapse; text-align: center;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="border: 1px solid #ddd; padding: 10px;">Order</th>
                            <th style="border: 1px solid #ddd; padding: 10px;">Customer</th>
                            <th style="border: 1px solid #ddd; padding: 10px;">Customer-type</th>
                            <th style="border: 1px solid #ddd; padding: 10px;">Identification</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 10px;">1</td>
                            <td style="border: 1px solid #ddd; padding: 10px;">{customer.name}</td>
                            <td style="border: 1px solid #ddd; padding: 10px;">{customer.customer_type.type}</td>
                            <td style="border: 1px solid #ddd; padding: 10px;">{customer.identification_card}</td>
                        </tr>
                        {table_guest}
                    </tbody>
                </table>
                {price}
        """

        if user_id:
            html_content = f"""
                <!DOCTYPE html>
                    <html>
                        <body style="font-family: Arial, sans-serif;">
                            <!-- Header -->
                            {'<h2 style="text-align: center; color: #333;">Rental Details</h2>' if form and form == 'Rental'
            else '<h2 style="text-align: center; color: #333;">Reservation Details</h2>'}               
    
                            <!-- Reservation Information -->
                            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                                <thead>
                                    <tr style="background-color: #f2f2f2;">
                                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Booking: {customer.name}
                                        </th>
                                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Room: {room.room.name}
                                        </th>
                                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Receptionist</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Check-in time: {room.check_in_date}
                                        </td>
                                        <td style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Check-out time: {room.check_out_date}
                                        </td>
                                        <td style="border: 1px solid #ddd; padding: 10px; text-align: left;">{current_user.name}</td>
                                    </tr>
                                </tbody>
                            </table>
                            {table_customer}
                        </body>
                    </html>
    
                    """
        else:
            html_content = f"""
                <!DOCTYPE html>
                    <html>
                        <body style="font-family: Arial, sans-serif;">
                            <!-- Header -->
                            {'<h2 style="text-align: center; color: #333;">Bill</h2>' if form and form == 'Bill' 
                            else '<h2 style="text-align: center; color: #333;">Reservation Details</h2>'}
    
                            <!-- Reservation Information -->
                            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                                <thead>
                                    <tr style="background-color: #f2f2f2;">
                                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Booking: {customer.name}
                                        </th>
                                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Room: {room.room.name}
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Check-in time: {room.check_in_date}
                                        </td>
                                        <td style="border: 1px solid #ddd; padding: 10px; text-align: left;">
                                            Check-out time: {room.check_out_date}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                            {table_customer}
                        </body>
                    </html>
                    """

        msg = MIMEMultipart("alternative")
        if form == 'Reservation':
            msg["Subject"] = "Room Reservation Form"
        elif form == 'Rental':
            msg["Subject"] = "Room Rental Form"
        elif form == 'Bill':
            msg["Subject"] = "Bill"
        msg["From"] = email_sender
        msg["To"] = customer.email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_sender, 'wsja hdjk nfvn boih')
            server.sendmail(email_sender, customer.email, msg.as_string())
            print("done")
        except Exception as e:
            print("Send mail ERROR: ", e)
        finally:
            server.quit()

    else:
        return False


@app.route('/room-detail/')
def room_detail():
    room_id = request.args.get('room_id')
    room = dao.load_room(room_id=room_id)
    comments = dao.load_comment(room_id=room_id)
    current_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M')

    return render_template('roomdetail.html', room=room, current_datetime=current_datetime, comments=comments)


@app.route('/api/check_room_availability', methods=['POST'])
def check_room_availability():
    room_id = request.json.get('room_id')
    checkin = request.json.get('checkin')
    checkout = request.json.get('checkout')

    session['checkin'] = checkin
    session['checkout'] = checkout

    checkin = datetime.strptime(checkin, '%Y-%m-%dT%H:%M')
    checkout = datetime.strptime(checkout, '%Y-%m-%dT%H:%M')
    is_available = dao.check_room_availability(checkin=checkin, checkout=checkout, room_id=room_id)

    return jsonify({
        'isAvailable': is_available
    })


@app.route('/booking/')
@login_required
def booking():
    room_id = request.args.get('room_id')
    room = dao.load_room(room_id=room_id)
    current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M")

    list_customer_type = dao.get_customer_type()
    if current_user.role == Role.CUSTOMER:
        username = session.get('username')
        customer = dao.get_customer_by_account(Customer, username)
        return render_template('booking.html', current_datetime=current_datetime, room=room, name=customer.name,
                               identification_card=customer.identification_card
                               , customer_type=customer.customer_type.type, list_customer_type=list_customer_type
                               , checkin=session.get('checkin'), checkout=session.get('checkout'))
    elif current_user.role == Role.RECEPTIONIST:
        session['user_id'] = current_user.id
        return render_template('booking.html', current_datetime=current_datetime, room=room,
                               list_customer_type=list_customer_type
                               , checkin=session.get('checkin'), checkout=session.get('checkout'))


@app.route('/api/check_account', methods=['POST'])
def check_account():
    list_name = request.json.get('listName')
    list_id = request.json.get('listId')
    list_customer_type = request.json.get('listCustomerType')

    checkin = request.json.get('checkin')
    checkout = request.json.get('checkout')
    room_id = request.json.get('roomId')
    act = request.json.get('act')

    room = dao.load_room(room_id=room_id)

    checkin_date = datetime.strptime(checkin, '%Y-%m-%dT%H:%M')
    checkout_date = datetime.strptime(checkout, '%Y-%m-%dT%H:%M')

    day = checkout_date - checkin_date

    length = len(list_name)
    customer = dao.existence_check(Customer, 'identification_card', list_id[0])

    session['guest'] = []
    session['checkin'] = checkin
    session['checkout'] = checkout
    user_id = session.get('user_id')

    if customer:
        session['customer'] = {
            'name': customer.name,
            'identification_card': customer.identification_card,
            'customer_type': customer.customer_type.type
        }
        for i in range(1, length):
            guest = {
                'name': list_name[i],
                'identification_card': list_id[i],
                'customer_type': list_customer_type[i]
            }

            session['guest'].append(guest)

        total_amount = utils.total_price(room.room_type.price, day.days, length, list_customer_type, room_id)

        if act:  # Nhan vien dat/thue
            session['act'] = act
            if act == 'Reservation':
                session['room_reservation_form'] = {
                    'order_id': f"reservation-{room_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'check_in_date': checkin,
                    'check_out_date': checkout,
                    'deposit': total_amount * 0.3,
                    'room_id': room_id,
                    'customer_id': customer.cus_id,
                    'total_amount': total_amount,
                    'user_id': user_id
                }
            elif act == 'Rent':
                session['room_rental_form'] = {
                    'check_in_date': checkin,
                    'check_out_date': checkout,
                    'total_amount': total_amount,
                    'user_id': user_id,
                    'customer_id': customer.cus_id,
                    'room_id': room_id
                }
        else:  # Khach hang dat
            session['room_reservation_form'] = {
                'order_id': f"reservation-{room_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'check_in_date': checkin,
                'check_out_date': checkout,
                'deposit': total_amount * 0.3,
                'room_id': room_id,
                'customer_id': customer.cus_id,
                'total_amount': total_amount
            }

        return jsonify({
            'success': True
        })

    return jsonify({
        'success': False
    })


def handle_save_form(obj, customer, list_guest, user_id, form):
    form_common = None
    if form == 'Reservation':
        form_common = RoomReservationForm(check_in_date=obj['check_in_date'],
                                          check_out_date=obj['check_out_date'],
                                          deposit=obj['deposit'],
                                          total_amount=obj['total_amount'],
                                          room_id=obj['room_id'], customer_id=customer.cus_id,
                                          user_id=user_id)
    elif form == 'Rental':
        form_common = RoomRentalForm(check_in_date=obj['check_in_date'],
                                     check_out_date=obj['check_out_date'],
                                     total_amount=obj['total_amount'],
                                     room_id=obj['room_id'],
                                     customer_id=customer.cus_id,
                                     user_id=user_id)
    arr_guest = []
    if list_guest and form_common:
        for guest in list_guest:
            g = dao.existence_check(Guest, 'identification_card', guest['identification_card'])
            if g:
                if form == 'Reservation':
                    g.room_reservation_form.append(form_common)
                elif form == 'Rental':
                    g.room_rental_form.append(form_common)
            else:
                if guest['customer_type'].__eq__('Domestic'):
                    type = 1
                else:
                    type = 2
                g = Guest(name=guest['name'], identification_card=guest['identification_card'], customer_type_id=type)

                if form == 'Reservation':
                    g.room_reservation_form.append(form_common)
                elif form == 'Rental':
                    g.room_rental_form.append(form_common)
                arr_guest.append(g)
    db.session.add(form_common)
    db.session.add_all(arr_guest)
    db.session.commit()


@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    room_id = request.args.get('room_id')
    room = dao.load_room(room_id=room_id)
    length = len(session.get('guest'))

    if request.method.__eq__('POST'):  # Nhan vien thue phong
        room_rental_form = session.get('room_rental_form')
        customer = dao.get_customer_by_account(Customer, session['customer']['identification_card'])
        list_guest = session.get('guest')
        user_id = session.get('user_id')
        handle_save_form(obj=room_rental_form, customer=customer, list_guest=list_guest, user_id=user_id, form='Rental')
        send_form(user_id=user_id, form='Rental')
        flash('Please check your email', 'Successfully created rental receipt.')
        session.pop('act', None)
        session.pop('checkin', None)
        session.pop('checkout', None)

        return redirect('/')

    return render_template('reservation.html', room=room, length=length, act=session.get('act', 'Reservation'))


@app.route('/payment', methods=['GET', 'POST'])
def payment():
    payment_type = request.form.get('payment_type')
    rental_id = request.form.get('rental_id')
    if payment_type and rental_id:
        room_rental_form = dao.get_form_by_id(RoomRentalForm, int(rental_id))
        amount = room_rental_form.total_amount
        order_id = f'Rental-{room_rental_form.room_id}-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    else:
    # Lấy thông tin thanh toán từ người dùng
        amount = session['room_reservation_form']['deposit']  # Số tiền thanh toán (VNĐ)
        order_id = session['room_reservation_form']['order_id']
    vnp = dao.vnpay()
    # Xây dựng hàm cần thiết cho vnpay
    vnp.requestData['vnp_Version'] = '2.1.0'
    vnp.requestData['vnp_Command'] = 'pay'
    vnp.requestData['vnp_TmnCode'] = VNPAY_CONFIG['vnp_TmnCode']
    vnp.requestData['vnp_Amount'] = str(int(amount * 100))
    vnp.requestData['vnp_CurrCode'] = 'VND'
    vnp.requestData['vnp_TxnRef'] = order_id
    vnp.requestData['vnp_OrderInfo'] = 'Thanhtoan'  # Nội dung thanh toán
    vnp.requestData['vnp_OrderType'] = 'hotel'

    vnp.requestData['vnp_Locale'] = 'vn'

    vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp.requestData['vnp_IpAddr'] = "127.0.0.1"
    vnp.requestData['vnp_ReturnUrl'] = url_for('vnpay_return', payment_type=payment_type, rental_id=rental_id, _external=True)

    vnp_payment_url = vnp.get_payment_url(VNPAY_CONFIG['vnp_Url'], VNPAY_CONFIG['vnp_HashSecret'])

    return redirect(vnp_payment_url)


@app.route('/vnpay_return', methods=['GET'])
def vnpay_return():
    vnp_ResponseCode = request.args.get('vnp_ResponseCode')
    payment_type = request.args.get('payment_type')
    rental_id = request.args.get('rental_id')
    if vnp_ResponseCode == '00':
        if payment_type and payment_type == 'rental':
            room_rental_form = dao.get_form_by_id(RoomRentalForm, int(rental_id))
            room_rental_form.status = BookingStatus.COMPLETED

            room_reservation_form_id = room_rental_form.room_reservation_form_id
            if room_reservation_form_id:
                room_reservation_form = dao.get_form_by_id(RoomReservationForm, int(room_reservation_form_id))
                room_reservation_form.status = BookingStatus.COMPLETED
            bill = Bill(total_price=room_rental_form.total_amount, user_id=current_user.id, room_rental_form_id=room_rental_form.id)
            db.session.add(bill)
            db.session.commit()
            send_form(form='Bill', form_id=rental_id)
            flash('Payment success', 'Payment result')
            return redirect('/nvcheckin')
        else:
            list_guest = session.get('guest')
            room_reservation_form = session.get('room_reservation_form')
            user_id = None

            if current_user.role == Role.CUSTOMER:
                username = session.get('username')
                customer = dao.get_customer_by_account(Customer, username)

            elif current_user.role == Role.RECEPTIONIST:
                customer = dao.get_customer_by_account(Customer, session['customer']['identification_card'])
                user_id = session.get('user_id')

            handle_save_form(obj=room_reservation_form, customer=customer, list_guest=list_guest, user_id=user_id,
                             form='Reservation')
            send_form(user_id=user_id, form='Reservation')
            flash('Payment success', 'Payment result')
            session.pop('act', None)
            session.pop('checkin', None)
            session.pop('checkout', None)

    else:
        flash('Payment failed', 'Payment result')

    return redirect('/')


@app.route('/nvcheckin')
def checkin():
    reservation_id = request.args.get('reservation-id')
    if reservation_id: #Nhan vien click check-in
        room_reservation_form = dao.get_form_by_id(RoomReservationForm, int(reservation_id))
        current_datetime = datetime.now()
        reservation_date = room_reservation_form.check_in_date
        if (reservation_date.date() >= current_datetime.date() and reservation_date.time() <= current_datetime.time()):
            room_reservation_form.status = BookingStatus.IN_USE
            room_rental_form = RoomRentalForm(check_in_date=room_reservation_form.check_in_date,
                                              check_out_date=room_reservation_form.check_out_date,
                                              total_amount=room_reservation_form.total_amount - room_reservation_form.deposit,
                                              user_id=current_user.id,
                                              customer_id=room_reservation_form.customer_id,
                                              room_id=room_reservation_form.room_id,
                                              room_reservation_form_id=room_reservation_form.id)
            for guest in room_reservation_form.guest:
                guest.room_rental_form.append(room_rental_form)
            db.session.add(room_rental_form)
            db.session.commit()
            send_form(user_id=current_user.id, form='Rental')
            flash("Room rental form has been successfully sent. Please check your email.", "Checkin Successful")
        else:
            flash("Not yet the check-in date.", "Error")

    customer_id = request.args.get('customer_id')
    room_reservation_form = dao.get_reservation_form_not_exist_rental(customer_id=customer_id)
    return render_template('employees/nvcheckin.html', room_reservation_form=room_reservation_form,
                           customer_id=customer_id)


@app.route('/nvcheckout')
def checkout():
    rental_id = request.args.get('rental-id')
    customer_id = request.args.get('customer-id')
    if rental_id:
        return redirect(f'/bill?rental-id={rental_id}')
    room_rental_form = dao.get_room_rental_form_all(customer_id=customer_id)
    return render_template('employees/nvcheckout.html', room_rental_form=room_rental_form)


@app.route('/bill')
def bill():
    rental_id = request.args.get('rental-id')
    room_rental_form = dao.get_form_by_id(RoomRentalForm, int(rental_id))
    reservation_id = room_rental_form.room_reservation_form_id
    room_reservation_form = ''
    if reservation_id:
        room_reservation_form = dao.get_form_by_id(RoomReservationForm, int(reservation_id))
    return render_template('bill.html', room_rental_form=room_rental_form, room_reservation_form=room_reservation_form)


@app.route('/rental_history')
def rental_history():
    list_rented_rooms = None
    if current_user.role == Role.CUSTOMER:
        username = session.get('username')
        customer = dao.get_customer_by_account(Customer, username)
        list_rented_rooms = dao.get_rented_room(customer.cus_id)
    return render_template('rental_history.html', list_rented_rooms=list_rented_rooms)


@app.route('/api/comment', methods=['POST'])
def comment():
    content = request.json.get('content')
    room_id = request.json.get('roomId')
    rental_id = request.json.get('rentalId')

    username = session.get('username')
    customer = dao.get_customer_by_account(Customer, username)
    room_rental_form = dao.get_form_by_id(RoomRentalForm, int(rental_id))

    room_rental_form.is_review = True
    cmt = Comment(content=content, room_id=room_id, customer_id=customer.cus_id)
    db.session.add(cmt)
    db.session.commit()

    return jsonify({
        'isSuccess': True
    })


@app.route('/account', methods=['GET'])
def account():
    user_id = session.get('_user_id')
    user = dao.get_user_by_id(user_id)
    customer = Customer.query.filter_by(User_id=user_id).first()
    if '_user_id' not in session:
        return redirect(url_for('login'))

    return render_template('account.html', user=user, customer=customer)


@app.route('/account/edit', methods=['GET', 'POST'])
def edit_account():
    user_id = session.get('_user_id')
    user = dao.get_user_by_id(user_id)
    user = db.session.query(User).options(joinedload(User.customer)).filter_by(id=user_id).first()
    if '_user_id' not in session:
        return redirect(url_for('login'))

    customer = Customer.query.filter_by(User_id=user_id).first()

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        identification_card = request.form.get('identification_card')
        customer_type_id = request.form.get('customer_type_id')
        gender = request.form.get('gender')

        # Update dữ liệu User
        current_user.username = username
        current_user.email = email
        current_user.phone = phone

        current_user.gender = gender

        if customer:  # này chưa lưu được vô CSDL hmmm
            customer.identification_card = identification_card
            customer.customer_type_id = customer_type_id
        try:
            # Update vô CSDL
            db.session.commit()
            flash("Thông tin tài khoản được cập nhật thành công!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Có lỗi xảy ra: {str(e)}", "danger")
        return redirect(url_for('account'))

    return render_template('edit_account.html', user=user, customer=customer)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cancel_form, trigger="interval", seconds=1)  # Chạy mỗi ngày
    scheduler.start()


if __name__ == '__main__':
    from app import admin
    # start_scheduler()
    app.run(debug=True)
