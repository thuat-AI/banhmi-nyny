# menu_routes.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import MenuItem
from forms import MenuItemForm

menu_bp = Blueprint('menu', __name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        return redirect(url_for('admin_page'))

    return render_template('admin_item_form.html', form=form, action='add')

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
