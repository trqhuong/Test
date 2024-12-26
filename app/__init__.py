from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary
app = Flask(__name__)

app.secret_key = 'HJLIYYWO(&^((^NCHDKVIS'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/hotel?charset=utf8mb4" % quote('123456')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 3

db = SQLAlchemy(app)
login_manager = LoginManager(app)


cloudinary.config(
    cloud_name="dndsrbf9s",
    api_key="932944391659178",
    api_secret="_UlDjHd_T5WxNV0iZMMN9tGJuy0",
    secure=True
)

VNPAY_CONFIG = {
    'vnp_TmnCode': 'RC52CA8T',
    'vnp_HashSecret': '0F67MDQPA2ANUFVUMVRBXV9X5Z5V9TB4',
    'vnp_Url': 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
    "vnp_ReturnUrl": "http://localhost:5000/vnpay_return"
}
