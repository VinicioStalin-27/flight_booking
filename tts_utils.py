# tts_utils.py
import os
import tempfile
from gtts import gTTS
from pydub import AudioSegment

def synthesize_speech(text, lang='en'):
    """
    Genera un archivo de audio OGG a partir del texto usando gTTS.
    Devuelve la ruta del archivo OGG temporal.
    """
    # Generar el audio en MP3 con gTTS
    tts = gTTS(text, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
        tts.save(tmp_mp3.name)
        mp3_path = tmp_mp3.name

    # Convertir MP3 a OGG usando pydub (asegúrate de tener instalado ffmpeg)
    audio = AudioSegment.from_mp3(mp3_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_ogg:
        audio.export(tmp_ogg.name, format="ogg", codec="libopus")
        ogg_path = tmp_ogg.name

    os.remove(mp3_path)
    return ogg_path
