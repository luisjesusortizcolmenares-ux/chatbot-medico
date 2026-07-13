import os
from flask import Flask, request
from google import genai
import db_helper

# Inicialización de la aplicación
app = Flask(__name__)

# Configuración del cliente Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Función para obtener respuesta de Gemini
def obtener_respuesta_gemini(prompt):
    try:
        # Usamos el modelo 2.0-flash que es el que soporta la nueva librería genai
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        # Esto imprimirá el error real en los logs de Render si algo más falla
        print(f"--- ERROR REAL DE API: {str(e)} ---")
        return f"Error técnico: {str(e)}"

# Ruta del Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    datos = request.form
    telefono_usuario = datos.get("From")
    mensaje_recibido = datos.get("Body", "").strip()
    
    if not telefono_usuario or not mensaje_recibido:
        return "OK", 200

    paciente = db_helper.obtener_paciente(telefono_usuario)
    
    if paciente is None:
        # Prompt inicial de registro
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
        # Interacción para paciente registrado
        nombre, edad, condiciones = paciente[1], paciente[2], paciente[3]
        prompt = f"""
        Eres un médico experto conversando con {nombre}, de {edad} años, quien padece de: {condiciones}.
        El usuario pregunta: '{mensaje_recibido}'.
        Responde de forma clara, breve, empática y profesional.
        """
        respuesta_bot = obtener_respuesta_gemini(prompt)

    return f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{respuesta_bot}</Message></Response>", 200, {"Content-Type": "text/xml"}

# Punto de entrada para Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
