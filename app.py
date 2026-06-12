from flask import Flask, request
from google import genai
import db_helper
import os

app = Flask(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route("/webhook", methods=["POST"])
def webhook():
    datos = request.form
    telefono_usuario = datos.get("From")
    mensaje_recibido = datos.get("Body", "").strip()
    
    if not telefono_usuario or not mensaje_recibido:
        return "OK", 200

    # 1. Buscamos al paciente directamente
    paciente = db_helper.obtener_paciente(telefono_usuario)
    
    # 2. LÓGICA DE REGISTRO
    # Si paciente es None, significa que es la primera vez que escribe
    if paciente is None:
        if "nombre" in mensaje_recibido.lower() and "edad" in mensaje_recibido.lower():
            # Extraemos los datos usando Gemini
            prompt_extraer = f"Extrae: Nombre, Edad, Condiciones del mensaje: '{mensaje_recibido}'. Formato: Nombre|Edad|Condiciones"
            res_ia = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_extraer).text
            try:
                nombre, edad, cond = res_ia.split('|')
                db_helper.registrar_paciente(telefono_usuario, nombre.strip(), int(edad), cond.strip())
                respuesta_bot = f"¡Muchas gracias, {nombre.strip()}! Expediente registrado. ¿Cómo te sientes hoy?"
            except:
                respuesta_bot = "No logré registrarte. Por favor escribe: Mi nombre es [NOMBRE], tengo [EDAD] años y sufro de [CONDICIONES]."
        else:
            respuesta_bot = "¡Hola! Para abrir tu expediente médico, por favor dime: Mi nombre es [NOMBRE], tengo [EDAD] años y sufro de [CONDICIONES]."
    
    # 3. LÓGICA DE PACIENTE REGISTRADO
    else:
        nombre, edad, condiciones = paciente[1], paciente[2], paciente[3]
        prompt = f"Eres un médico experto. Estás hablando con {nombre}, de {edad} años, quien padece de: {condiciones}. Mensaje recibido: '{mensaje_recibido}'. Analiza su estado y da consejos breves y empáticos."
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        respuesta_bot = response.text

    return f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{respuesta_bot}</Message></Response>", 200, {"Content-Type": "text/xml"}

if __name__ == "__main__":
    app.run(port=5000)
