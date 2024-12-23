from app import app, db
import utils
from flask import redirect, request, render_template
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from app.models import Room, RoomType, RoomRegulation, CustomerRegulation, User, Role
from flask_login import current_user, logout_user


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html', stats_room=utils.count_room_by_roomType())


admin = Admin(app=app, name='HotelManagementWeb', template_mode='bootstrap4', index_view=MyAdminIndexView())


class AuthenticatedView(ModelView):
    def is_accessible(self):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            logout_user()
            return False  # chặn quyền truy cập vào các mục
        return True
        # return current_user.is_authenticated and current_user.role.__eq__(Role.ADMIN)


class UserView(AuthenticatedView):
    column_list = ['role', 'username', 'email', 'phone', 'gender']
    column_searchable_list = ['username']
    column_filters = ['role']
    column_editable_list = ['phone']
    can_export = True



class RoomView(AuthenticatedView):
    column_list = ['id', 'name', 'image', 'room_type_id']
    column_searchable_list = ['name']
    column_filters = ['id', 'name']
    column_editable_list = ['name', 'image']
    can_export = True


class RoomTypeView(AuthenticatedView):
    column_list = ['id', 'name', 'price', 'room']
    column_filters = ['name']
    column_editable_list = ['name']
    can_export = True


class RoomRegulationView(AuthenticatedView):
    column_list = ['id', 'number_of_guests', 'room_type_id', 'rate']
    column_editable_list = ['number_of_guests','rate']
    can_export = True


class CustomerRegulationView(AuthenticatedView):
    column_list = ['id', 'Coefficient', 'customer_type_id']
    column_editable_list =['Coefficient']
    can_export = True


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
