import werkzeug
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import RegisterForm, LoginForm, EditForm, AdminForm, ResetPassword, ChangePassword, OrderForm, OrderEditForm
from functools import wraps
from flask import abort
import os
from datetime import date, datetime
from twilio.twiml.messaging_response import MessagingResponse
from notification import Notification

# Initiate the flask app with bootstrap and wtf forms
# Secret key is to be stored in environ variable in heroku as well as pycharm
app = Flask(__name__)
# app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SECRET_KEY'] = "q1w2e3r4"
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB from Pycharm
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///club.db")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Use login manager to find current user status and authenticate
login_manager = LoginManager()
login_manager.init_app(app)

# Coffee Price Dictionary
coffee_dict = {
    "Cappuccino": 3,
    "Mocha": 2,
    "Latte": 1
}


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(100))
    fetcher = db.Column(db.String(100))

    orders = relationship("Order", back_populates="user")
    receipts = relationship("Receipt", back_populates="user")


class Receipt(db.Model):
    __tablename__ = "receipts"
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.String(200))
    price = db.Column(db.String(100))
    receipt_number = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = relationship("User", back_populates="receipts")


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = relationship("User", back_populates="orders")

    coffee_type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    date = db.Column(db.String(100))
    payment_status = db.Column(db.String(100))


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/cc')
def cc():
    return render_template("cc.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()
        # Use flash messages to make login interactive
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                if user.name == "Administrator":
                    return redirect(url_for('admin_page'))
                else:
                    return redirect(url_for('user_profile', user_id=user.id))
            else:
                flash('Invalid password provided')
                return redirect(url_for('login'))
        else:
            flash('Invalid user provided')
            return redirect(url_for('login'))

    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        if User.query.filter_by(email=register_form.email.data).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        # Create new user and login the new user
        new_user = User(
            email=register_form.email.data,
            password=werkzeug.security.generate_password_hash(register_form.password.data, method='pbkdf2:sha256',
                                                              salt_length=8),
            name=register_form.name.data.title(),
            mobile=register_form.mobile.data,
            fetcher="False"
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('user_profile', user_id=new_user.id))

    return render_template("register.html", form=register_form)


@app.route('/user_profile/<user_id>', methods=["GET", "POST"])
@login_required
def user_profile(user_id):
    all_orders = Order.query.all()
    order_form = OrderForm()
    # Give user the privilege to change password through a wtf change_password_form
    change_password_form = ChangePassword()
    # Find the user entry from the database
    # user = User.query.filter_by(id=user_id).first()
    # Code to change password
    if change_password_form.validate_on_submit():
        new_password = change_password_form.password.data
        current_user.password = werkzeug.security.generate_password_hash(new_password, method='pbkdf2:sha256',
                                                                         salt_length=8)
        db.session.commit()
        logout_user()
        return redirect(url_for('login'))

    if order_form.validate_on_submit():
        new_order = Order(
            coffee_type=order_form.coffee_type.data,
            quantity=order_form.quantity.data,
            price=coffee_dict[order_form.coffee_type.data]*order_form.quantity.data,
            date=date.today().strftime("%B %d, %Y"),
            payment_status="Open",
            user=current_user,
        )
        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for('user_profile', user_id=current_user.id))
    return render_template("user_profile.html", orders=all_orders, oform=order_form, form=change_password_form, user=current_user)


@app.route('/edit_profile', methods=["GET", "POST"])
@login_required
def edit_profile():
    # Allow the user to edit certain parts from his profile
    edit_form = EditForm(
        name=current_user.name,
        mobile=current_user.mobile,
    )
    # Prefill the edit form with the current values
    if edit_form.validate_on_submit():
        current_user.name = edit_form.name.data
        current_user.mobile = edit_form.mobile.data
        db.session.commit()
        return redirect(url_for('user_profile', user_id=current_user.id))

    return render_template("edit_profile.html", form=edit_form)


@app.route('/admin_page', methods=["GET", "POST"])
@admin_only
def admin_page():
    # Create an admin password reset form
    reset_password_form = ResetPassword()
    # Query for all users to display the users in admin page
    all_users = User.query.all()
    all_receipts = Receipt.query.all()
    all_orders = Order.query.all()
    # Reset password code
    if reset_password_form.validate_on_submit():
        name = reset_password_form.name.data
        req_user = User.query.filter_by(name=name).first()
        if req_user:
            req_user.password = werkzeug.security.generate_password_hash("cc1234", method='pbkdf2:sha256',
                                                                         salt_length=8)
            db.session.commit()
            flash('Password reset to cc1234')
        else:
            flash('User not found')
        return redirect(url_for('admin_page'))
    return render_template("admin_page.html", users=all_users, orders=all_orders, receipts=all_receipts, form=reset_password_form)


@app.route('/admin_edit/<user_id>', methods=["GET", "POST"])
@admin_only
def admin_edit(user_id):
    # After click on user from admin page, allow admin to update certain fields in the user profile
    req_user = User.query.filter_by(id=user_id).first()
    admin_form = AdminForm(
        name=req_user.name,
        mobile=req_user.mobile,
        fetcher=req_user.fetcher
    )
    if admin_form.validate_on_submit():
        req_user.name = admin_form.name.data
        req_user.mobile = admin_form.mobile.data
        req_user.fetcher = admin_form.fetcher.data
        db.session.commit()
        return redirect(url_for('user_profile', user_id=req_user.id))

    return render_template("admin_edit.html", form=admin_form)


@app.route('/order_edit/<order_id>', methods=["GET", "POST"])
@login_required
def order_edit(order_id):
    # After click on user from profile page, allow user to update certain fields in the order
    req_order = Order.query.filter_by(id=order_id).first()
    order_edit_form = OrderEditForm(
        coffee_type=req_order.coffee_type,
        price=req_order.price,
        quantity=req_order.quantity,
        payment_status=req_order.payment_status
     )
    if order_edit_form.validate_on_submit():
        req_order.coffee_type = order_edit_form.coffee_type.data
        req_order.price = order_edit_form.price.data
        req_order.quantity = order_edit_form.quantity.data
        print(str(req_order.payment_status))
        print(req_order.payment_status)
        req_order.payment_status = str(req_order.payment_status)  # Admin status change not working. Check Selectfield returns
        db.session.commit()
        return redirect(url_for('user_profile', user_id=current_user.id))

    return render_template("order_edit.html", form=order_edit_form)


@app.route('/make_receipt', methods=["GET", "POST"])
@login_required
def make_receipt():
    items_price = 0.0
    items = []
    open_orders = Order.query.filter_by(payment_status="Open").all()
    for order in open_orders:
        items.append((order.coffee_type, order.quantity, order.price))
        items_price = items_price + float(order.price)
        order.payment_status = "Close"
    db.session.commit()

    new_receipt = Receipt(
        items=str(items),
        price=str(items_price),
        user=current_user,
        receipt_number=date.today().strftime("%B %d, %Y") + "_" + current_user.name
        )
    db.session.add(new_receipt)
    db.session.commit()

    with open(f'./static/Receipts/{date.today().strftime("%B%d%Y") + "_" + current_user.name}.txt', 'w') as file:
        file.write("Summary of (Coffee_Type, Quantity, Price)\n")
        file.write(str(items))
        file.write(f"\nTotal Price: {str(items_price)}")

    return redirect(url_for('user_profile', user_id=current_user.id))


@app.route("/sms", methods=['GET', 'POST'])
def sms():
    # Start our TwiML response
    resp = MessagingResponse()
    mobile_number = request.values.get('From').split(":")[-1]  # Only tested with whatsapp
    message_body = request.values.get('Body', None)
    if message_body.lower() == "order":
        text = "Please order in format coffee_type-quantity e.g. Cappuccino-3\n"
        menu = ""
        for coffee in coffee_dict:
            menu += str(coffee) + ":" + str(coffee_dict[coffee]) + " EUR" + "\n"
        resp.message(text+menu)
    else:
        try:
            quantity = int(message_body.split("-")[-1])
            coffee_type = message_body.split("-")[0]
            # Identify User and create a new order
            req_user = User.query.filter_by(mobile=mobile_number).first()
            new_order = Order(
                coffee_type=coffee_type,
                quantity=quantity,
                price=coffee_dict[coffee_type]*quantity,
                date=date.today().strftime("%B %d, %Y"),
                payment_status="Open",
                user=req_user,
            )
            db.session.add(new_order)
            db.session.commit()
            # Add confirmation message
            resp.message(f"Received from {req_user.name, mobile_number} an order for {message_body}")
        except KeyError:
            resp.message("Error: Order not in menu or not in correct format.")
        except ValueError:
            resp.message("Error: Order not in menu or not in correct format.")

    # Send summary of orders at 10 AM every day / Triggered by a whatsapp message sent to the number at or after 10
    if int(datetime.now().strftime("%H")) >= 10:
        notification = Notification()
        items_price = 0.0
        items = []
        open_orders = Order.query.filter_by(payment_status="Open").all()
        for order in open_orders:
            items.append((order.coffee_type, order.quantity, order.price))
            items_price = items_price + float(order.price)
        mail_text = "Summary of (Coffee_Type, Quantity, Price)\n" + str(items) + f"\nTotal Price: {str(items_price)}"
        fetcher_email = User.query.filter_by(fetcher="True").first().email
        notification.send_email(mail_text, fetcher_email)

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True, port=5020)
