from app import app, db, dao
import utils
from flask import redirect, request
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from app.models import Room, RoomType, RoomRegulation, CustomerRegulation, User, Role,RoomRentalForm,Bill,RoomReservationForm
from flask_login import current_user, logout_user
import hashlib
from sqlalchemy.sql import exists, and_


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html', stats_room=utils.count_room_by_roomType())


admin = Admin(app=app, name='HotelManagementWeb', template_mode='bootstrap4', index_view=MyAdminIndexView())


class AuthenticatedView(ModelView):
    def is_accessible(self):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            logout_user()
            return False
        return True


class UserView(AuthenticatedView):
    column_list = ['role', 'username', 'email', 'phone', 'gender']
    column_searchable_list = ['username']
    column_filters = ['role']
    column_editable_list = ['phone']
    form_excluded_columns = [
        'room',
        'room_regulation',
        'customer_regulation',
        'room_reservation_form',
        'bill',
        'room_rental_from',
        'customer'
    ]

    def on_model_change(self, form, model, is_created):
        if not form.password.data:
            raise ValueError("Mật khẩu không được để trống")
        else:
            model.password = hashlib.md5(form.password.data.encode('utf-8')).hexdigest()
        super(UserView, self).on_model_change(form, model, is_created)


class RoomView(AuthenticatedView):
    column_list = ['id', 'name', 'image', 'room_type_id','Room_status','Room_price']
    column_searchable_list = ['name']
    column_filters = ['id', 'name']
    column_editable_list = ['name', 'image']
    form_excluded_columns = [
        'room_reservation_from',
        'room_rental_from',
        'comment',
        'user' #lỗi bắt buộc nhập
    ]
    can_export = True
    def get_room_status(self, room):
        session = self.session
        # Kiểm tra trạng thái phiếu Thuê
        in_use = session.query(exists().where(
            and_(RoomRentalForm.room_id == room.id, RoomRentalForm.status == 'IN_USE')
        )).scalar()
        # Kiểm tra trạng thái phiếu đặt
        confirmed = session.query(exists().where(
            and_(RoomReservationForm.room_id == room.id, RoomReservationForm.status == 'CONFIRMED')
        )).scalar()
        # Xác định trạng thái
        if in_use or confirmed:
            return "Rented"
        else:
            return "Available"

    def trang_thai_phong_formatter(view, context, model, name):
        return view.get_room_status(model)

    # Định nghĩa formatter cho cột room_price
    column_formatters = {
        'Room_status': trang_thai_phong_formatter,
        'Room_price': lambda view, context, model, name: (
            f"{model.room_type.price:,.0f} VND" if model.room_type else 'N/A'
        )
    }



class RoomTypeView(AuthenticatedView):
    column_list = ['id', 'name', 'price', 'room']
    column_labels = {
        'id': 'ID',
        'name': 'Name',
        'price': 'Price',
        'room': 'RoomDisplay'  # Đặt nhãn cho cột mới
    }
    column_filters = ['name']
    column_editable_list = ['name']
    can_export = True
    form_excluded_columns = [
        'room',
        'room_regulation'
    ]
    def _format_rooms(view, context, model, name):
        return ', '.join([room.name for room in model.room])
    column_formatters = {
        'room': _format_rooms,
        'price': lambda v, c, m, p: f"{m.price:,.0f} VND"
    }


class RoomRegulationView(AuthenticatedView):
    column_list = ['id', 'number_of_guests', 'room_type_id', 'rate']
    column_editable_list = ['rate','number_of_guests']
    form_excluded_columns = [
        'user' #lỗi bắt buộc nhập
    ]


class CustomerRegulationView(AuthenticatedView):
    column_list = ['id', 'Coefficient', 'customer_type_id']
    form_excluded_columns = [
        'user' #lỗi bắt buộc nhập
    ]


class AuthenticatedBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class LogoutView(AuthenticatedBaseView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect('/admin')


# class StatsView(AuthenticatedBaseView):
#     @expose("/")
#     def index(self):
#         return self.render('admin/revenue_stats.html')

class RevenueStatisticView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        kw = request.args.get('kw')
        month = request.args.get('month')
        year = request.args.get('year')

        r = utils.revenue_statistics(kw=kw,
                                     month=month,
                                     year=year)
        total_revenue = 0
        for m in r:
            total_revenue = total_revenue + m[1]

        if not month:
            month = '(1-12)'
        if not year:
            year = '(All)'

        return self.render('admin/revenue_stats.html',
                           revenue_statistics=r,
                           total_revenue=total_revenue,
                           year=year,
                           month=month)


class Room_stats(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        # name = request.args.get('name')
        kw = request.args.get('kw')
        month = request.args.get('month')
        year = request.args.get('year')

        room_report = utils.stats(
            month=month,
            year=year,
            kw=kw)

        return self.render('admin/room_stats.html',
                           stats=room_report)


admin.add_view(RoomView(Room, db.session))
admin.add_view(RoomTypeView(RoomType, db.session))
admin.add_view(RoomRegulationView(RoomRegulation, db.session))
admin.add_view(CustomerRegulationView(CustomerRegulation, db.session))
admin.add_view(UserView(User, db.session))
admin.add_view(RevenueStatisticView(name='Revenue statistics'))
admin.add_view(Room_stats(name='Frequency statistics'))
admin.add_view(LogoutView(name='Log out'))
