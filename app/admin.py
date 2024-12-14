from app import app,db
import utils
from flask import redirect,request
from flask_admin import Admin,BaseView,expose
from flask_admin.contrib.sqla import ModelView
from app.models import Room,RoomType,RoomRegulation,CustomerRegulation,User,Role
from flask_login import current_user, logout_user

admin=Admin(app=app,name='HotelManagementWeb',template_mode='bootstrap4')

class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.__eq__(Role.ADMIN)


class UserView(AuthenticatedView):
    column_list = ['role','username','email','phone','gender']
    column_searchable_list = ['username']
    column_filters = ['role']
    column_editable_list =['phone']


class RoomView(AuthenticatedView):
    column_list = ['id','name','image','room_type_id','status']
    column_searchable_list = ['name','status']
    column_filters = ['id','name']
    column_editable_list=['name','image']


class RoomTypeView(AuthenticatedView):
    column_list = ['id','name','price','room']
    column_filters = ['name']
    column_editable_list = ['name']
    can_export = True

class RoomRegulationView(AuthenticatedView):
    column_list = ['id', 'number_of_guests', 'room_type_id','rate']


class CustomerRegulationView(AuthenticatedView):
    column_list = ['id', 'Coefficient', 'customer_type_id']

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

class RevenueStatisticView( AuthenticatedBaseView):
    @expose('/')
    def index(self):
        kw = request.args.get('kw')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        month = request.args.get('month')
        year = request.args.get('year')

        r = utils.revenue_statistics(kw=kw,
                                       from_date=from_date,
                                       to_date=to_date,
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
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        month = request.args.get('month')
        year = request.args.get('year')

        room_report = utils.stats(from_date=from_date,
                                       to_date=to_date,
                                       month=month,
                                       year=year,
                                   kw=kw)

        return self.render('admin/room_stats.html',
                           stats=room_report)

admin.add_view(RoomView(Room,db.session))
admin.add_view(RoomTypeView(RoomType,db.session))
admin.add_view(RoomRegulationView(RoomRegulation,db.session))
admin.add_view(CustomerRegulationView(CustomerRegulation,db.session))
admin.add_view(UserView(User,db.session))
admin.add_view(RevenueStatisticView(name='Revenue statistics'))
admin.add_view(Room_stats(name='Frequency statistics'))
admin.add_view(LogoutView(name='Log out'))