from configparser import Interpolation
from datetime import datetime
import hashlib
from cloudinary.utils import unique
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, text
from sqlalchemy.orm import relationship
from enum import Enum as RoleEnum
from app import db, app
from flask_login import UserMixin


class Role(RoleEnum):
    ADMIN = 1,
    RECEPTIONIST = 2,
    CUSTOMER = 3


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)


class User(Base, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    phone = Column(String(10), nullable=False)
    avatar = Column(String(100),
                    default="https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg")
    gender = Column(String(6), nullable=False)
    role = Column(Enum(Role), default=Role.CUSTOMER)
    room = relationship('Room', backref='user', lazy=True)
    # room_regulation = relationship('RoomRegulation', backref='user', lazy=True)
    # customer_regulation = relationship('CustomerRegulation', backref='user', lazy=True)
    room_reservation_form = relationship('RoomReservationForm', backref='user', lazy=True)
    bill = relationship('Bill', backref='user', lazy=True)
    room_rental_from = relationship('RoomRentalForm', backref='user', lazy=True)


class CustomerType(Base):
    type = Column(String(10))
    # user = relationship('User', backref='customer_type', lazy=True)
    customer_regulation = relationship('CustomerRegulation', backref='customer_type', lazy=True)
    customer = relationship('Customer', backref='customer_type', lazy=True)
    guest = relationship('Guest', backref='customer_type', lazy=True)


class Customer(User):
    User_id = Column(Integer, ForeignKey(User.id), unique=True)
    cus_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    identification_card = Column(String(12), nullable=False, unique=True)
    customer_type_id = Column(Integer, ForeignKey(CustomerType.id), nullable=False, default=1)
    room_reservation_form = relationship('RoomReservationForm', backref='customer', lazy=True)
    room_rental_form = relationship('RoomRentalForm', backref='customer', lazy=True)
    comment = relationship('Comment', backref='customer', lazy=True, cascade='all, delete-orphan')

    user = relationship("User", backref="customer", lazy="joined")


class Guest(Base):
    name = Column(String(50), nullable=False)
    identification_card = Column(String(12), nullable=False, unique=True)
    customer_type_id = Column(Integer, ForeignKey(CustomerType.id), nullable=False, default=1)
    room_reservation_form = relationship('RoomReservationForm', secondary='reservation_detail', lazy='subquery',
                                         backref='guest')
    room_rental_form = relationship('RoomRentalForm', secondary='rental_detail', lazy='subquery',
                                    backref='guest')


class RoomType(Base):
    name = Column(String(50), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    room = relationship('Room', backref='room_type', lazy=True)
    room_regulation = relationship('RoomRegulation', backref='room_type', uselist=False)


class Room(Base):
    name = Column(String(50), nullable=False)
    image = Column(String(100))
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    room_type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    room_reservation_from = relationship('RoomReservationForm', backref='room', lazy=True)
    room_rental_from = relationship('RoomRentalForm', backref='room', lazy=True)
    comment = relationship('Comment', backref='room', lazy=True,cascade='all, delete-orphan')


class RoomRegulation(Base):
    number_of_guests = Column(Integer, nullable=False, default=3)
    # user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    room_type_id = Column(Integer, ForeignKey(RoomType.id), unique=True, nullable=False)
    rate = Column(Float, nullable=False, default=0.25)
    # room_type = relationship('RoomType', backref='room_regulation')


class CustomerRegulation(Base):
    Coefficient = Column(Float, nullable=False, default=1.5)
    # user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    customer_type_id = Column(Integer, ForeignKey(CustomerType.id), nullable=False, unique=True)


class RoomReservationForm(Base):
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    deposit = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=True)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    customer_id = Column(Integer, ForeignKey(Customer.cus_id), nullable=False)
    room_rental_form = relationship('RoomRentalForm', backref='room_reservation_form', uselist=False)


class RoomRentalForm(Base):
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    deposit = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    customer_id = Column(Integer, ForeignKey(Customer.cus_id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    # bill_id = Column(Integer, ForeignKey(Bill.id), nullable=False, unique=True)
    room_reservation_form_id = Column(Integer, ForeignKey(RoomReservationForm.id), unique=True, nullable=True)
    bill = relationship('Bill', backref='room_rental_form', lazy=True, uselist=False,cascade='all, delete-orphan')


class Bill(Base):
    total_price = Column(Float, nullable=False)
    created_date = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    room_rental_form_id = Column(Integer, ForeignKey(RoomRentalForm.id), nullable=False, unique=True)
    # room_rental_from = relationship('RoomRentalForm', backref='bill', lazy=True)


class Comment(Base):
    content = Column(String(1000), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    # user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    customer_id = Column(Integer, ForeignKey(Customer.cus_id), nullable=False)


reservation_detail = db.Table('reservation_detail',
                              Column('id', Integer, primary_key=True, nullable=False, autoincrement=True),
                              Column('guest_id', Integer, ForeignKey(Guest.id)),
                              Column('reservation_id', Integer, ForeignKey(RoomReservationForm.id)))
rental_detail = db.Table('rental_detail',
                         Column('id', Integer, primary_key=True, nullable=False, autoincrement=True),
                         Column('guest_id', Integer, ForeignKey(Guest.id)),
                         Column('rental_id', Integer, ForeignKey(RoomRentalForm.id)))


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        customer_type1 = CustomerType(type='Domestic')
        customer_type2 = CustomerType(type='Foreign')
        db.session.add_all([customer_type1, customer_type2])
        db.session.commit()
        customer_type = db.session.query(CustomerType).filter(CustomerType.type.__eq__('domestic')).first()
        user1 = User(name='Lê Hữu Hậu', username='lehuuhau',password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                     email='lehuuhau1231@gmail.com',phone='0378151028', gender=1, role=Role.ADMIN)
        user2 = User(name='Lâm', username='huuhau', password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                     email='lehuuhau@gmail.com', phone='0378151028', gender=1, role=Role.RECEPTIONIST)
        cus = Customer(name='Trần Quỳnh Hương', username='trqhuong',
                       password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                       email='quynhhuongtran314@gmail.com',
                       phone='0941166034', gender=2, identification_card='085388761234', customer_type_id=2)
        cus1 = Customer(name='Quỳnh Hương', username='huong',
                        password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                        email='quynhhuongtran@gmail.com', phone='0941166036', gender=2,
                        identification_card='085387417586', customer_type_id=1)

        cus2 = Customer(name='Lê Hữu Hậu', username='hau',
                        password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                        email='lehuuhau004@gmail.com', phone='0941166006', gender=2,
                        identification_card='085387417581', customer_type_id=1)

        db.session.add_all([user1, cus, user2, cus1, cus2])
        db.session.commit()

        #         ==============================Thêm loại phòng======================================

        room_type_single = RoomType(name='Single Bedroom', price=100)
        room_type_twin = RoomType(name='Twin Bedroom', price=300)
        room_type_double = RoomType(name='Double Bedroom', price=500)

        db.session.add_all([room_type_single, room_type_twin, room_type_double])
        db.session.commit()

        #         ==============================Thêm phòng======================================

        room1 = Room()
        admin = User.query.filter(User.role.__eq__(Role.ADMIN)).first()
        rooms = [
            {
                'name': 'Deluxe Room(River view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/singleViewRiver1_xldkkp.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_single.id,

            },
            {
                'name': 'Executive Room(City view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/doubleViewRiver_rtsum2.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_twin.id,

            },
            {
                'name': 'President Room(River view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/doubleViewRiver_rtsum2.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_double.id,

            },
            {
                'name': 'Deluxe Room(City view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/singleViewCity1_yrewg4.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_single.id,

            },
            {
                'name': 'Executive Room(River view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/twinViewRiver1_kn87ab.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_twin.id,

            },
            {
                'name': 'President Room(City view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/doubleViewCity1_wavkyb.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_double.id,

            },
            {
                'name': 'President Room(City view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/doubleViewCity1_wavkyb.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_double.id,

            },
            {
                'name': 'President Room(River view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/doubleViewCity1_wavkyb.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_double.id,

            },
            {
                'name': 'Executive Room(City view)',
                'image': 'https://res.cloudinary.com/dndsrbf9s/image/upload/v1732957297/doubleViewRiver_rtsum2.jpg',
                'user_id': admin.id,
                'room_type_id': room_type_twin.id,

            }
        ]

        for room in rooms:
            db.session.add(Room(**room))
        db.session.commit()

        #         ==============================Thêm quy định phòng======================================
        room_regulation_data = [{'room_type_id': room_type_single.id, },
                                {'room_type_id': room_type_twin.id,},
                                {'room_type_id': room_type_double.id, }]
        for regulation in room_regulation_data:
            db.session.add(RoomRegulation(**regulation))
        db.session.commit()

        #         ==============================Thêm quy định KH======================================
        cus_regulation = CustomerRegulation(customer_type_id=2)
        db.session.add(cus_regulation)
        db.session.commit()

        #         ==============================Thêm phiếu đặt======================================
        reservation_data = [
            {'customer_id': 2, 'user_id': 3, 'room_id': 4, 'check_in_date': datetime(2025, 1, 9, 17, 1),
             'check_out_date': datetime(2025, 1, 19, 17, 1), 'deposit': 900000, 'total_amount': 1000000},
            {'customer_id': 1, 'user_id': None, 'room_id': 2, 'check_in_date': datetime(2024, 12, 27, 17, 11),
             'check_out_date': datetime(2024, 12, 29, 17, 11), 'deposit': 1500000, 'total_amount': 1000000},
            {'customer_id': 2, 'user_id': 3, 'room_id': 2, 'check_in_date': datetime(2024, 12, 22, 17, 12),
             'check_out_date': datetime(2024, 12, 26, 17, 12), 'deposit': 1500000, 'total_amount': 1000000},
            {'customer_id': 1, 'user_id': 3, 'room_id': 1, 'check_in_date': datetime(2025, 1, 10, 17, 1),
             'check_out_date': datetime(2025, 2, 9, 17, 1), 'deposit': 1200000, 'total_amount': 1000000}
        ]

        for data in reservation_data:
            reservation = RoomReservationForm(**data)
            db.session.add(reservation)
        db.session.commit()
        #         ==============================Thêm Guest======================================

        u1 = Guest(name='A', identification_card='789456123258', customer_type_id=1)
        u2 = Guest(name='B', identification_card='456789123369', customer_type_id=2)
        u3 = Guest(name='C', identification_card='789456159357', customer_type_id=1)

        db.session.add_all([u1, u2, u3])
        db.session.commit()

        #         ==============================Thêm ReservationDetail======================================
        reservation_1 = db.session.query(RoomReservationForm).filter_by(customer_id=cus.cus_id).first()
        reservation_2 = db.session.query(RoomReservationForm).filter_by(customer_id=cus1.cus_id).first()

        guest_1 = db.session.query(Guest).filter_by(id=u1.id).first()
        guest_2 = db.session.query(Guest).filter_by(id=u2.id).first()

        guest_1.room_reservation_form.append(reservation_1)
        guest_2.room_reservation_form.append(reservation_1)
        guest_2.room_reservation_form.append(reservation_2)

        db.session.add(guest_2, guest_1)
        db.session.commit()
        #         ==============================Thêm phiếu thuê======================================

        rental_data = [
            {'customer_id': 2, 'user_id': 3, 'room_id': 4, 'check_in_date': datetime(2025, 1, 9, 17, 1),
             'check_out_date': datetime(2025, 1, 19, 17, 1), 'deposit': 900000, 'room_reservation_form_id': 1},
            {'customer_id': 1, 'user_id': 3, 'room_id': 2, 'check_in_date': datetime(2024, 12, 25, 17, 11),
             'check_out_date': datetime(2024, 12, 29, 17, 11), 'deposit': 1500000},
            {'customer_id': 2, 'user_id': 3, 'room_id': 2, 'check_in_date': datetime(2024, 12, 22, 17, 12),
             'check_out_date': datetime(2024, 12, 26, 17, 12), 'deposit': 1500000, 'room_reservation_form_id': 3},
            {'customer_id': 1, 'user_id': 3, 'room_id': 1, 'check_in_date': datetime(2025, 1, 10, 17, 1),
             'check_out_date': datetime(2025, 2, 9, 17, 1), 'deposit': 1200000}]
        for r in rental_data:
            rental = RoomRentalForm(**r)
            db.session.add(rental)
        db.session.commit()
        #         ==============================Thêm RentalDetail======================================

        rental_1 = db.session.query(RoomRentalForm).filter_by(customer_id=cus.cus_id).first()
        rental_2 = db.session.query(RoomRentalForm).filter_by(customer_id=cus1.cus_id).first()

        guest_3 = db.session.query(Guest).filter_by(id=u1.id).first()
        guest_4 = db.session.query(Guest).filter_by(id=u2.id).first()

        guest_3.room_rental_form.append(rental_1)
        guest_3.room_rental_form.append(rental_2)
        guest_4.room_rental_form.append(rental_2)

        db.session.add(guest_3, guest_4)
        db.session.commit()

        #         ==============================Thêm hóa đơn======================================
        bill_data = [{'user_id': 3, 'room_rental_form_id': 1, 'total_price': 2000000,
                      'created_date': datetime(2025, 1, 19, 17, 1)},
                     {'user_id': 3, 'room_rental_form_id': 2, 'total_price': 5000000,
                      'created_date': datetime(2024, 12, 29, 17, 11)},
                     {'user_id': 3, 'room_rental_form_id': 3, 'total_price': 4000000,
                      'created_date': datetime(2024, 12, 26, 17, 11)},
                     {'user_id': 3, 'room_rental_form_id': 4, 'total_price': 1000000,
                      'created_date': datetime(2025, 2, 9, 17, 11)}]
        for b in bill_data:
            bill = Bill(**b)
            db.session.add(bill)
        db.session.commit()
        #         ==============================Thêm cmt======================================
        comment_data = [{'customer_id': 1, 'content': 'Phòng này quá ok <3', 'room_id': 1,
                         'created_date': datetime(2025, 1, 20, 17, 1)},
                        {'customer_id': 2, 'content': 'Cũng tàm tạm, cần nâng cấp dịch vụ phòng!', 'room_id': 2,
                         'created_date': datetime(2025, 1, 2, 17, 1)},
                        {'customer_id': 2, 'content': 'Sẽ ghé thăm vào lần sau nếu có dịp', 'room_id': 2,
                         'created_date': datetime(2025, 1, 9, 17, 1)},
                        {'customer_id': 1, 'content': 'Một căn phòng đáng trải nghiệm nhất tại khách sạn, 5 sao nhé',
                         'room_id': 4,
                         'created_date': datetime(2025, 2, 9, 17, 1)}]
        for c in comment_data:
            cmt = Comment(**c)
            db.session.add(cmt)
        db.session.commit()







