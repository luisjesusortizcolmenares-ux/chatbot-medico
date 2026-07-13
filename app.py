from flask import Flask, request
from google import genai
from google.genai import errors # Importamos los errores de Google
import db_helper
import os

app = Flask(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Función auxiliar para llamar a Gemini de forma segura
def obtener_respuesta_gemini(prompt):
    try:
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text
    except errors.ClientError as e:
        # Detectamos si es un error 429 (Resource Exhausted)
        if e.code == 429:
            return "Lo siento, ahora mismo tengo mucha demanda. Por favor, intenta escribirme en unos minutos."
        return f"Ocurrió un error técnico: {e.message}"
    except Exception as e:
        return "Hubo un error inesperado al procesar tu solicitud."

@app.route("/webhook", methods=["POST"])
def webhook():
    datos = request.form
    telefono_usuario = datos.get("From")
    mensaje_recibido = datos.get("Body", "").strip()
    
    if not telefono_usuario or not mensaje_recibido:
        return "OK", 200

    paciente = db_helper.obtener_paciente(telefono_usuario)
    
    if paciente is None:
        if "nombre" in mensaje_recibido.lower() and "edad" in mensaje_recibido.lower():
            prompt_extraer = f"Extrae: Nombre, Edad, Condiciones del mensaje: '{mensaje_recibido}'. Formato: Nombre|Edad|Condiciones"
            res_ia = obtener_respuesta_gemini(prompt_extraer)
            
            # Verificamos si la respuesta de IA contiene el error
            if "Lo siento" in res_ia or "error" in res_ia.lower():
                respuesta_bot = res_ia
            else:
                try:
                    nombre, edad, cond = res_ia.split('|')
                    db_helper.registrar_paciente(telefono_usuario, nombre.strip(), int(edad), cond.strip())
                    respuesta_bot = f"¡Muchas gracias, {nombre.strip()}! Expediente registrado. ¿Cómo te sientes hoy?"
                except:
                    respuesta_bot = "No logré registrarte. Por favor escribe: Mi nombre es [NOMBRE], tengo [EDAD] años y sufro de [CONDICIONES]."
        else:
            respuesta_bot = "¡Hola! Para abrir tu expediente médico, por favor dime: Mi nombre es [NOMBRE], tengo [EDAD] años y sufro de [CONDICIONES]."
    
    else:
        nombre, edad, condiciones = paciente[1], paciente[2], paciente[3]
        prompt = f"Eres un médico experto. Estás hablando con {nombre}, de {edad} años, quien padece de: {condiciones}. Mensaje recibido: '{mensaje_recibido}'. Analiza su estado y da consejos breves y empáticos."
        respuesta_bot = obtener_respuesta_gemini(prompt)

    return f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{respuesta_bot}</Message></Response>", 200, {"Content-Type": "text/xml"}

if __name__ == "__main__":
    app.run(port=5000)
