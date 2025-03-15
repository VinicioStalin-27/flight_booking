# db_model.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class FlightOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64), nullable=False)  # Identificador del usuario (chat_id de Telegram)
    flight_info = db.Column(db.Text, nullable=True)   # JSON con la info extraída
    state = db.Column(db.String(32), nullable=False, default='pending')  # Estados: pending, processing, complete
    feedback = db.Column(db.String(32), nullable=True)  # Sentimiento de la retroalimentación
    feedback_text = db.Column(db.Text, nullable=True)  # Texto de la retroalimentación
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
