import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import json
import paho.mqtt.client as paho
from gtts import gTTS
from googletrans import Translator

# --- Funciones de conexión MQTT ---
def on_publish(client, userdata, result):
    print("📡 Comando publicado exitosamente.")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(1)
    message_received = str(message.payload.decode("utf-8"))
    st.write(f"🏁 Respuesta recibida: {message_received}")

# --- Configuración del broker MQTT ---
broker = "broker.mqttdashboard.com"
port = 1883
client = paho.Client("Entrenador_Voz")
client.on_message = on_message

# --- Interfaz principal ---
st.set_page_config(page_title="Asistente Deportivo por Voz", page_icon="⚽", layout="centered")

st.title("🏋️‍♂️ ASISTENTE DEPORTIVO POR VOZ")
st.subheader("Controla tu entrenamiento usando solo tu voz 🎙️")

# Imagen representativa
try:
    image = Image.open("entrenamiento.jpg")
    st.image(image, width=250)
except:
    st.warning("No se encontró la imagen 'entrenamiento.jpg'")

st.write("Toca el botón y da una instrucción deportiva como:")
st.markdown("""
- “Inicia calentamiento”  
- “Mide mi tiempo de carrera”  
- “Reproduce música motivadora”  
- “Detén el cronómetro”  
""")

# --- Botón de control de voz ---
stt_button = Button(label="🎤 Activar micrófono", width=220)

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
    }
    recognition.start();
"""))

# --- Escucha eventos ---
result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# --- Procesamiento del comando ---
if result:
    if "GET_TEXT" in result:
        comando = result.get("GET_TEXT").strip()
        st.success(f"🎧 Comando detectado: {comando}")

        # Enviar comando por MQTT
        client.on_publish = on_publish
        client.connect(broker, port)
        message = json.dumps({"ComandoDeportivo": comando})
        client.publish("asistente_deportivo", message)

        # Generar respuesta hablada
        respuesta = f"Comando recibido: {comando}. ¡Vamos con toda!"
        tts = gTTS(respuesta, lang="es")
        os.makedirs("temp", exist_ok=True)
        audio_path = "temp/respuesta.mp3"
        tts.save(audio_path)
        st.audio(audio_path)

        # Traducción opcional
        traductor = Translator()
        traduccion = traductor.translate(comando, dest="en")
        st.write(f"🔤 Traducción (inglés): {traduccion.text}")

st.markdown("---")
st.caption("Desarrollado por: Tu Asistente Deportivo Virtual 🏃‍♀️")

    
    try:
        os.mkdir("temp")
    except:
        pass
