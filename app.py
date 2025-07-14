from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo
import sqlite3
import os
import shutil
import pandas as pd
from datetime import datetime
import time


# === CẤU HÌNH ỨNG DỤNG ===
app = Flask(__name__)
app.secret_key = "nyny_secret_key_please_change_this_to_a_strong_key"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = "menu.db"

# === SETUP FLASK-LOGIN ===
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id_, username, password_hash, role):
        self.id = id_
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user_row:
        return User(user_row["id"], user_row["username"], user_row["password_hash"], user_row["role"])
    return None

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Mật khẩu cũ', validators=[DataRequired()])
    new_password = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Đổi mật khẩu')

class AddUserForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3)])
    password = PasswordField("Mật khẩu (mặc định 123456 nếu bỏ trống)", validators=[Length(min=0)])
    role = SelectField("Quyền", choices=[("user", "user"), ("admin", "admin")], validators=[DataRequired()])
    submit = SubmitField("Thêm")

def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )
    ''')
    if not conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone():
        password_hash = generate_password_hash("123")
        conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', password_hash, 'admin'))
    conn.commit()
    conn.close()

init_db()

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_panel"))

    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        user_row = conn.execute("SELECT * FROM users WHERE username = ?", (form.username.data,)).fetchone()
        conn.close()

        if user_row and check_password_hash(user_row["password_hash"], form.password.data):
            user = User(user_row["id"], user_row["username"], user_row["password_hash"], user_row["role"])
            login_user(user, remember=form.remember.data)
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("admin_panel"))
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        flash("Bạn không có quyền truy cập trang này.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    menu_items = conn.execute("SELECT * FROM menu").fetchall()
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_feedbacks = conn.execute("SELECT COUNT(*) FROM feedbacks").fetchone()[0]
    conn.close()
    return render_template("admin.html", menu_items=menu_items, total_orders=total_orders, total_feedbacks=total_feedbacks)

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Mật khẩu cũ không đúng.", "danger")
            return redirect(url_for("change_password"))

        conn = get_db_connection()
        new_hash = generate_password_hash(form.new_password.data)
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, current_user.id))
        conn.commit()
        conn.close()
        flash("Đổi mật khẩu thành công!", "success")
        return redirect(url_for("admin_panel"))
    return render_template("change_password.html", form=form)

@app.route("/", methods=["GET", "POST"])
def home():
    conn = get_db_connection()
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "order":
            name = request.form.get("order_name")
            phone = request.form.get("order_phone")
            address = request.form.get("order_address")
            content = request.form.get("order_content")
            if name and phone and address and content:
                conn.execute("INSERT INTO orders (name, phone, address, content) VALUES (?, ?, ?, ?)", (name, phone, address, content))
                conn.commit()
                flash(f"✅ Cảm ơn {name} đã đặt hàng!", "success")
            else:
                flash("❗ Vui lòng điền đầy đủ thông tin đơn hàng.")

        elif form_type == "feedback":
            name = request.form.get("feedback_name")
            rating = request.form.get("feedback_rating")
            message = request.form.get("feedback_message")
            if name and rating and message:
                conn.execute("INSERT INTO feedbacks (name, rating, message) VALUES (?, ?, ?)", (name, rating, message))
                conn.commit()
                flash(f"💬 Cảm ơn {name} đã đánh giá {rating} sao!", "success")
            else:
                flash("❗ Vui lòng điền đầy đủ thông tin đánh giá.")

    menu_items = conn.execute("SELECT * FROM menu").fetchall()
    order_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    feedback_count = conn.execute("SELECT COUNT(*) FROM feedbacks").fetchone()[0]
    conn.close()
    return render_template("home.html", menu_items=menu_items, order_count=order_count, feedback_count=feedback_count)

@app.route("/add", methods=["POST"])
@login_required
def add_item():
    if current_user.role != "admin":
        abort(403)
    name = request.form["name"]
    price = request.form["price"]
    image_file = request.files["image"]
    image_path = ""
    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        filename = f"{os.path.splitext(filename)[0]}_{int(time.time())}{os.path.splitext(filename)[1]}"
        image_file.save(os.path.join(UPLOAD_FOLDER, filename))
        image_path = f"uploads/{filename}"

    conn = get_db_connection()
    conn.execute("INSERT INTO menu (name, price, image) VALUES (?, ?, ?)", (name, price, image_path))
    conn.commit()
    conn.close()
    flash("Thêm món mới thành công.", "success")
    return redirect(url_for("admin_panel"))

@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM menu WHERE id = ?", (item_id,)).fetchone()
    if not item:
        abort(404)
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        image_file = request.files["image"]
        image_path = item["image"]
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            filename = f"{os.path.splitext(filename)[0]}_{int(time.time())}{os.path.splitext(filename)[1]}"
            image_file.save(os.path.join(UPLOAD_FOLDER, filename))
            image_path = f"uploads/{filename}"
        conn.execute("UPDATE menu SET name = ?, price = ?, image = ? WHERE id = ?", (name, price, image_path, item_id))
        conn.commit()
        conn.close()
        flash("Cập nhật món ăn thành công.", "success")
        return redirect(url_for("admin_panel"))
    conn.close()
    return render_template("edit.html", item=item)

@app.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    conn.execute("DELETE FROM menu WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Xóa món ăn thành công.", "success")
    return redirect(url_for("admin_panel"))

@app.route("/reports")
@login_required
def view_reports():
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    feedbacks = conn.execute("SELECT * FROM feedbacks ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("reports.html", orders=orders, feedbacks=feedbacks)

@app.route("/export/orders")
@login_required
def export_orders():
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT name, phone, address, content, created_at FROM orders ORDER BY created_at DESC", conn)
    filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join("static", filename)
    df.to_excel(filepath, index=False)
    conn.close()
    return send_file(filepath, as_attachment=True)

@app.route("/export/feedbacks")
@login_required
def export_feedbacks():
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT name, rating, message, created_at FROM feedbacks ORDER BY created_at DESC", conn)
    filename = f"feedbacks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join("static", filename)
    df.to_excel(filepath, index=False)
    conn.close()
    return send_file(filepath, as_attachment=True)

@app.route("/backup")
@login_required
def backup_db():
    if current_user.role != "admin":
        abort(403)
    backup_path = "menu_backup.db"
    shutil.copyfile(DATABASE, backup_path)
    flash(f"✅ Đã sao lưu thành công: {backup_path}", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/users")
@login_required
def list_users():
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("admin_users.html", users=users)

@app.route("/admin/users/add", methods=["GET", "POST"])
@login_required
def add_user():
    if current_user.role != "admin":
        abort(403)
    form = AddUserForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        raw_password = form.password.data.strip() or "123456"
        password_hash = generate_password_hash(raw_password)
        role = form.role.data
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
            conn.commit()
            flash(f"✅ Đã thêm người dùng {username} (mật khẩu: {raw_password})", "success")
            return redirect(url_for("list_users"))
        except sqlite3.IntegrityError:
            flash("❌ Tên đăng nhập đã tồn tại.", "danger")
        finally:
            conn.close()
    return render_template("admin_user_add.html", form=form)

@app.route("/admin/users/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        flash("Không tìm thấy người dùng.", "danger")
        return redirect(url_for("list_users"))

    if request.method == "POST":
        new_role = request.form.get("role")
        new_password = request.form.get("new_password")
        if new_role:
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        if new_password and len(new_password) >= 6:
            new_hash = generate_password_hash(new_password)
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()
        conn.close()
        flash("✅ Cập nhật người dùng thành công.", "success")
        return redirect(url_for("list_users"))

    conn.close()
    return render_template("admin_user_edit.html", user=user)

@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        abort(403)
    if current_user.id == user_id:
        flash("❌ Bạn không thể xoá chính mình.", "warning")
        return redirect(url_for("list_users"))
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("🗑️ Đã xoá người dùng.", "info")
    return redirect(url_for("list_users"))

if __name__ == "__main__":
    app.run(debug=True)
