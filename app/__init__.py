from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)


app.secret_key = 'HJLIYYWO(&^((^NCHDKVIS'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/hoteldb?charset=utf8mb4" % quote('123456')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 3

db = SQLAlchemy(app)
login_manager = LoginManager(app)


cloudinary.config(
    cloud_name = "dndsrbf9s",
    api_key = "932944391659178",
    api_secret = "_UlDjHd_T5WxNV0iZMMN9tGJuy0",
    secure=True
)
