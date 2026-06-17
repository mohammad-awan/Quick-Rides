from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime
from sqlalchemy import or_, and_
from app.models import User, ContactMessage, Car, Booking, DriverApplication
import re
import os

user_bp = Blueprint(
    'user_bp',
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates', 'user_templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static', 'user_static')
)

# total_cars = Car.query.count()
# total_bookings = Booking.query.count()


@user_bp.route("/")
def index():
    total_cars = Car.query.count()
    total_users = User.query.count()
    car_list = Car.query.order_by(Car.id.desc()).all()
    return render_template("index.html", cars=car_list, total_cars=total_cars, users=total_users)


@user_bp.route("/about")
def about():
    total_cars = Car.query.count()
    total_users = User.query.count()
    return render_template("about.html", cars=total_cars, users=total_users)


@user_bp.route("/cars")
def cars():
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    price_min = request.args.get('price_min', type=int)
    price_max = request.args.get('price_max', type=int)
    seats = request.args.get('seats', type=int)

    # Convert dates
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = None
        end_date = None

    # ✅ Swap dates if user gave wrong range
    if start_date and end_date and end_date < start_date:
        start_date, end_date = end_date, start_date

    # ✅ Swap prices if user gave wrong range
    if price_min and price_max and price_max < price_min:
        price_min, price_max = price_max, price_min

    # Filter logic
    if not (start_date or end_date or price_min or price_max or seats):
        car_list = Car.query.order_by(Car.id.desc()).all()
    else:
        query = Car.query

        if price_min is not None:
            query = query.filter(Car.price_per_day >= price_min)
        if price_max is not None:
            query = query.filter(Car.price_per_day <= price_max)
        if seats is not None:
            query = query.filter(Car.seats >= seats)

        if start_date and end_date:
            booked_car_ids = db.session.query(Booking.car_id).filter(
                Booking.start_date <= end_date,
                Booking.end_date >= start_date
            ).subquery()
            query = query.filter(~Car.id.in_(booked_car_ids))

        car_list = query.order_by(Car.id.desc()).all()

    return render_template("car.html", cars=car_list, start_date=start_date, end_date=end_date,
                           price_min=price_min, price_max=price_max, seats=seats)


@user_bp.route("/services")
def services():
    return render_template("services.html")


@user_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        new_msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(new_msg)
        db.session.commit()
        flash("Your message has been sent!", "success")
        return redirect('/contact')

    return render_template('contact.html')


@user_bp.route('/car/<int:car_id>')
def single_car(car_id):
    car = Car.query.get_or_404(car_id)
    car_list = Car.query.order_by(Car.id.desc()).all()
    return render_template('car-single.html', car=car, cars=car_list)


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("register.html")

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Email is already registered", "warning")
            return render_template("register.html")

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for('user_bp.login'))

    return render_template("register.html")


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['role'] = 'user'

            flash("Login successful", "success")
            return redirect(url_for('user_bp.index'))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")


@user_bp.route('/profile')
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('user_bp.profile'))
    return render_template("edit_profile.html", user=user)


@user_bp.route('/logout')
def logout():
    session.clear()  # ✅ This clears all session data like user_id, role, last_name
    flash("You have been logged out.", "info")
    return redirect(url_for('user_bp.login'))


def is_valid_cnic(cn):
    return re.match(r'^\d{5}-\d{7}-\d$', cn)


def is_valid_contact(con):
    return re.match(r'^03\d{2}-\d{7}$', con)


@user_bp.route('/book/<int:car_id>', methods=['GET', 'POST'])
def book_car(car_id):
    if 'user_id' not in session:
        return redirect(url_for('user_bp.login'))

    car = Car.query.get_or_404(car_id)
    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        cnic = request.form['cnic']
        contact_no = request.form['contact_no']
        address = request.form['address']
        ref_name = request.form['ref_name']
        ref_contact = request.form['ref_contact']
        ref_address = request.form['ref_address']

        try:
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        except ValueError:
            flash("❌ Invalid date format.", "danger")
            return render_template("booking.html", car=car)

        # Validate CNIC and Contact Format
        if not is_valid_cnic(cnic):
            flash("❌ Invalid CNIC format (xxxxx-xxxxxxx-x)", "danger")
            return render_template("booking.html", car=car)
        elif not is_valid_contact(contact_no):
            flash("❌ Invalid contact number (03xx-xxxxxxx)", "danger")
            return render_template("booking.html", car=car)
        elif not is_valid_contact(ref_contact):
            flash("❌ Invalid reference contact (03xx-xxxxxxx)", "danger")
            return render_template("booking.html", car=car)

        # Check car availability
        existing = Booking.query.filter(
            Booking.car_id == car_id,
            Booking.status == "Confirmed",
            or_(
                and_(Booking.start_date <= start_date, Booking.end_date >= start_date),
                and_(Booking.start_date <= end_date, Booking.end_date >= end_date),
                and_(Booking.start_date >= start_date, Booking.end_date <= end_date),
            )
        ).first()

        if existing:
            flash("❌ This car is already booked for selected dates.", "danger")
            return render_template("booking.html", car=car)

        # Save booking
        booking = Booking(
            user_id=user.id,
            car_id=car_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            cnic=cnic,
            contact_no=contact_no,
            address=address,
            ref_name=ref_name,
            ref_contact=ref_contact,
            ref_address=ref_address,
            start_date=start_date,
            end_date=end_date,
            booked_on=datetime.utcnow(),
            status="Pending"
        )
        db.session.add(booking)
        db.session.commit()
        return redirect(url_for('user_bp.check_booking', booking_id=booking.id))

    return render_template("booking.html", car=car)


@user_bp.route('/check_booking/<int:booking_id>')
def check_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('user_bp.login'))

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=session['user_id']
    ).first()

    if not booking:
        flash("❌ No booking found for this booking ID.", "danger")
        return redirect(url_for('user_bp.cars'))

    return render_template('check_booking.html', booking=booking)


@user_bp.route('/confirm_booking/<int:booking_id>', methods=['POST'])
def confirm_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('user_bp.login'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session['user_id']:
        flash("Unauthorized access to this booking.", "danger")
        return redirect(url_for('user_bp.check_booking', booking_id=booking.id))

    if booking.status == 'Pending':
        booking.status = 'Requested'
        db.session.commit()
        flash("✅ Booking request sent to admin for confirmation. Please wait.", "info")

    return redirect(url_for('user_bp.check_booking', booking_id=booking.id))


@user_bp.route('/terms')
def terms():
    return render_template('term_conditions.html')


@user_bp.route('/best-price')
def best_price():
    return render_template('best_price.html')


@user_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


def is_valid_license(license_number):
    return bool(re.match(r'^DL-\d{10}$', license_number))


@user_bp.route('/become-driver', methods=['GET', 'POST'])
def become_driver():
    if 'user_id' not in session:
        return redirect(url_for('user_bp.login'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        license_number = request.form.get('license_number')
        experience = request.form.get('experience')

        # ✅ Check only if license number is already used
        existing_license = DriverApplication.query.filter_by(license_number=license_number).first()
        if existing_license:
            flash("⚠️ A request with this license number has already been submitted.", "warning")
            return redirect(url_for('user_bp.become_driver'))

        new_driver = DriverApplication(
            user_id=session['user_id'],
            full_name=full_name,
            email=email,
            phone=phone,
            license_number=license_number,
            experience=experience,
            status='Pending'
        )
        db.session.add(new_driver)
        db.session.commit()

        flash("✅ Application submitted. Please confirm your request.", "success")
        return redirect(url_for('user_bp.check_driver', driver_id=new_driver.id))

    return render_template('driver_application.html')


@user_bp.route('/check-driver/<int:driver_id>')
def check_driver(driver_id):
    driver = DriverApplication.query.get_or_404(driver_id)

    if request.method == 'POST':
        if driver.status == "Pending":
            driver.status = "Requested"
            db.session.commit()
            flash("Driver request submitted for approval.", "success")
        return redirect(url_for('some_next_page'))

    return render_template('check_driver.html', driver=driver)


@user_bp.route('/confirm_driver/<int:driver_id>', methods=['POST'])
def confirm_driver(driver_id):
    if 'user_id' not in session:
        return redirect(url_for('user_bp.login'))

    driver = DriverApplication.query.get_or_404(driver_id)

    if driver.user_id != session['user_id']:
        flash("Unauthorized access to this driver application.", "danger")
        return redirect(url_for('user_bp.check_driver', driver_id=driver.id))

    if driver.status == 'Pending':
        driver.status = 'Requested'
        db.session.commit()
        flash("✅ Your driver request is now submitted to admin for review.", "info")

    return redirect(url_for('user_bp.check_driver', driver_id=driver.id))


@user_bp.route('/faq')
def faq():
    return render_template('FAQ.html')



