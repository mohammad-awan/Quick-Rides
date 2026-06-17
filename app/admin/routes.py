from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, current_user
from werkzeug.security import check_password_hash
from PIL import Image
# from app.decorators import admin_required
from datetime import datetime
from werkzeug.utils import secure_filename
from app import db
from app.models import Admin, User, ContactMessage, AdminReply, Car, CarImage, Booking, DriverApplication, Staff
import os
import uuid

admin_bp = Blueprint(
    'admin_bp',
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates', 'admin_templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static', 'admin_static')
)


UPLOAD_FOLDER = os.path.join(admin_bp.static_folder, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
folder_path = os.path.join(admin_bp.static_folder, 'admin_staff_pics')
os.makedirs(folder_path, exist_ok=True)  # ✅ Make sure folder exists


@admin_bp.route("/", methods=["GET", "POST"])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            error = 'Invalid username or password'
            return render_template('admin_login.html', error=error)

    return render_template('admin_login.html')


@admin_bp.route("/admin_dashboard")
# @login_required
# @admin_required
def admin_dashboard():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    total_cars = Car.query.count()
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    pending_requests = Booking.query.filter_by(status='Pending').count()
    rejected_bookings = Booking.query.filter_by(status='Rejected').count()
    driver_pending = DriverApplication.query.filter_by(status='Pending').count()
    driver_rejected = DriverApplication.query.filter_by(status='Rejected').count()

    return render_template(
        "home.html",
        total_cars=total_cars,
        total_users=total_users,
        admin=current_user,
        total_bookings=total_bookings,
        pending_requests=pending_requests,
        rejected_bookings=rejected_bookings,
        driver_pending=driver_pending,
        driver_rejected=driver_rejected
        # This will be your logged-in admin
    )


@admin_bp.route('/manage_users')
# @login_required
# @admin_required
def manage_users():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    users = User.query.order_by(User.registered_on.desc()).all()
    return render_template('manage_users.html', users=users)


@admin_bp.route('/messages/<email>', methods=['GET', 'POST'])
def chat_box(email):
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    if request.method == 'POST':
        reply = request.form['reply']
        new_reply = AdminReply(contact_email=email, message=reply)
        db.session.add(new_reply)
        db.session.commit()
        return redirect(url_for('admin_bp.chat_box', email=email))

    user_msgs = ContactMessage.query.filter_by(email=email).order_by(ContactMessage.sent_at).all()
    admin_msgs = AdminReply.query.filter_by(contact_email=email).order_by(AdminReply.sent_at).all()
    user_name = user_msgs[0].name if user_msgs else "User"

    all_msgs = sorted(
        [{'from': user_name, 'text': m.message, 'time': m.sent_at} for m in user_msgs] +
        [{'from': 'admin', 'text': m.message, 'time': m.sent_at} for m in admin_msgs],
        key=lambda x: x['time']
    )

    return render_template('chat_box.html', email=email, messages=all_msgs)


@admin_bp.route('/messages')
# @login_required
# @admin_required
def view_messages():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    emails = db.session.query(ContactMessage.email).distinct().all()
    emails = [e[0] for e in emails]
    return render_template('messages_list.html', emails=emails)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Resize image safely
def resize_image(image_path, size=(800, 600)):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")  # Ensure compatibility
        img = img.resize(size, Image.LANCZOS)
        img.save(image_path)
        print(f"Image resized: {image_path}")
    except Exception as e:
        print("Resize error:", e)


@admin_bp.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    if request.method == 'POST':
        try:
            print("📥 POST received")

            # Get form data
            name = request.form['name']
            brand = request.form['brand']
            price_per_day = request.form['price_per_day']
            transmission = request.form['transmission']
            seats = request.form['seats']
            luggage = request.form['luggage']
            fuel = request.form['fuel']
            mileage = request.form['mileage']
            description = request.form.get('description')
            features = request.form.get('features')

            # Handle image uploads
            files = request.files.getlist('images')
            saved_images = []

            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    resize_image(filepath)
                    saved_images.append(filename)
                    print("✅ Image saved:", filename)

            if not saved_images:
                flash("At least one valid image is required.", "danger")
                return redirect(request.url)

            image_main = saved_images[0]
            image_extra = ','.join(saved_images[1:]) if len(saved_images) > 1 else None

            car = Car(
                name=name,
                brand=brand,
                price_per_day=price_per_day,
                transmission=transmission,
                seats=seats,
                luggage=luggage,
                fuel=fuel,
                mileage=mileage,
                description=description,
                features=features,
                image_main=image_main,
                image_extra=image_extra,
                added_on=datetime.utcnow()
            )
            db.session.add(car)
            db.session.commit()
            print("✅ Car saved:", car.name)

            for filename in saved_images:
                db.session.add(CarImage(car_id=car.id, image_filename=filename))
            db.session.commit()
            print("✅ CarImages saved")

            flash('Car added successfully!', 'success')
            return redirect(url_for('admin_bp.add_car'))

        except Exception as e:
            print("❌ Error occurred:", e)
            flash("An error occurred while adding the car.", "danger")
            return redirect(request.url)

    return render_template('add_car.html')


@admin_bp.route('/edit_car/<int:car_id>', methods=['GET', 'POST'])
# @login_required
# @admin_required
def edit_car(car_id):
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    car = Car.query.get_or_404(car_id)

    if request.method == 'POST':
        car.name = request.form['name']
        car.brand = request.form['brand']
        car.price_per_day = request.form['price_per_day']
        car.transmission = request.form['transmission']
        car.seats = request.form['seats']
        car.luggage = request.form['luggage']
        car.fuel = request.form['fuel']
        car.mileage = request.form['mileage']
        car.description = request.form.get('description')
        car.features = request.form.get('features')

        files = request.files.getlist('images')
        saved_images = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                saved_images.append(filename)

        if saved_images:
            prev_images = CarImage.query.filter_by(car_id=car.id).all()
            for img in prev_images:
                img_path = os.path.join(UPLOAD_FOLDER, img.image_filename)
                if os.path.exists(img_path):
                    os.remove(img_path)
                db.session.delete(img)

            car.image_main = saved_images[0]
            car.image_extra = ','.join(saved_images[1:]) if len(saved_images) > 1 else None

            for filename in saved_images:
                db.session.add(CarImage(car_id=car.id, image_filename=filename))

        db.session.commit()
        flash('Car updated successfully!', 'success')
        return redirect(url_for('admin_bp.manage_cars'))

    return render_template('edit_car.html', car=car)


@admin_bp.route('/delete_car/<int:car_id>', methods=['POST'])
# @login_required
# @admin_required
def delete_car(car_id):
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    car = Car.query.get_or_404(car_id)

    if car.image_main:
        main_path = os.path.join(UPLOAD_FOLDER, car.image_main)
        if os.path.exists(main_path):
            os.remove(main_path)

    if car.image_extra:
        for img in car.image_extra.split(','):
            extra_path = os.path.join(UPLOAD_FOLDER, img)
            if os.path.exists(extra_path):
                os.remove(extra_path)

    CarImage.query.filter_by(car_id=car.id).delete()

    db.session.delete(car)
    db.session.commit()

    flash('Car deleted successfully!', 'success')
    return redirect(url_for('admin_bp.manage_cars'))


@admin_bp.route('/manage_cars')
# @login_required
# @admin_required
def manage_cars():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    all_cars = Car.query.order_by(Car.added_on.desc()).all()
    return render_template('manage_cars.html', cars=all_cars)


@admin_bp.route("/booking-requests")
def booking_requests():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    bookings = Booking.query.filter_by().order_by(Booking.booked_on.desc()).all()
    return render_template("booking_requests.html", bookings=bookings)


@admin_bp.route("/confirm-booking/<int:booking_id>", methods=['POST'])
def confirm_booking(booking_id):
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.status == "Requested":
        booking.status = "Confirmed"
        booking.confirmation_message = (
            f"✅ Your booking of {booking.car.name} from {booking.start_date} to {booking.end_date} "
            f"by name {booking.first_name} {booking.last_name} is confirmed."
        )
        db.session.commit()
        flash("Booking confirmed!", "success")

    return redirect(url_for('admin_bp.booking_requests'))


@admin_bp.route("/reject-booking/<int:booking_id>", methods=['POST'])
def reject_booking(booking_id):
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.status == "Requested":
        booking.status = "Rejected"
        booking.rejection_message = (
            "❌ Your booking is rejected because the given data is not verified. "
            "If you still want booking, then please visit our office."
        )
        db.session.commit()
        flash("Booking rejected.", "danger")

    return redirect(url_for('admin_bp.booking_requests'))


@admin_bp.route('/driver-requests')
def driver_requests():
    requested_drivers = DriverApplication.query.filter_by().order_by(DriverApplication.applied_on.desc()).all()
    return render_template('driver_requests.html', drivers=requested_drivers)


@admin_bp.route('/approve-driver/<int:driver_id>', methods=['POST'])
def approve_driver(driver_id):
    driver = DriverApplication.query.get_or_404(driver_id)
    if driver.status == "Requested":
        driver.status = "Approved"
        driver.confirmation_message = f"✅ Congratulations {driver.full_name}, your driver request has been approved!"
        db.session.commit()
        flash("Driver approved successfully!", "success")
    return redirect(url_for('admin_bp.driver_requests'))


@admin_bp.route('/reject-driver/<int:driver_id>', methods=['POST'])
def reject_driver(driver_id):
    driver = DriverApplication.query.get_or_404(driver_id)
    if driver.status == "Requested":
        driver.status = "Rejected"
        driver.rejection_message = f"❌ Sorry {driver.full_name}, your driver request has been rejected."
        db.session.commit()
        flash("Driver rejected.", "danger")
    return redirect(url_for('admin_bp.driver_requests'))


@admin_bp.route('/staff-list')
def manage_staff():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_bp.admin_dashboard'))

    staff_members = Staff.query.order_by(Staff.join_date.desc()).all()
    return render_template('manage_staff.html', staff=staff_members)


@admin_bp.route('/add-staff', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        cnic = request.form.get('cnic')
        home_address = request.form.get('home_address')
        role_in_office = request.form.get('role_in_office')
        join_date = datetime.strptime(request.form.get('join_date'), "%Y-%m-%d")
        left_of_date = request.form.get('left_of_date')

        picture_file = request.files.get('picture')
        picture_filename = None
        if picture_file and picture_file.filename != '':
            picture_filename = secure_filename(picture_file.filename)
            folder_path = os.path.join(admin_bp.static_folder, 'admin_staff_pics')
            os.makedirs(folder_path, exist_ok=True)  # ✅ Ensure the folder exists
            picture_path = os.path.join(folder_path, picture_filename)
            picture_file.save(picture_path)

        new_staff = Staff(
            first_name=first_name,
            last_name=last_name,
            email=email,
            contact=contact,
            cnic=cnic,
            home_address=home_address,
            role_in_office=role_in_office,
            join_date=join_date,
            left_of_date=left_of_date,
            picture=picture_filename
        )

        db.session.add(new_staff)
        db.session.commit()
        flash("New staff member added successfully!", "success")
        return redirect(url_for('admin_bp.manage_staff'))

    return render_template('add_staff.html')


@admin_bp.route('/update-staff/<int:staff_id>', methods=['GET', 'POST'])
def update_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)

    if request.method == 'POST':
        staff.first_name = request.form.get('first_name')
        staff.last_name = request.form.get('last_name')
        staff.email = request.form.get('email')
        staff.contact = request.form.get('contact')
        staff.cnic = request.form.get('cnic')
        staff.home_address = request.form.get('home_address')
        staff.role_in_office = request.form.get('role_in_office')

        picture_file = request.files.get('picture')
        if picture_file and picture_file.filename != '':
            picture_filename = secure_filename(picture_file.filename)
            folder_path = os.path.join(admin_bp.static_folder, 'admin_staff_pics')
            os.makedirs(folder_path, exist_ok=True)  # ✅ Ensure the folder exists
            picture_path = os.path.join(folder_path, picture_filename)
            picture_file.save(picture_path)
            staff.picture = picture_filename

        db.session.commit()
        flash("Staff details updated successfully!", "success")
        return redirect(url_for('admin_bp.manage_staff'))

    return render_template(
        'update_staff.html',
        staff=staff,
        join_date_str=staff.join_date.strftime('%Y-%m-%d') if staff.join_date else '',
        left_of_date_str=staff.left_of_date.strftime('%Y-%m-%d') if staff.left_of_date else ''
    )



















