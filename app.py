@app.route("/webhook", methods=["POST"])
def webhook():
    datos = request.form
    telefono_usuario = datos.get("From")
    mensaje_recibido = datos.get("Body", "").strip()
    
    if not telefono_usuario or not mensaje_recibido:
        return "OK", 200

    paciente = db_helper.obtener_paciente(telefono_usuario)
    
    # 1. SI NO ESTÁ REGISTRADO: Intentamos registrarlo o responder su duda
    if paciente is None:
        # Le enviamos el mensaje a Gemini para ver si quiere registrarse o preguntar algo
        prompt_inicial = f"""
        Eres un asistente médico inteligente. El usuario envió: '{mensaje_recibido}'.
        Si el usuario quiere registrarse, busca su nombre, edad y condiciones médicas. 
        Si los encuentras, responde exactamente con este formato: REGISTRO|Nombre|Edad|Condiciones.
        Si no quiere registrarse o hace una pregunta médica, responde normalmente de forma empática.
        """
        res_ia = obtener_respuesta_gemini(prompt_inicial)
        
        if res_ia.startswith("REGISTRO|"):
            partes = res_ia.split('|')
            db_helper.registrar_paciente(telefono_usuario, partes[1], int(partes[2]), partes[3])
            respuesta_bot = f"¡Bienvenido {partes[1]}! Ya tienes tu expediente. ¿En qué más puedo ayudarte hoy?"
        else:
            respuesta_bot = res_ia

    # 2. SI YA ESTÁ REGISTRADO: Gemini responde todo lo que pregunte
    else:
        nombre, edad, condiciones = paciente[1], paciente[2], paciente[3]
        prompt = f"""
        Eres un médico experto conversando con {nombre}, de {edad} años, quien padece de: {condiciones}.
        El usuario pregunta: '{mensaje_recibido}'.
        Responde de forma clara, breve, empática y profesional.
        """
        respuesta_bot = obtener_respuesta_gemini(prompt)

    return f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{respuesta_bot}</Message></Response>", 200, {"Content-Type": "text/xml"}
