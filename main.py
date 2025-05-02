import streamlit as st
import chatbot
import admin

# Configuración de la página
st.set_page_config(
    page_title="Chatbot Semillero Comfenalco",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def app():
    """Aplicación principal que maneja el enrutamiento entre las diferentes secciones"""
    
    # Título en el sidebar
    st.sidebar.title("🤖 Chatbot Semillero")
    
    # Opciones de menú en Streamlit para elegir entre el chatbot y admin
    menu = ["Chatbot", "Administrador"]
    choice = st.sidebar.radio("Navegación", menu)

    # Mostrar la sección correspondiente según la selección
    if choice == "Chatbot":
        chatbot.main()
    elif choice == "Administrador":
        admin.main()
    
    # Pie de página
    st.sidebar.markdown("---")
    st.sidebar.info(
        """
        **Sobre esta aplicación**  
        Un chatbot inteligente que responde preguntas basándose en todas las 
        fuentes de conocimiento indexadas.
        """
    )

if __name__ == "__main__":
    app()