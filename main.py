from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db
from models import User, Room, Reservation
from dotenv import load_dotenv
import os
from datetime import datetime

# load_dotenv()

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SECRET_KEY'] = 'tajny_klic'

# db.init_app(app)

# @app.route('/')
# def index():
#     # Získání aktuálně vybraných hodnot z URL
#     f_faculty = request.args.get('faculty')
#     f_building = request.args.get('building')
#     f_room = request.args.get('room_number')

#     # 1. Kaskáda pro seznam Fakult
#     fakulty = db.session.query(Room.faculty).distinct().all()
#     seznam_fakult = [f[0] for f in fakulty if f[0]]

#     # 2. Kaskáda pro seznam Budov
#     budovy_query = db.session.query(Room.building).distinct()
#     if f_faculty:
#         budovy_query = budovy_query.filter(Room.faculty == f_faculty)
#     seznam_budov = [b[0] for b in budovy_query.all() if b[0]]

#     # 3. Kaskáda pro seznam Místností (tvůj nový filtr)
#     mistnosti_query = db.session.query(Room.room_number).distinct()
#     if f_faculty:
#         mistnosti_query = mistnosti_query.filter(Room.faculty == f_faculty)
#     if f_building:
#         mistnosti_query = mistnosti_query.filter(Room.building == f_building)
#     seznam_mistnosti_filtr = [m[0] for m in mistnosti_query.all() if m[0]]

#     # 4. Finální filtrování hlavní tabulky
#     query = Room.query
#     if f_faculty:
#         query = query.filter(Room.faculty == f_faculty)
#     if f_building:
#         query = query.filter(Room.building == f_building)
#     if f_room:
#         query = query.filter(Room.room_number == f_room)

#     vsechny_mistnosti = query.all()

#     return render_template('index.html', 
#                            rooms=vsechny_mistnosti, 
#                            fakulty=seznam_fakult, 
#                            budovy=seznam_budov,
#                            mistnosti=seznam_mistnosti_filtr,
#                            selected_faculty=f_faculty,
#                            selected_building=f_building,
#                            selected_room_number=f_room)

# @app.route('/reserve', methods=['POST'])
# def make_reservation():
#     try:
#         room_id = request.form.get('room_id')
#         res_date = request.form.get('res_date')      
#         start_t = request.form.get('start_time')     
#         end_t = request.form.get('end_time')         
#         reason = request.form.get('reason')

#         start_dt = datetime.strptime(f"{res_date} {start_t}", '%Y-%m-%d %H:%M')
#         end_dt = datetime.strptime(f"{res_date} {end_t}", '%Y-%m-%d %H:%M')

#         # 1. KONTROLA: Konec nesmí být před začátkem
#         if end_dt <= start_dt:
#             flash('Chyba: Konec rezervace musí být po jejím začátku!', 'danger')
#             return redirect(url_for('index'))

#         # --- 2. KONTROLA KOLIZÍ ---
#         # Najdeme, jestli už existuje rezervace pro tuto místnost,
#         # která je schválená nebo čeká, a její čas se překrývá s naším.
#         kolize = Reservation.query.filter(
#             Reservation.room_id == room_id,
#             Reservation.status.in_(['pending', 'approved']),
#             Reservation.start_time < end_dt,
#             Reservation.end_time > start_dt
#         ).first()

#         if kolize:
#             kolize_start = kolize.start_time.strftime('%H:%M')
#             kolize_end = kolize.end_time.strftime('%H:%M')
#             flash(f'Chyba kolize: Místnost je již zarezervována (od {kolize_start} do {kolize_end}).', 'danger')
#             return redirect(url_for('index'))

#         new_res = Reservation(
#             user_id=1, # Falešné přihlášení (Jan Novák)
#             room_id=room_id,
#             start_time=start_dt,
#             end_time=end_dt,
#             reason=reason,
#             status='pending'
#         )

#         db.session.add(new_res)
#         db.session.commit()
#         flash('Rezervace úspěšně odeslána a čeká na schválení!', 'success')

#     except Exception as e:
#         flash(f'Chyba: {str(e)}', 'danger')

#     return redirect(url_for('index'))

# if __name__ == '__main__':
#     app.run(debug=True)


# ==========================================
# REST API
# ==========================================


# NOVÉ IMPORTY PRO API A TOKENY
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['JWT_SECRET_KEY'] = 'super_tajne_heslo_pro_nasi_aplikaci' 
jwt = JWTManager(app)

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


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "message": "Přihlášení úspěšné",
            "access_token": access_token,
            "role": user.role
        }), 200
    else:
        return jsonify({"error": "Špatný e-mail nebo heslo"}), 401 # 401 znamená Neautorizováno

@app.route('/api/my-profile', methods=['GET'])
@jwt_required()
def my_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }), 200

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    f_faculty = request.args.get('faculty')
    f_building = request.args.get('building')

    query = Room.query

    if f_faculty:
        query = query.filter(Room.faculty == f_faculty)
    if f_building:
        query = query.filter(Room.building == f_building)

    mistnosti = query.all()

    rooms_data = []
    for room in mistnosti:
        rooms_data.append({
            "id": room.id,
            "room_number": room.room_number,
            "faculty": room.faculty,
            "building": room.building,
            "floor": room.floor,
            "room_type": room.room_type,
            "capacity": room.capacity,
            "notes": room.notes
        })

    return jsonify(rooms_data), 200

@app.route('/api/reserve', methods=['POST'])
@jwt_required() # Ochrana: Musí mít Token!
def api_reserve():
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    room_id = data.get('room_id')
    res_date = data.get('res_date')      # Očekáváme např. '2023-11-01'
    start_t = data.get('start_time')     # Očekáváme např. '10:00'
    end_t = data.get('end_time')         # Očekáváme např. '12:00'
    reason = data.get('reason')

    if not all([room_id, res_date, start_t, end_t, reason]):
        return jsonify({"error": "Chybí některý z povinných údajů!"}), 400

    try:
        start_dt = datetime.strptime(f"{res_date} {start_t}", '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(f"{res_date} {end_t}", '%Y-%m-%d %H:%M')

        if end_dt <= start_dt:
            return jsonify({"error": "Konec rezervace musí být po její začátku."}), 400

        kolize = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.status.in_(['pending', 'approved']),
            Reservation.start_time < end_dt,
            Reservation.end_time > start_dt
        ).first()

        if kolize:
            kolize_start = kolize.start_time.strftime('%H:%M')
            kolize_end = kolize.end_time.strftime('%H:%M')
            return jsonify({
                "error": "Kolize časů",
                "message": f"Místnost je v tento čas již obsazena (od {kolize_start} do {kolize_end})."
            }), 409

        new_res = Reservation(
            user_id=current_user_id,
            room_id=room_id,
            start_time=start_dt,
            end_time=end_dt,
            reason=reason,
            status='pending'
        )

        db.session.add(new_res)
        db.session.commit()
        
        return jsonify({"message": "Rezervace úspěšně odeslána a čeká na schválení!"}), 201

    except ValueError:
        return jsonify({"error": "Špatný formát data nebo času."}), 400
    except Exception as e:
        return jsonify({"error": f"Neočekávaná chyba: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)