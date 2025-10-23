import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import paho.mqtt.client as paho
import json
from gtts import gTTS
from googletrans import Translator

# --- Funciones MQTT ---
def on_publish(client, userdata, result):
    print("El dato ha sido publicado\n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

# --- Configuración del broker MQTT ---
broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("GIT-HUBC")
client1.on_message = on_message

# --- Interfaz principal ---
st.title("🏎️ Control de Voz - Velocidad de Auto")
st.subheader("Habla para controlar la velocidad del vehículo")

try:
    image = Image.open("auto.jpg")
    st.image(image, width=300)
except:
    st.warning("⚠️ No se encontró la imagen 'auto.jpg'")

st.write("🎙️ Toca el botón y habla:")

# --- Botón de voz ---
stt_button = Button(label="🎤 Iniciar Reconocimiento", width=250)
stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    };
    recognition.start();
"""))

# --- Captura de voz ---
result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# --- Procesamiento de voz y envío MQTT ---
if result and "GET_TEXT" in result:
    comando = result.get("GET_TEXT").strip().lower()
    st.success(f"🎧 Comando detectado: {comando}")

    client1.on_publish = on_publish
    client1.connect(broker, port)

    message = json.dumps({"comando": comando})
    ret = client1.publish("voz_auto_david", message)

    # Traducción y voz
    translator = Translator()
    respuesta = translator.translate(f"Comando recibido: {comando}", dest="es").text
    tts = gTTS(respuesta, lang="es")
    tts.save("temp_audio.mp3")

    audio_file = open("temp_audio.mp3", "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format="audio/mp3")

# --- Crear carpeta temporal si no existe ---
if not os.path.exists("temp"):
    os.mkdir("temp")
