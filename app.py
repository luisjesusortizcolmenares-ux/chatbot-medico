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
        # Usamos gemini-1.5-flash para máxima estabilidad
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
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
        # Prompt inicial de registro mejorado para ser cálido y empático
        prompt_inicial = f"""
        Eres BioVision, un asistente médico virtual sumamente cálido, empático y muy humano.
        Un usuario nuevo te acaba de enviar este mensaje: '{mensaje_recibido}'.

        Tu objetivo es registrar al paciente. Actúa según estas dos reglas:
        1. Si en su mensaje ya te está dando su nombre, edad y condiciones médicas, no saludes, responde ÚNICAMENTE con este formato exacto: REGISTRO|Nombre|Edad|Condiciones. (Ejemplo: REGISTRO|Carlos|45|Hipertensión).
        2. Si el mensaje es un simple saludo, una pregunta general, o faltan datos para el registro, dale una bienvenida hermosa y muy amigable. Preséntate como BioVision, dile que estás feliz de atenderle hoy, y explícale que para darle una mejor atención necesitas abrir su expediente. Pregúntale con mucho tacto y amabilidad cuál es su nombre, su edad y si padece de alguna condición médica. Usa emojis para que se sienta cercano.
        """
        res_ia = obtener_respuesta_gemini(prompt_inicial)
        
        if res_ia.startswith("REGISTRO|"):
            try:
                partes = res_ia.split('|')
                db_helper.registrar_paciente(telefono_usuario, partes[1].strip(), int(partes[2]), partes[3].strip())
                respuesta_bot = f"¡Listo, {partes[1].strip()}! 📝 Ya he creado tu expediente de forma segura. Cuéntame, ¿en qué te puedo ayudar el día de hoy?"
            except:
                respuesta_bot = "¡Ups! Tuvimos un pequeño inconveniente guardando tus datos. ¿Podrías repetirme tu nombre, tu edad y si tienes alguna condición médica, por favor? 🙏"
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
