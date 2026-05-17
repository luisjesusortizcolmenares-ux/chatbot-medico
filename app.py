from flask import Flask, request
from google import genai
import db_helper

app = Flask(__name__)

# CONFIGURACIÓN DE GEMINI
# Pon tu clave real aquí adentro manteniendo las comillas
GEMINI_API_KEY = "AIzaSyAP_3-mwCYV8z7HEvtCGQJfwDbQCZ3AkdM"
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route("/webhook", methods=["POST"])
def webhook():
    datos = request.form
    telefono_usuario = datos.get("From")
    mensaje_recibido = datos.get("Body", "").strip()
    
    if not telefono_usuario or not mensaje_recibido:
        return "OK", 200

    # 1. Revisar si el paciente existe en la base de datos
    paciente = db_helper.obtener_paciente(telefono_usuario)
    
    # 2. Crear el contexto médico para la IA según el estado del paciente
    if paciente is not None:
        nombre = paciente[1]
        edad = paciente[2]
        condiciones = paciente[3]
        
        # Paciente registrado: Evaluamos su reporte diario con telemedicina preventiva
        prompt = f"""
        Eres un asistente médico experto en medicina preventiva y telemedicina.
        Estás hablando con tu paciente {nombre}, de {edad} años, quien padece de: {condiciones}.
        
        Él te acaba de reportar lo siguiente sobre su día: "{mensaje_recibido}".
        
        Analiza su mensaje textualmente. Si lo que comió, hizo o siente pone en riesgo su salud debido a sus condiciones preexistentes, genera una alerta médica preventiva sutil. Dale consejos amables y profesionales basados en sus hábitos. Sé breve, empático y directo (máximo 3 párrafos).
        """
    else:
        # Paciente nuevo: La IA interactúa para registrarlo de forma conversacional
        prompt = f"""
        Eres un asistente médico automatizado de una clínica preventiva.
        Un nuevo paciente te escribe por primera vez y te dice: "{mensaje_recibido}".
        
        Salúdalo cordialmente y pídele de forma amigable sus datos básicos para abrir su expediente: su Nombre completo, Edad y si sufre de alguna enfermedad crónica (como hipertensión, diabetes, etc.). Sé muy educado y breve.
        """

    try:
        # 3. Llamada oficial a Gemini (Usando el modelo gratuito gemini-2.5-flash)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        respuesta_bot = response.text
    except Exception as e:
        print(f"[ERROR GEMINI] {e}")
        respuesta_bot = "Lo siento, estoy experimentando un problema técnico temporal. Por favor, intenta de nuevo en unos minutos."

    # Imprimimos en la consola de Windows para monitorear en vivo
    print(f"\n[WHATSAPP] De: {telefono_usuario} -> {mensaje_recibido}")
    print(f"[GEMINI] -> {respuesta_bot}\n")
    
    # Formateamos la respuesta para Twilio/WhatsApp
    respuesta_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Message>{respuesta_bot}</Message>
    </Response>"""
    
    return respuesta_twiml, 200, {"Content-Type": "text/xml"}

if __name__ == "__main__":
    app.run(port=5000, debug=True)