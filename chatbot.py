import streamlit as st
from utils.utils import search_fragments, get_indexed_urls, client

def search_all_sources(query, temperature=0.7):
    """
    Genera una respuesta basada en fragmentos relevantes de todas las fuentes indexadas.
    
    Args:
        query: La pregunta o consulta del usuario
        temperature: Controla la aleatoriedad de la respuesta
        
    Returns:
        La respuesta generada o un mensaje de error
    """
    # Obtener todas las fuentes indexadas
    sources = get_indexed_urls()
    
    if not sources:
        return "No hay fuentes de conocimiento indexadas. Por favor, añade algunas en la sección Administrador."
    
    # Buscar fragmentos en todas las fuentes
    all_fragments = []
    keywords = extract_keywords(query)
    expanded_query = f"{query} {' '.join(keywords)}"
    
    # Buscar en cada fuente
    for source in sources:
        # Intentar con consulta expandida
        fragments = search_fragments(expanded_query, source, k=3)  # Reducido a 3 por fuente para no sobrecargar
        
        if fragments:
            # Añadir información sobre la fuente a cada fragmento
            all_fragments.extend([f"[Fuente: {source}] {fragment}" for fragment in fragments])
    
    # Si no hay suficientes fragmentos, intentar con la consulta original
    if len(all_fragments) < 3:
        for source in sources:
            fragments = search_fragments(query, source, k=4)
            if fragments:
                all_fragments.extend([f"[Fuente: {source}] {fragment}" for fragment in fragments])
    
    # Eliminar posibles duplicados y limitar a los mejores 8 fragmentos para no sobrecargar el contexto
    unique_fragments = list(dict.fromkeys(all_fragments))[:8]
    
    if not unique_fragments:
        return "Lo siento, no pude encontrar información relevante sobre eso en ninguna de las fuentes de conocimiento. Intenta reformular tu pregunta."
    
    # Formateamos el contexto para la consulta
    context = "\n\n".join(unique_fragments)
    
    try:
        # Utilizamos la API de chat para gpt-3.5-turbo
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Eres un asistente útil especializado en responder preguntas basándote en la información proporcionada.
                
Tu tarea es:
1. Analizar cuidadosamente el contexto proporcionado
2. Responder con información precisa que se encuentre en el contexto
3. Si la información no está claramente en el contexto, busca pistas o datos relacionados que puedan ayudar
4. Evita respuestas genéricas como "La información no menciona específicamente..."
5. Si realmente no hay información relacionada con la pregunta, sugiere reformularla o proporciona información relacionada que sí esté disponible

Debes ser informativo y útil, extrayendo todo el valor posible del contexto."""},
                {"role": "user", "content": f"Basándote en esta información:\n\n{context}\n\nResponde a esta pregunta: {query}"}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar respuesta: {str(e)}"

def extract_keywords(query):
    """
    Extrae palabras clave significativas de la consulta para mejorar la búsqueda
    
    Args:
        query (str): La consulta del usuario
        
    Returns:
        list: Lista de palabras clave únicas extraídas
    """
    # Lista de palabras comunes para ignorar (stopwords)
    stopwords = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "a", "ante", "bajo", 
        "con", "de", "desde", "en", "entre", "hacia", "hasta", "para", "por", "según", "sin", 
        "sobre", "tras", "que", "cual", "quien", "cuyo", "como", "cuando", "donde", "cuanto",
        "tienen", "tiene", "hay", "son", "es", "está", "están", "ser", "estar", "haber",
        "me", "te", "se", "nos", "os", "mi", "tu", "su", "nuestro", "vuestro", "mío", "tuyo", "suyo"
    }
    
    # Eliminar signos de puntuación y convertir a minúsculas
    clean_query = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in query.lower())
    
    # Dividir en palabras y filtrar stopwords usando un conjunto para mejor rendimiento
    words = [word for word in clean_query.split() if word not in stopwords and len(word) > 2]
    
    # Devolver palabras clave únicas (sin duplicados)
    return list(set(words))

def main():
    """Interfaz principal del chatbot"""
    st.title("🗨️ Chatbot Semillero Comfenalco")
    
    # Recuperar historial de chat de la sesión
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar mensajes del historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Sidebar para configuración
    with st.sidebar:
        st.subheader("Configuración")
        
        # Mostrar las fuentes disponibles (informativo)
        indexed_sources = get_indexed_urls()
        if not indexed_sources:
            st.warning("No hay fuentes indexadas. Ve a la sección Admin para agregar algunas.")
        else:
            st.success(f"Usando {len(indexed_sources)} fuentes como base de conocimiento:")
            for source in indexed_sources:
                st.write(f"📄 {source}")
            
        # Configuraciones avanzadas
        with st.expander("Configuración avanzada"):
            temperature = st.slider("Temperatura", 0.0, 1.0, 0.7, 0.1, 
                                help="Valores más altos hacen las respuestas más creativas, valores más bajos las hacen más precisas")
            
            show_context = st.checkbox("Mostrar contexto utilizado", value=False,
                                     help="Muestra los fragmentos que el sistema utiliza para generar la respuesta")
            
            debug_mode = st.checkbox("Modo de depuración", value=False,
                                   help="Muestra información adicional sobre la búsqueda")
        
        # Botón para limpiar historial de chat
        if st.button("Limpiar conversación"):
            st.session_state.messages = []
            st.experimental_rerun()
    
    # Entrada de usuario
    if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
        # Añadir mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                # Mostrar información de debugging si está activado
                if debug_mode:
                    keywords = extract_keywords(prompt)
                    expanded_query = f"{prompt} {' '.join(keywords)}"
                    st.write("⚙️ **Modo debug activado**")
                    st.write(f"Palabras clave extraídas: {', '.join(keywords)}")
                    st.write(f"Consulta expandida: '{expanded_query}'")
                    
                    # Información sobre las fuentes consultadas
                    sources = get_indexed_urls()
                    if sources:
                        st.write(f"Buscando en {len(sources)} fuentes: {', '.join(sources)}")
                    
                # Generar respuesta considerando todas las fuentes
                response = search_all_sources(prompt, temperature)
                
                # Mostrar contexto utilizado si está activado
                if show_context:
                    sources = get_indexed_urls()
                    all_fragments = []
                    
                    for source in sources:
                        fragments = search_fragments(prompt, source, k=2)
                        if fragments:
                            for fragment in fragments:
                                all_fragments.append((source, fragment))
                    
                    if all_fragments:
                        with st.expander("Contexto utilizado"):
                            for i, (source, frag) in enumerate(all_fragments):
                                st.text_area(f"Fragmento {i+1} (Fuente: {source})", frag, height=100)
            
            st.markdown(response)
        
        # Añadir respuesta al historial
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()