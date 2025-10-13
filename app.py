from flask import Flask, render_template, redirect, url_for, flash, request, abort
from config import Config
from models import db, User, Doctor, Appointment
from forms import RegisterForm, LoginForm, DoctorForm, AppointmentForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate

#admin details
# VALUES ('admin123', 'admin@example.com', 'pbkdf2:sha256:260000$TBTR0D4A0gvuaXHG$4fec38cacae6d2ceba7b49216c85af43c5670c8a0f2798b108b704c83c5c6d7a', '1234567890', 1)
#admin123:admin@123
#user1:user123
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Public pages ---
@app.route('/')
def index():
    docs = Doctor.query.order_by(Doctor.created_at.desc()).all()
    return render_template('index.html', doctors=docs)

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# --- User registration & login ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
        else:
            hashed = generate_password_hash(form.password.data)
            user = User(username=form.username.data, email=form.email.data,
                        password_hash=hashed, contact=form.contact.data, is_admin=False)
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully. Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully', 'success')
            next_page = request.args.get('next') or url_for('index')
            return redirect(next_page)
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# --- Admin panel (doctor management) ---
def admin_required(func):
    from functools import wraps
    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return decorated

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    doctors = Doctor.query.order_by(Doctor.created_at.desc()).all()
    return render_template('admin_panel.html', doctors=doctors,
                           admin_email=app.config['ADMIN_EMAIL'],
                           admin_contact=app.config['ADMIN_CONTACT'])

@app.route('/admin/add_doctor', methods=['GET','POST'])
@login_required
@admin_required
def add_doctor():
    form = DoctorForm()
    if form.validate_on_submit():
        doc = Doctor(
            name=form.name.data,
            degree=form.degree.data,
            specialization=form.specialization.data,
            bio=form.bio.data
        )
        db.session.add(doc)
        db.session.commit()
        flash('Doctor added', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('add_doctor.html', form=form)

@app.route('/doctor/<int:doc_id>')
def doctor_profile(doc_id):
    doc = Doctor.query.get_or_404(doc_id)
    return render_template('doctor_profile.html', doc=doc)

# --- Appointment booking (only for logged-in users) ---
@app.route('/book/<int:doc_id>', methods=['GET','POST'])
@login_required
def book(doc_id):
    if current_user.is_admin:
        flash('Admins cannot book appointments. Please manage doctors from the admin panel.', 'warning')
        return redirect(url_for('admin_panel'))
    doc = Doctor.query.get_or_404(doc_id)
    form = AppointmentForm()
    if form.validate_on_submit():
        # Basic availability check (no duplicate for same doctor at same date+time)
        existing = Appointment.query.filter(
    Appointment.doctor_id == doc.id,
    Appointment.date == form.date.data,
    Appointment.time == form.time.data,
    Appointment.status != 'cancelled'
).first()

        if existing:
            flash('This slot is already taken. Choose another time.', 'warning')
        else:
            appt = Appointment(
                doctor_id=doc.id,
                patient_id=current_user.id,
                date=form.date.data,
                time=form.time.data,
                status='pending'
            )
            db.session.add(appt)
            db.session.commit()
            flash('Appointment requested. You can view in My Appointments.', 'success')
            return redirect(url_for('my_appointments'))
    return render_template('book_appoinment.html', doctor=doc, form=form)

@app.route('/my_appointments')
@login_required
def my_appointments():
    if current_user.is_admin:
        flash('Admins cannot view personal appointments. Please manage doctors from the admin panel.', 'warning')
        return redirect(url_for('admin_panel'))
    appts = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.date, Appointment.time).all()
    return render_template('my_appointments.html', appointments=appts)

@app.route('/cancel/<int:appt_id>')
@login_required
def cancel_appointment(appt_id):
    if current_user.is_admin:
        abort(403)
    appt = Appointment.query.get_or_404(appt_id)
    if appt.patient_id != current_user.id:
        abort(403)
    appt.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled', 'info')
    return redirect(url_for('my_appointments'))

# --- Admin: view doctor's daily schedule ---
@app.route('/admin/schedule/<int:doc_id>')
@login_required
@admin_required
def admin_schedule(doc_id):
    # show today's schedule, or date passed via query
    date_str = request.args.get('date')
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date = datetime.utcnow().date()
    else:
        date = datetime.utcnow().date()
    appts = Appointment.query.filter_by(doctor_id=doc_id, date=date).order_by(Appointment.time).all()
    doc = Doctor.query.get_or_404(doc_id)
    return render_template('admin_panel.html', doctors=[doc], schedule=appts, admin_email=app.config['ADMIN_EMAIL'], admin_contact=app.config['ADMIN_CONTACT'])

@app.route('/admin/delete_doctor/<int:doc_id>', methods=['POST'])
@login_required
@admin_required
def delete_doctor(doc_id):
    doc = Doctor.query.get_or_404(doc_id)
    # Delete associated appointments first to avoid foreign key constraint
    Appointment.query.filter_by(doctor_id=doc_id).delete()
    db.session.delete(doc)
    db.session.commit()
    flash('Doctor deleted successfully', 'success')
    return redirect(url_for('admin_panel'))



# --- Error handlers ---
@app.errorhandler(403)
def forbidden(e):
    return render_template('404.html', message='Forbidden (403)'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', message='Not found (404)'), 404

if __name__ == '__main__':
    app.run(debug=True)
