from flask import Flask, render_template, request, redirect, url_for, flash
from database import db
from models import User, Room, Reservation
from dotenv import load_dotenv
import os
from datetime import datetime

# --- NOVÉ IMPORTY PRO PŘIHLÁŠENÍ ---
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tajny_klic'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Sem tě to hodí, když nejsi přihlášený
login_manager.login_message = "Pro rezervaci místnosti se prosím přihlaste."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@ujep.cz').first():
        test_admin = User(
            username='admin', 
            email='admin@ujep.cz', 
            password_hash=generate_password_hash('heslo123'), 
            role='admin'
        )
        db.session.add(test_admin)
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Vítej zpět, {user.username}!', 'success')
            return redirect(url_for('my_reservations'))
        else:
            flash('Špatný e-mail nebo heslo.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Byl jsi úspěšně odhlášen.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    f_faculty = request.args.get('faculty')
    f_building = request.args.get('building')
    f_room = request.args.get('room_number')

    fakulty = db.session.query(Room.faculty).distinct().all()
    seznam_fakult = [f[0] for f in fakulty if f[0]]

    budovy_query = db.session.query(Room.building).distinct()
    if f_faculty:
        budovy_query = budovy_query.filter(Room.faculty == f_faculty)
    seznam_budov = [b[0] for b in budovy_query.all() if b[0]]

    mistnosti_query = db.session.query(Room.room_number).distinct()
    if f_faculty:
        mistnosti_query = mistnosti_query.filter(Room.faculty == f_faculty)
    if f_building:
        mistnosti_query = mistnosti_query.filter(Room.building == f_building)
    seznam_mistnosti_filtr = [m[0] for m in mistnosti_query.all() if m[0]]

    query = Room.query
    if f_faculty:
        query = query.filter(Room.faculty == f_faculty)
    if f_building:
        query = query.filter(Room.building == f_building)
    if f_room:
        query = query.filter(Room.room_number == f_room)

    vsechny_mistnosti = query.all()

    return render_template('index.html', 
                           rooms=vsechny_mistnosti, 
                           fakulty=seznam_fakult, 
                           budovy=seznam_budov,
                           mistnosti=seznam_mistnosti_filtr,
                           selected_faculty=f_faculty,
                           selected_building=f_building,
                           selected_room_number=f_room)

@app.route('/my-reservations')
@login_required
def my_reservations():
    user_reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.start_time.desc()).all()
    return render_template('my_reservations.html', reservations=user_reservations)

@app.route('/cancel-reservation/<int:res_id>', methods=['POST'])
@login_required
def cancel_reservation(res_id):
    reservation = Reservation.query.get_or_404(res_id)
    
    if reservation.user_id != current_user.id:
        flash('Nemáte oprávnění zrušit tuto rezervaci.', 'danger')
        return redirect(url_for('my_reservations'))
        
    reservation.status = 'rejected'
    db.session.commit()
    flash('Rezervace byla úspěšně zrušena.', 'success')
    return redirect(url_for('my_reservations'))

@app.route('/reserve', methods=['POST'])
@login_required
def make_reservation():
    try:
        room_id = request.form.get('room_id')
        res_date = request.form.get('res_date')      
        start_t = request.form.get('start_time')     
        end_t = request.form.get('end_time')         
        reason = request.form.get('reason')
        # Nový parametr: Pustí nás dál, pokud uživatel potvrdil varování
        force = request.form.get('force') 

        start_dt = datetime.strptime(f"{res_date} {start_t}", '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(f"{res_date} {end_t}", '%Y-%m-%d %H:%M')

        if end_dt <= start_dt:
            flash('Chyba: Konec rezervace musí být po jejím začátku!', 'danger')
            return redirect(url_for('index'))

        # Hledáme kolizi
        kolize = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.status.in_(['pending', 'approved']),
            Reservation.start_time < end_dt,
            Reservation.end_time > start_dt
        ).first()

        # POKUD JE KOLIZE A UŽIVATEL JI JEŠTĚ NEPOTVRDIL:
        if kolize and not force:
            # Neposíláme ho pryč! Ukážeme mu stránku s dotazem A/N.
            room = Room.query.get(room_id)
            return render_template('collision_confirm.html', 
                                   room=room,
                                   res_date=res_date, start_t=start_t, end_t=end_t, reason=reason,
                                   kolize=kolize)

        # Pokud kolize není, NEBO uživatel klikl na "Přesto rezervovat" (force=True), uložíme to.
        new_res = Reservation(
            user_id=current_user.id,
            room_id=room_id,
            start_time=start_dt,
            end_time=end_dt,
            reason=reason,
            status='pending'
        )

        db.session.add(new_res)
        db.session.commit()
        
        if force:
            flash('Žádost o výjimku byla odeslána administrátorovi.', 'warning')
        else:
            flash('Rezervace úspěšně odeslána a čeká na schválení!', 'success')

    except Exception as e:
        flash(f'Chyba: {str(e)}', 'danger')

    return redirect(url_for('my_reservations'))

if __name__ == '__main__':
    app.run(debug=True)