from app.models import Room, RoomType, RoomRegulation, Customer, CustomerType, CustomerRegulation
from app import dao, db
from sqlalchemy import func, Numeric, extract
from app.models import *


def total_price(price, day, length, list_customer_type, room_id):
    total = price * day
    if length > 2:  # Nếu tồn tại 3 khách
        room_regulation = db.session.query(Room.id, RoomRegulation.rate). \
            join(RoomType, Room.room_type_id == RoomType.id). \
            join(RoomRegulation, RoomType.id == RoomRegulation.room_type_id). \
            filter(Room.id == room_id).first()

        total = total + (total * room_regulation.rate)

    customer = db.session.query(Customer.id, CustomerType.type, CustomerRegulation.Coefficient). \
        join(CustomerType, Customer.customer_type_id == CustomerType.id). \
        join(CustomerRegulation, CustomerType.id == CustomerRegulation.customer_type_id). \
        filter(CustomerType.type == 'Foreign').first()

    for item in list_customer_type:
        if item == customer.type:
            total = total * customer.Coefficient
            return total
    return total


def revenue_statistics(kw=None, year=None, month=None):
    with app.app_context():
        #Tính tổng số bill và lọc
        if not kw and not year and not month :
            count_bill=Bill.query.count()
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


        return revenue.all()

def stats(kw=None, year=None, month=None):
    with app.app_context():
        # Tính tổng số ngày thuê phòng
        total_days = db.session.query(
            func.coalesce(func.sum(
                func.datediff(RoomRentalForm.check_out_date, RoomRentalForm.check_in_date)
            ), 0)
        ).join(Bill, Bill.room_rental_form_id.__eq__(RoomRentalForm.id), isouter=True)

        if month:
            total_days = total_days.filter(
                extract('month', Bill.created_date) == month)
        if year:
            total_days = total_days.filter(
                extract('year', Bill.created_date) == year)

        # Lấy tổng số ngày thuê
        total_days_result = total_days.first() #Lấy kết quả đầu tiên của truy vấn.
        total = total_days_result[0] if total_days_result else 0 # Truy cập giá trị tổng số ngày thuê (do truy vấn trả về một tuple
                                                                 # Nếu không có kết quả, đặt total=0

        # print(f"Tổng số ngày thuê phòng: {total} ngày")

        # Truy vấn thống kê chi tiết từng phòng
        stats_query = db.session.query(
            Room.name,
            func.coalesce(func.sum(
                func.datediff(RoomRentalForm.check_out_date, RoomRentalForm.check_in_date)
            ), 0),
            func.round((
                    func.coalesce(func.sum(
                        func.datediff(RoomRentalForm.check_out_date, RoomRentalForm.check_in_date)
                    ), 0) / total * 100
            ), 2) #func.round hiện 2 số sau dấu phẩy
        ).join(RoomRentalForm, RoomRentalForm.room_id == Room.id, isouter=True)\
        .join(Bill, Bill.room_rental_form_id.__eq__(RoomRentalForm.id), isouter=True)\
        .group_by(Room.name)

        # Bộ lọc theo điều kiện
        if month:
            stats_query = stats_query.filter(
                extract('month', Bill.created_date) == month)
        if year:
            stats_query = stats_query.filter(
                extract('year', Bill.created_date) == year)
        if kw:
            stats_query = stats_query.filter(
                RoomType.name.contains(kw))

        # Trả về kết quả
        return stats_query.all()


def count_room_by_roomType():
    with app.app_context():
        return db.session.query(RoomType.id, RoomType.name, func.count(Room.id)) \
            .join(Room, Room.room_type_id.__eq__(RoomType.id),isouter=True).group_by(RoomType.id).all()

print(stats())