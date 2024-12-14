
from sqlalchemy import func, Numeric, extract
from app.models import *


def revenue_statistics(kw=None, year=None, month=None, from_date=None, to_date=None):
    with app.app_context():
        #Tính tổng số bill và lọc
        if not kw and not year and not month and not from_date and not to_date:
            count_bill=Bill.query.count()
        elif from_date:#lọc theo ngày bắt đầu
            count_bill=Bill.query.filter(
                Bill.created_date.__ge__(from_date)).count()#__ge__: >=
        elif to_date:#lọc theo ngày kết thúc
            count_bill = Bill.query.filter(
                Bill.created_date.__le__(to_date)).count()#__le__:<=
        elif kw:#lọc theo từ khóa
            count_bill=Bill.query.count()
        elif month:
            count_bill=Bill.query.filter(
                extract('month',Bill.created_date)==month)
            if year:
                count_bill=count_bill.filter(extract('year', Bill.created_date) == year)
            count_bill=count_bill.count()
        else:
            count_bill=Bill.query.filter(extract('year',Bill.created_date)==year).count()

        revenue = db.session.query(
            RoomType.name,
            func.coalesce(func.sum(Bill.total_price), 0),  # tổng doanh thu hóa đơn cho từng loại phòng ko có trả về 0
            func.coalesce(func.count(Bill.id), 0),  # Đếm số lượng hóa đơn cho từng loại phòng
            # Tính tỷ lệ (tổng bill của loại phòng/tổng bill)*100
            func.cast((func.count(Bill.id) / count_bill) * 100, Numeric(5, 2))) \
            .join(Room, Room.room_type_id.__eq__(RoomType.id), isouter=True) \
            .join(RoomRentalForm, RoomRentalForm.room_id.__eq__(Room.id), isouter=True) \
            .join(Bill, Bill.room_rental_form_id.__eq__(RoomRentalForm.id), isouter=True) \
            .group_by(RoomType.name) \
            .order_by(RoomType.id)

        #lọc doanh thu
        if month:
            revenue = revenue.filter(
                extract('month', Bill.created_date) == month)

        if year:
            revenue  = revenue .filter(
                extract('year',Bill.created_date) == year)

        if kw:
            revenue  = revenue .filter(
                RoomType.name.contains(kw))

        if from_date:
            revenue  = revenue .filter(
                Bill.created_date.__ge__(from_date))

        if to_date:
            revenue  = revenue .filter(
                Bill.created_date.__le__(to_date))

        return revenue.all()


def stats( kw=None,year=None, month=None, from_date=None, to_date=None):
    with (app.app_context()):
        total_days=db.session.query(func.coalesce(func.sum(
                   extract('day', RoomRentalForm.check_out_date) - extract('day', RoomRentalForm.check_in_date)))
        ).join(Bill, Bill.room_rental_form_id.__eq__(RoomRentalForm.id), isouter=True)



        if not kw and not year and not month and not from_date and not to_date :
            count_days = total_days.count()
        elif from_date:
            count_days = total_days.query.filter(
                Bill.created_date.__ge__(from_date)).count()  # __ge__: >=
        elif to_date:
            count_days = total_days.query.filter(
                Bill.created_date.__ge__(to_date)).count()  # __le__:<=
        elif kw:
            count_days = total_days.count()
        elif month:
            count_days = total_days.filter(
                extract('month', Bill.created_date) == month)
            if year:
                count_days = count_days.filter(
                    extract('year', Bill.created_date) == year)
            count_days = total_days.count()
        else:
            count_days = total_days.query.filter(extract('year', Bill.created_date) == year).count()

        stats = db.session.query(
            Room.name,
            func.coalesce(func.sum(
                extract('day', RoomRentalForm.check_out_date) - extract('day', RoomRentalForm.check_in_date))),
            func.cast(
                func.sum(
                    ((extract('day', RoomRentalForm.check_out_date) - extract('day',
                                                                              RoomRentalForm.check_in_date)) / count_days) * 100
                ),Numeric(5, 2)
            )
        ).join(RoomRentalForm, RoomRentalForm.room_id == Room.id, isouter=True)\
        .join(Bill, Bill.room_rental_form_id.__eq__(RoomRentalForm.id), isouter=True)\
        .group_by(Room.name)


        if month:
            stats = stats.filter(
                extract('month', Bill.created_date) == month)

        if year:
            stats = stats.filter(
                extract('year', Bill.created_date) == year)

        if kw:
            stats = stats.filter(
                RoomType.name.contains(kw))

        if from_date:
            stats = stats.filter.filter(
                Bill.created_date.__ge__(from_date))

        if to_date:
            stats = stats.filter.filter(
                Bill.created_date.__le__(to_date))

        return stats.all()




