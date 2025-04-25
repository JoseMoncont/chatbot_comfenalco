import streamlit as st
import requests

# Configuración de la página
st.set_page_config(page_title="Chatbot Comfenalco", page_icon="🤖", layout="wide")
st.title("💬 Chatbot Semillero Comfenalco")
st.caption("🚀 Un chatbot para consultas sobre Crédito Social en Comfenalco")

# Cargar el archivo de texto
def cargar_contexto(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as archivo:
            return archivo.read()
    except FileNotFoundError:
        st.error(f"Archivo no encontrado: {ruta}")
        return ""

contexto = cargar_contexto('datos/credito_social.txt')

# Crear una sesión para almacenar mensajes previos
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role": "assistant", "content": "Hola, ¿en qué puedo ayudarte con respecto a Crédito Social?"}]

# Mostrar los mensajes previos como un chat
for msg in st.session_state['messages']:
    st.chat_message(msg["role"]).write(msg["content"])

# Entrada de la pregunta
prompt = st.chat_input("✍️ Escribe tu pregunta sobre Crédito Social:")

if prompt:
    if not contexto:
        st.info("No se ha cargado el contexto. Asegúrate de tener el archivo 'credito_social.txt' en la carpeta correcta.")
        st.stop()

    # Guardar la pregunta en los mensajes previos
    st.session_state['messages'].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Generando respuesta..."):
        # Preparar el prompt con contexto y la pregunta
        prompt_completo = f"{contexto}\n\nUsuario: {prompt}\nIA:"
        try:
            # Llamada al modelo Mistral vía API local de Ollama
            respuesta = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'mistral',
                    'prompt': prompt_completo,
                    'stream': False
                }
            ).json().get('response', 'No se recibió respuesta.')

            # Agregar respuesta del modelo a la conversación
            st.session_state['messages'].append({"role": "assistant", "content": respuesta})

        except requests.exceptions.RequestException as e:
            st.session_state['messages'].append({"role": "assistant", "content": f"❌ Error al conectar con el modelo: {e}"})

    # Mostrar la respuesta del modelo
    st.chat_message("assistant").write(respuesta)
