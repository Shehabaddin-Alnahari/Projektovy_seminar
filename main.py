from flask import Flask, render_template
from database import db
from models import User, Room, Reservation
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Fyzické vytvoření tabulek
with app.app_context():
    db.create_all()

@app.route('/')
def index():
# Vytáhneme všechny místnosti z databáze
    vsechny_mistnosti = Room.query.all()
    # Pošleme je do HTML šablony pod názvem 'rooms'
    return render_template('index.html', rooms=vsechny_mistnosti)

if __name__ == '__main__':
    app.run(debug=True)