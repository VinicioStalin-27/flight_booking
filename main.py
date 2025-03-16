
import json
import os
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS

from config import SQLALCHEMY_DATABASE_URI
from db_model import db, FlightOrder
from entity_extractor import extract_flight_info, translate_text, translate_text_es, validate_info
from telegram_utils import send_message, send_voice
from speech_utils import transcribe_voice
from tts_utils import synthesize_speech
from langdetect import detect

# Instalar la librería nltk y descargar el lexicon de VADER
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment import SentimentIntensityAnalyzer


# Inicializar el analizador de sentimiento de NLTK
sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    """
    Analiza el sentimiento del texto y devuelve 'positive', 'negative' o 'neutral'
    utilizando NLTK SentimentIntensityAnalyzer.
    """
    scores = sia.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        return "positive"
    elif compound <= -0.05:
        return "negative"
    else:
        return "neutral"

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Diccionario que asocia cada campo faltante a una pregunta
question_mapping = {
    "from": "Please provide your departure city:",
    "to": "Please provide your destination city:",
    "departure_date": "When will you depart?",
    "return_date": "When will you return?",
    # "stay_duration": "Please provide the duration of your stay in days:",
    "num_people": "How many passengers/tickets do you need?",
    "airline": "Which airline do you prefer?"
}

@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        lang = 'en'
        data = request.json
        uid = str(data["message"]["from"]["id"])
        text = data["message"].get("text", "")

        # Si se recibe el comando /start, enviar mensaje de bienvenida y detener procesamiento adicional
        if text.strip() == "/start":
            welcome_text = "Welcome! Please provide your flight details."
            send_message(uid, welcome_text)
            return jsonify({"status": "ok"})
        # else:
        #     return jsonify({"status": "ok"})

        # Detectar el idioma del texto
        if text:
            try:
                lang = detect(text)
            except:
                lang = 'en'

        # Si se recibe un mensaje de voz, transcribirlo y usar la transcripción como texto
        if "voice" in data["message"]:
            file_id = data["message"]["voice"]["file_id"]
            try:
                text, lang = transcribe_voice(file_id)
            except Exception as e:
                send_message(uid, f"Error transcribing voice message: {str(e)}")
                return jsonify({"status": "error"})

        # Traducir el texto para unificar el procesamiento
        text = translate_text(text)

        # Buscar un pedido pendiente (estado 'pending' o 'processing') para este uid
        order = FlightOrder.query.filter(FlightOrder.uid == uid,
                                         FlightOrder.state.in_(["pending", "processing", "feedback"])).first()

        if not order:
            order = FlightOrder(uid=uid, flight_info=json.dumps({f: None for f in ['from', 'to', 'departure_date', 'return_date', 'stay_duration', 'num_people', 'airline']}), state='pending')
            db.session.add(order)
            db.session.commit()

        # Si el pedido está en estado 'feedback', guardar la calificación y enviar un mensaje de agradecimiento
        if order.state == "feedback":
            sentiment = analyze_sentiment(text)
            order.feedback = sentiment
            order.feedback_text = text
            order.state = "complete"
            db.session.commit()
            if order.feedback == "positive":
                send_text = "Thank you for your positive feedback!"
            elif order.feedback == "negative":
                send_text = "We're sorry to hear that. We'll work to improve our service."
            else:
                send_text = "Thank you for your feedback!"
            if lang == 'es':
                send_text = translate_text_es(send_text)
            send_message(uid, send_text)
            return jsonify({"status": "ok"})

        info = json.loads(order.flight_info)
        pending_fields = [k for k, v in info.items() if v is None]
        new_info = extract_flight_info(text, pending_fields, info)

        for key in pending_fields:
            if new_info.get(key) is not None:
                info[key] = new_info[key]

        info = validate_info(info)
        order.flight_info = json.dumps(info)
        db.session.commit()

        # Revisar campos faltantes en el pedido
        info = json.loads(order.flight_info)
        pending_fields = [k for k, v in info.items() if v is None]

        if pending_fields:
            response_text = question_mapping.get(pending_fields[0], f"Please provide {pending_fields[0]}")
            order.state = "processing"
        else:
            response_text = f"Your flight for {info['num_people']} passengers from {info['from']} to {info['to']} on {info['departure_date']} during {info['stay_duration']} days has been booked. Please follow the link to complete the payment. https://www.example.com/checkout"
            # response_text = f"You booked a flight from {info['from']} to {info['to']} on {info['departure_date']}."
            order.state = "feedback"

        db.session.commit()

        if lang == 'es':
            response_text = translate_text_es(response_text)

        if "voice" in data["message"]:
            # Generar un archivo de audio con la respuesta
            audio_path = synthesize_speech(response_text, lang)
            # Enviar el archivo de audio a Telegram mediante /sendVoice
            send_voice(uid, audio_path)
            os.remove(audio_path)

        else:
            # Enviar la respuesta a Telegram mediante /sendMessage
            send_message(uid, response_text)

        if order.state == "feedback":
            if "voice" in data["message"]:
                send_message(uid, response_text)
            feedback_text = "Please rate your experience with our service."
            if lang == 'es':
                feedback_text = translate_text_es(feedback_text)
            send_message(uid, feedback_text)

        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_flask():
    app.run(host="0.0.0.0", port=5555)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    thread = Thread(target=run_flask)
    thread.start()
