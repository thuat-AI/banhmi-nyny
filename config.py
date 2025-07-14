import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'một_chuỗi_mật_khẩu_mạnh_rất_dài'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cấu hình SMTP gửi mail (ví dụ Gmail SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')  # đặt biến môi trường
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')  # đặt biến môi trường
