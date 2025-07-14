# views.py
from flask import render_template, redirect, url_for, flash, request, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Order, Feedback
from forms import LoginForm, ChangePasswordForm, CreateUserForm
from datetime import datetime
import io
import pandas as pd


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "order":
            name = request.form.get("order_name")
            phone = request.form.get("order_phone")
            address = request.form.get("order_address")
            content = request.form.get("order_content")
            order = Order(name=name, phone=phone, address=address, content=content)
            db.session.add(order)
            db.session.commit()
            flash("Đặt hàng thành công!")

        elif form_type == "feedback":
            name = request.form.get("feedback_name")
            rating = request.form.get("feedback_rating")
            message = request.form.get("feedback_message")
            feedback = Feedback(name=name, rating=rating, message=message)
            db.session.add(feedback)
            db.session.commit()
            flash("Cảm ơn bạn đã góp ý!")

        return redirect(url_for("home"))

    menu_items = []  # Load menu từ DB nếu có
    order_count = Order.query.count()
    feedback_count = Feedback.query.count()
    return render_template("home.html", menu_items=menu_items, order_count=order_count, feedback_count=feedback_count)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Đăng nhập thành công!")
            return redirect(url_for("admin"))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")
    return render_template("auth/login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("login"))


@app.route("/admin")
@login_required
def admin():
    if current_user.role != 'admin':
        flash("Bạn không có quyền truy cập trang này!", "danger")
        return redirect(url_for("home"))

    from models import MenuItem
    menu_items = MenuItem.query.all()
    total_orders = Order.query.count()
    total_feedbacks = Feedback.query.count()
    return render_template("admin.html", menu_items=menu_items, total_orders=total_orders, total_feedbacks=total_feedbacks)


@app.route("/reports")
@login_required
def reports():
    if current_user.role != 'admin':
        flash("Bạn không có quyền truy cập.", "danger")
        return redirect(url_for("home"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template("reports.html", orders=orders, feedbacks=feedbacks)


@app.route("/export/orders")
@login_required
def export_orders():
    if current_user.role != 'admin':
        return redirect(url_for("home"))

    orders = Order.query.all()
    df = pd.DataFrame([{
        "Họ tên": o.name,
        "Điện thoại": o.phone,
        "Địa chỉ": o.address,
        "Nội dung": o.content,
        "Thời gian": o.created_at.strftime("%d/%m/%Y %H:%M")
    } for o in orders])

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Orders')
    writer.close()
    output.seek(0)

    return send_file(output, download_name="orders.xlsx", as_attachment=True)


@app.route("/export/feedbacks")
@login_required
def export_feedbacks():
    if current_user.role != 'admin':
        return redirect(url_for("home"))

    feedbacks = Feedback.query.all()
    df = pd.DataFrame([{
        "Tên": f.name,
        "Đánh giá": f.rating,
        "Góp ý": f.message,
        "Thời gian": f.created_at.strftime("%d/%m/%Y %H:%M")
    } for f in feedbacks])

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Feedbacks')
    writer.close()
    output.seek(0)

    return send_file(output, download_name="feedbacks.xlsx", as_attachment=True)

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import MenuItem
from forms import MenuItemForm

menu_bp = Blueprint('menu', __name__)

UPLOAD_FOLDER = 'static/uploads'  # Thư mục chứa ảnh upload

# ➕ Thêm món
@menu_bp.route('/admin/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập.', 'danger')
        return redirect(url_for('home'))

    form = MenuItemForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            image_file = form.image.data
            filename = os.path.join(UPLOAD_FOLDER, secure_filename(image_file.filename))
            image_file.save(filename)

        item = MenuItem(
            name=form.name.data,
            price=form.price.data,
            image=filename
        )
        db.session.add(item)
        db.session.commit()
        flash('✅ Thêm món thành công!', 'success')
        return redirect(url_for('admin_page'))  # trang quản lý

    return render_template('admin_item_form.html', form=form, action='add')

# ✏️ Sửa món
@menu_bp.route('/admin/items/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập.', 'danger')
        return redirect(url_for('home'))

    item = MenuItem.query.get_or_404(item_id)
    form = MenuItemForm(obj=item)

    if form.validate_on_submit():
        if form.image.data:
            image_file = form.image.data
            filename = os.path.join(UPLOAD_FOLDER, secure_filename(image_file.filename))
            image_file.save(filename)
            item.image = filename

        item.name = form.name.data
        item.price = form.price.data
        db.session.commit()
        flash('✅ Cập nhật thành công!', 'success')
        return redirect(url_for('admin_page'))

    return render_template('admin_item_form.html', form=form, item=item, action='edit')

# 🗑️ Xoá món
@menu_bp.route('/admin/items/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền xoá.', 'danger')
        return redirect(url_for('home'))

    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('🗑️ Đã xoá món!', 'info')
    return redirect(url_for('admin_page'))
