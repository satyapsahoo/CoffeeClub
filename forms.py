from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, IntegerField, SelectField
from wtforms.validators import DataRequired


# WTForm from flask bootstrap. WTForm is easier to handle than html forms.
class RegisterForm(FlaskForm):
    email = EmailField("Email*", validators=[DataRequired()])
    password = PasswordField("Password*", validators=[DataRequired()])
    name = StringField("Name*", validators=[DataRequired()])
    mobile = StringField("Mobile*")
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let me in")


class EditForm(FlaskForm):
    name = StringField("Name")
    mobile = StringField("Mobile")
    submit = SubmitField("Submit")


class AdminForm(FlaskForm):
    name = StringField("Name")
    mobile = StringField("Mobile")
    fetcher = SelectField("Fetcher", choices=["True", "False"])
    submit = SubmitField("Submit")


class ResetPassword(FlaskForm):
    name = StringField("Enter Name")
    submit = SubmitField("Reset Password")


class ChangePassword(FlaskForm):
    password = PasswordField("Enter New Password", validators=[DataRequired()])
    submit = SubmitField("Change Password")


class OrderForm(FlaskForm):
    coffee_type = SelectField("Coffee Type", choices=["Cappuccino", "Mocha", "Latte"], validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    submit = SubmitField("Place Order")


class OrderEditForm(FlaskForm):
    coffee_type = SelectField("Coffee Type", choices=["Cappuccino", "Mocha", "Latte"], validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    price = StringField("Price")
    payment_status = SelectField("Payment_Status", choices=["Open", "Close"])
    submit = SubmitField("Confirm Order")
