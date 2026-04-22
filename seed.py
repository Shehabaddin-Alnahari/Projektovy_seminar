from main import app
from database import db
from models import User, Room

# Spustíme to v kontextu aplikace
with app.app_context():
    # 1. Vyčistíme stará data (volitelné, ale dobré pro testování)
    db.session.query(Room).delete()
    db.session.query(User).delete()
    
    # 2. Vytvoříme testovací uživatele
    user1 = User(stag_username='jnovak', name='Jan Novák', email='novak@uni.cz', role='teacher')
    user2 = User(stag_username='adobra', name='Anna Dobrá', email='dobra@uni.cz', role='admin')
    
    # 3. Vytvoříme testovací místnosti
    room1 = Room(room_number='A101', building='Budova A', floor=1, capacity=30, room_type='PC Laboratoř', faculty='FAV', notes='20x PC, projektor')
    room2 = Room(room_number='A102', building='Budova A', floor=1, capacity=50, room_type='Přednášková místnost', faculty='FAV', notes='Projektor, tabule')
    room3 = Room(room_number='B205', building='Budova B', floor=2, capacity=15, room_type='Zasedací místnost', faculty='FST', notes='Videokonference')
    
    # 4. Přidáme do databáze a uložíme
    db.session.add_all([user1, user2, room1, room2, room3])
    db.session.commit()

    print("Testovací data byla úspěšně vložena do databáze!")