import hashlib
from app.models import User, Room, RoomType, Customer, CustomerType, Guest, RoomReservationForm, RoomRentalForm,Role
from app import db, app
import cloudinary.uploader
from sqlalchemy import or_, desc
import hmac
from urllib.parse import urlencode
import urllib.parse



def check_room_availability(checkin, checkout, room_id):
    room_reservation = RoomReservationForm.query.filter(RoomReservationForm.room_id == room_id).all()
    room_rental = RoomRentalForm.query.filter(RoomRentalForm.room_id == room_id).all()
    is_available = True

    for room in room_reservation:
        if not ((checkin > room.check_out_date) or (checkout < room.check_in_date)):
            is_available = False
            break

    if is_available:
        for room in room_rental:
            if not ((checkin > room.check_out_date) or (checkout < room.check_in_date)):
                is_available = False
                break

    return is_available


def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    u = User.query.filter(User.username.__eq__(username),
                          User.password.__eq__(password))
    if role:
        u = u.filter(User.role.__eq__(role))

    return u.first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_customer_by_account(table, account):
    account = account.strip()
    return table.query.filter(or_(table.username == account, table.email == account)).first()


def add_customer(name, username, password, email, phone, avatar, gender, identification, type):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    if type.__eq__('Domestic'):
        type = 1
    else:
        type = 2
    user = Customer(name=name, username=username, password=password, email=email, phone=phone, gender=gender
                    , identification_card=identification, customer_type_id=type)
    if avatar:
        upload_result = cloudinary.uploader.upload(avatar)
        user.avatar = upload_result.get('secure_url')
    db.session.add(user)
    db.session.commit()


def existence_check(table, attribute, value):
    return table.query.filter(getattr(table, attribute).__eq__(value)).first()


def change_password(user_id, new_password):
    new_password = str(hashlib.md5(new_password.strip().encode('utf-8')).hexdigest())
    user = get_user_by_id(user_id)
    if user:
        user.password = new_password
        db.session.commit()


def load_room(checkin=None, checkout=None, page=None, room_type=None, room_id=None):
    rooms = Room.query

    if room_type:
        rooms = rooms.join(RoomType).filter(RoomType.name == room_type)

    new_room = []
    if checkin and checkout:
        if checkin <= checkout:
            for room in rooms:
                if check_room_availability(checkin, checkout, room.id):
                    new_room.append(room)

            # Thêm logic phân trang cho new_room
            if page:
                page_size = app.config["PAGE_SIZE"]
                start = (page - 1) * page_size
                end = start + page_size
                return new_room[start:end], len(new_room)
            return new_room, len(new_room)

    if room_id:
        return rooms.filter(Room.id == room_id).first()

    length = rooms.count()
    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        rooms = rooms.slice(start, start + page_size)

    return rooms.all(), length


def count_room():
    return Room.query.count()


def get_customer_type(type=None):
    if type:
        return CustomerType.query.filter(CustomerType.type == type).first()
    return CustomerType.query.all()


def add_guest(data):
    if data['customer_type'].__eq__('Domestic'):
        type = 1
    else:
        type = 2
    guest = Guest(name=data['name'], identification_card=data['identification_card'], customer_type_id=type)
    db.session.add(guest)


def add_room_reservation_form(data, customer_id, user_id=None):
    if user_id:
        room_reservation_form = RoomReservationForm(check_in_date=data['check_in_date'],
                                                    check_out_date=data['check_out_date'],
                                                    deposit=data['deposit'], total_amount=data['total_amount'],
                                                    room_id=data['room_id'], customer_id=customer_id, user_id=user_id)
    else:
        room_reservation_form = RoomReservationForm(check_in_date=data['check_in_date'],
                                                    check_out_date=data['check_out_date'],
                                                    deposit=data['deposit'], total_amount=data['total_amount'],
                                                    room_id=data['room_id'], customer_id=customer_id)
    db.session.add(room_reservation_form)


def get_room_reservation_form():
    return RoomReservationForm.query.order_by(desc(RoomReservationForm.id)).first()


class vnpay:
    requestData = {}
    responseData = {}

    def get_payment_url(self, vnpay_payment_url, secret_key):
        # Dữ liệu thanh toán được sắp xếp dưới dạng danh sách các cặp khóa-giá trị theo thứ tự tăng dần của khóa.
        inputData = sorted(self.requestData.items())
        # Duyệt qua danh sách đã sắp xếp và tạo chuỗi query sử dụng urllib.parse.quote_plus để mã hóa giá trị
        queryString = ''
        hasData = ''
        seq = 0
        for key, val in inputData:
            if seq == 1:
                queryString = queryString + "&" + key + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                queryString = key + '=' + urllib.parse.quote_plus(str(val))

        # Sử dụng phương thức __hmacsha512 để tạo mã hash từ chuỗi query và khóa bí mật
        hashValue = self.__hmacsha512(secret_key, queryString)
        return vnpay_payment_url + "?" + queryString + '&vnp_SecureHash=' + hashValue

    def validate_response(self, secret_key):
        # Lấy giá trị của vnp_SecureHash từ self.responseData.
        vnp_SecureHash = self.responseData['vnp_SecureHash']
        # Loại bỏ các tham số liên quan đến mã hash
        if 'vnp_SecureHash' in self.responseData.keys():
            self.responseData.pop('vnp_SecureHash')

        if 'vnp_SecureHashType' in self.responseData.keys():
            self.responseData.pop('vnp_SecureHashType')
        # Sắp xếp dữ liệu (inputData)
        inputData = sorted(self.responseData.items())

        hasData = ''
        seq = 0
        for key, val in inputData:
            if str(key).startswith('vnp_'):
                if seq == 1:
                    hasData = hasData + "&" + str(key) + '=' + urllib.parse.quote_plus(str(val))
                else:
                    seq = 1
                    hasData = str(key) + '=' + urllib.parse.quote_plus(str(val))
        # Tạo mã hash
        hashValue = self.__hmacsha512(secret_key, hasData)

        print(
            'Validate debug, HashData:' + hasData + "\n HashValue:" + hashValue + "\nInputHash:" + vnp_SecureHash)

        return vnp_SecureHash == hashValue

    # tạo mã hash dựa trên thuật toán HMAC-SHA-512
    @staticmethod
    def __hmacsha512(key, data):
        byteKey = key.encode('utf-8')
        byteData = data.encode('utf-8')
        return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()

