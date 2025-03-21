# telegram_utils.py
import requests
from config import TELEGRAM_BOT_TOKEN

def send_message(chat_id, text):
    """Envía un mensaje a Telegram usando la API /sendMessage."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return response.json()

def send_voice(chat_id, audio_file_path):
    """Envía un mensaje de voz a Telegram usando la API /sendVoice."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice"
    with open(audio_file_path, 'rb') as audio_file:
        files = {'voice': audio_file}
        data = {"chat_id": chat_id}
        response = requests.post(url, data=data, files=files)
    return response.json()

def get_file_info(file_id):
    """Obtiene la información del archivo (file_path) mediante la API getFile de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"
    payload = {"file_id": file_id}
    response = requests.get(url, params=payload)
    return response.json()

def download_file(file_path):
    """Descarga el archivo de Telegram dado su file_path."""
    url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    r = requests.get(url)
    return r.content
