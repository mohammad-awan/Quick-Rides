from app import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship


class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)


class AdminReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_email = db.Column(db.String(120))  # link by email
    message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    price_per_day = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.String(50), nullable=False)
    transmission = db.Column(db.String(50), nullable=False)
    seats = db.Column(db.String(50), nullable=False)
    luggage = db.Column(db.String(50), nullable=False)
    fuel = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)
    image_main = db.Column(db.String(100), nullable=False)
    image_extra = db.Column(db.String(100), nullable=True)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    image_filename = db.Column(db.String(100), nullable=False)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Assuming User model exists
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    cnic = db.Column(db.String(20), nullable=False)
    contact_no = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    ref_name = db.Column(db.String(100), nullable=False)
    ref_contact = db.Column(db.String(20), nullable=False)
    ref_address = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Pending")  # "Pending", "Confirmed"
    booked_on = db.Column(db.DateTime, default=datetime.utcnow)
    confirmation_message = db.Column(db.String(300))
    rejection_message = db.Column(db.String(300))
    user = relationship("User", backref="bookings")
    car = relationship("Car", backref="bookings")

    def __repr__(self):
        return f"<Booking {self.id} | Car: {self.car_id} | User: {self.user_id} | Status: {self.status}>"


class DriverApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), nullable=False, unique=True)
    experience = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    confirmation_message = db.Column(db.String(300))
    rejection_message = db.Column(db.String(300))
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    cnic = db.Column(db.String(25), unique=True, nullable=False)
    home_address = db.Column(db.String(255), nullable=False)
    role_in_office = db.Column(db.String(100), nullable=False)
    join_date = db.Column(db.DateTime)
    left_of_date = db.Column(db.String(100))
    picture = db.Column(db.String(120), nullable=True)  # store image filename

