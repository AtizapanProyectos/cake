# cuestionario_data.py

CUESTIONARIO_CLINICO = {
    "individual": {
        "titulo": "Terapia Individual (Para mí)",
        "preguntas": [
            {"id": "edad", "tipo": "numero", "pregunta": "¿Cuál es tu edad actual?"},
            {"id": "estado_emocional", "tipo": "multiple", "pregunta": "¿Qué te gustaría alcanzar o sentir en esta nueva etapa de tu vida?",
             "opciones": ["Mayor paz mental y tranquilidad", "Más energía y motivación en mi día a día", "Mejorar la forma en que manejo mis emociones", "Conectar más con otros y sentirme acompañado/a", "Profundizar en mi autoconocimiento", "Potenciar mi desarrollo personal y profesional", "Prefiero explorarlo junto a mi terapeuta"]},
            {"id": "situacion_detonante", "tipo": "multiple", "pregunta": "¿En qué áreas te gustaría enfocarte para estar mejor?",
             "opciones": ["Mi relación con mi cuerpo y mis hábitos saludables", "Mis vínculos con pareja, familia o amigos", "Sanar y crecer tras una experiencia reciente", "Explorar mi identidad con mayor libertad", "Alcanzar un mejor equilibrio en mi trabajo o escuela", "Otra área de crecimiento personal", "Lo platicaré en mi consulta"]},
            {"id": "experiencia_previa", "tipo": "single", "pregunta": "¿Has vivido la experiencia de ir a terapia antes?",
             "opciones": ["Es mi primera vez, estoy listo/a para iniciar", "Sí, tuve procesos en el pasado", "Sí, actualmente estoy en un proceso"]},
            
            # 👇 AQUÍ ESTÁ LA MAGIA CONDICIONAL 👇
            {"id": "detalles_terapia", "tipo": "texto", "pregunta": "¿Qué tipo de terapia recibiste y hace cuánto tiempo?", 
             "mostrar_si": {"id": "experiencia_previa", "valores": ["Sí, tuve procesos en el pasado", "Sí, actualmente estoy en un proceso"]}},
            
            {"id": "miedos_terapia", "tipo": "multiple", "pregunta": "¿Qué te ayudaría a sentirte más cómodo/a y en confianza durante tus sesiones?",
             "opciones": ["Saber exactamente cómo funciona el proceso", "Un ambiente donde pueda ir a mi propio ritmo", "Sentir mucha empatía y cero juicios", "Tener herramientas claras y prácticas desde el inicio", "Voy con total apertura para descubrirlo"]},
            {"id": "disposicion", "tipo": "single", "pregunta": "¿Cómo te sientes respecto a dar este gran paso hacia tu bienestar?",
             "opciones": ["¡Totalmente listo/a y con entusiasmo!", "Con un poco de nervios, pero es un excelente momento", "Aún lo estoy evaluando, pero quiero intentarlo"]},
            {"id": "preferencia_terapeuta", "tipo": "single", "pregunta": "¿Tienes alguna preferencia para tu terapeuta?",
             "opciones": ["Prefiero un terapeuta Hombre", "Prefiero una terapeuta Mujer", "Me es indiferente, confío en el profesional ideal para mí"]},
            {"id": "forma_expresion", "tipo": "single", "pregunta": "¿De qué forma te sientes más libre al expresarte?",
             "opciones": ["Hablando de forma directa y abierta", "Tomándome mi tiempo para ganar confianza", "Escribiendo o usando herramientas creativas"]}
        ]
    },
    "pareja": {
        "titulo": "Terapia de Pareja",
        "preguntas": [
            {"id": "edad", "tipo": "numero", "pregunta": "¿Cuál es tu edad?"},
            {"id": "expectativas", "tipo": "multiple", "pregunta": "¿Qué metas positivas esperan lograr con este proceso?",
             "opciones": ["Mejorar nuestra empatía y comunicación", "Recuperar el compromiso y la confianza mutua", "Tener un espacio neutral y seguro para crecer", "Obtener herramientas prácticas para nuestra relación", "Mejorar nuestra conexión íntima y afectiva", "Aún lo estamos descubriendo"]},
            {"id": "experiencia_previa", "tipo": "single", "pregunta": "¿Han asistido a terapia de pareja anteriormente?",
             "opciones": ["No, es nuestra primera vez", "Sí, en el pasado", "Sí, estamos en terapia actualmente"]},
            
            # 👇 AQUÍ ESTÁ LA MAGIA CONDICIONAL 👇
            {"id": "detalles_terapia_pareja", "tipo": "texto", "pregunta": "¿Qué tipo de terapia recibieron y hace cuánto tiempo?",
             "mostrar_si": {"id": "experiencia_previa", "valores": ["Sí, en el pasado", "Sí, estamos en terapia actualmente"]}},
            
            {"id": "disposicion", "tipo": "single", "pregunta": "¿Ambos tienen la disposición para iniciar este camino de mejora?",
             "opciones": ["Sí, ambos estamos listos y comprometidos", "Sí, aunque uno de los dos tiene algunas dudas naturales", "Aún lo estamos platicando"]}
        ]
    },
    "tercero": {
        "titulo": "Para un Familiar o Amigo",
        "preguntas": [
            {"id": "edad_tuya", "tipo": "numero", "pregunta": "¿Cuál es tu edad?"},
            {"id": "edad_tercero", "tipo": "numero", "pregunta": "¿Qué edad tiene la persona para la que buscas apoyo?"},
            {"id": "motivo_tercero", "tipo": "multiple", "pregunta": "¿Qué te motiva a buscar este espacio de bienestar para él/ella?",
             "opciones": ["Quiero que encuentre más paz y tranquilidad", "Deseo apoyarlo/a a desarrollar mejores hábitos", "Me gustaría que mejore su entorno escolar, laboral o social", "Ayudarlo/a a transitar una etapa de cambio con acompañamiento", "Que tenga un espacio 100% seguro para hablar de sus emociones", "Que un profesional lo/a guíe en su desarrollo personal"]},
            {"id": "disposicion_tercero", "tipo": "single", "pregunta": "¿Esta persona está enterada y tiene disposición para iniciar este camino?",
             "opciones": ["Sí, está totalmente de acuerdo", "Sabe del tema y está dispuesto/a a intentarlo", "Aún no se lo he planteado, quiero informarme primero"]}
        ]
    }
}