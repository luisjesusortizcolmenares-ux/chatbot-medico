from flask import Flask, request
from google import genai
from google.genai import errors
import db_helper
import os

# 1. Definición de la aplicación (ESTO DEBE IR PRIMERO)
app = Flask(__name__)

# 2. Configuración
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Función auxiliar para llamar a Gemini
def obtener_respuesta_gemini(prompt):
    try:
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text
    except errors.ClientError as e:
        if e.code == 429:
            return "Lo siento, ahora mismo tengo mucha demanda. Intenta en unos minutos."
        return f"Ocurrió un error técnico: {e.message}"
    except Exception as e:
        return "Hubo un error inesperado al procesar tu solicitud."

# 3. RUTAS (Aquí abajo, después de definir app)
@app.route("/webhook", methods=["POST"])
def webhook():
    datos = request.form
    telefono_usuario = datos.get("From")
    mensaje_recibido = datos.get("Body", "").strip()
    
    if not telefono_usuario or not mensaje_recibido:
        return "OK", 200

    paciente = db_helper.obtener_paciente(telefono_usuario)
    
    if paciente is None:
        prompt_inicial = f"""
        Eres un asistente médico inteligente. El usuario envió: '{mensaje_recibido}'.
        Si el usuario quiere registrarse, busca su nombre, edad y condiciones médicas. 
        Si los encuentras, responde exactamente con este formato: REGISTRO|Nombre|Edad|Condiciones.
        Si no quiere registrarse o hace una pregunta médica, responde normalmente de forma empática.
        """
        res_ia = obtener_respuesta_gemini(prompt_inicial)
        
        if res_ia.startswith("REGISTRO|"):
            try:
                partes = res_ia.split('|')
                db_helper.registrar_paciente(telefono_usuario, partes[1].strip(), int(partes[2]), partes[3].strip())
                respuesta_bot = f"¡Bienvenido {partes[1].strip()}! Ya tienes tu expediente. ¿En qué más puedo ayudarte hoy?"
            except:
                respuesta_bot = "No pude registrarte. Por favor, escribe: Mi nombre es [NOMBRE], tengo [EDAD] años y sufro de [CONDICIONES]."
        else:
            respuesta_bot = res_ia
    else:
        nombre, edad, condiciones = paciente[1], paciente[2], paciente[3]
        prompt = f"""
        Eres un médico experto conversando con {nombre}, de {edad} años, quien padece de: {condiciones}.
        El usuario pregunta: '{mensaje_recibido}'.
        Responde de forma clara, breve, empática y profesional.
        """
        respuesta_bot = obtener_respuesta_gemini(prompt)

    return f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{respuesta_bot}</Message></Response>", 200, {"Content-Type": "text/xml"}

# 4. PUNTO DE ENTRADA (Vital para Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
