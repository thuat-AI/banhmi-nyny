from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField,
    SelectField
)
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, ValidationError
)
from models import User

# 🔐 Đăng nhập
class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')


# 🔑 Đổi mật khẩu
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Mật khẩu cũ', validators=[DataRequired()])
    new_password = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', validators=[
        DataRequired(), EqualTo('new_password', message='Mật khẩu không khớp')
    ])
    submit = SubmitField('Đổi mật khẩu')


# 🔄 Gửi yêu cầu đặt lại mật khẩu
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Gửi yêu cầu')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Không tìm thấy email trong hệ thống.')


# 🔄 Form đặt lại mật khẩu mới
class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', validators=[
        DataRequired(), EqualTo('new_password', message='Mật khẩu không khớp')
    ])
    submit = SubmitField('Đặt lại mật khẩu')


# 👤 Tạo người dùng mới (dùng trong admin thêm người dùng)
class CreateUserForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(), EqualTo('password', message='Mật khẩu không khớp')
    ])
    role = SelectField('Vai trò', choices=[('user', 'Người dùng'), ('admin', 'Quản trị')], validators=[DataRequired()])
    submit = SubmitField('Tạo người dùng')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Tên đăng nhập đã tồn tại.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email đã được sử dụng.')

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, FileField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileAllowed

class MenuItemForm(FlaskForm):
    name = StringField('Tên món', validators=[DataRequired()])
    price = FloatField('Giá', validators=[DataRequired(), NumberRange(min=1000)])
    image = FileField('Ảnh món', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Chỉ nhận ảnh!')])
    submit = SubmitField('Lưu')
