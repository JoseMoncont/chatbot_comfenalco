import streamlit as st
import os
from utils.utils import get_clean_text, split_text, save_embeddings, get_indexed_urls, load_fragments

def main():
    """Interfaz de administración para procesar y indexar URLs"""
    st.title("Administración de Fuentes de Conocimiento")
    
    # Navegación de pestañas para las diferentes funciones de administración
    tab1, tab2, tab3 = st.tabs(["Agregar contenido web", "Texto manual", "Administrar fuentes"])
    
    with tab1:
        st.subheader("Agregar nuevo contenido desde una URL")

        # Entrada de URL por parte del usuario
        url = st.text_input("Ingresa la URL para procesar:")
        overlap = st.slider("Superposición entre fragmentos (%)", 0, 50, 20, 
                         help="Mayor superposición puede mejorar la búsqueda pero genera más fragmentos")
        max_length = st.slider("Longitud máxima de fragmentos", 500, 2000, 1000,
                            help="Fragmentos más cortos son más precisos, fragmentos más largos contienen más contexto")
        
        col1, col2 = st.columns([3, 1])
        process_button = col2.button("Procesar URL")

        if url and process_button:
            with st.spinner("Procesando URL..."):
                # Obtener el texto limpio de la URL
                clean_text = get_clean_text(url)
                if "Error" in clean_text:
                    st.error(clean_text)
                else:
                    # Mostrar estadísticas del texto
                    st.write(f"Texto extraído: {len(clean_text)} caracteres")
                    
                    # Dividir el texto en fragmentos con superposición
                    overlap_chars = int(max_length * overlap / 100)
                    step_size = max_length - overlap_chars
                    fragments = []
                    
                    for i in range(0, len(clean_text), step_size):
                        fragment = clean_text[i:i + max_length]
                        if len(fragment) >= max_length / 2:  # Solo agregar si tiene un tamaño razonable
                            fragments.append(fragment)
                    
                    st.write(f"Fragmentos generados: {len(fragments)}")
                    
                    # Vista previa de fragmentos
                    with st.expander("Vista previa de fragmentos"):
                        preview_count = min(3, len(fragments))
                        for i in range(preview_count):
                            st.text_area(f"Fragmento {i+1}/{len(fragments)}", fragments[i], height=100)
                    
                    # Nombre de los embeddings (usar el nombre de la URL formateado)
                    name = url.split("//")[-1].replace("/", "_").replace(".", "_")
                    name_input = st.text_input("Nombre para indexar (identificador):", value=name)

                    if st.button("Guardar embeddings"):
                        with st.spinner("Generando embeddings... esto puede tomar tiempo"):
                            fragments_count = save_embeddings(name_input, fragments)
                            st.success(f"Embeddings guardados con éxito para '{name_input}' ({fragments_count} fragmentos)")
    
    with tab2:
        st.subheader("Agregar contenido manualmente")
        
        # Campo para texto manual
        manual_text = st.text_area("Ingresa el texto que deseas indexar:", height=300)
        manual_name = st.text_input("Nombre para esta fuente de conocimiento:")
        
        col1, col2 = st.columns([3, 1])
        max_length_manual = col1.slider("Longitud máxima de fragmentos (manual)", 500, 2000, 1000)
        process_manual = col2.button("Procesar texto")
        
        if manual_text and manual_name and process_manual:
            with st.spinner("Procesando texto..."):
                # Dividir el texto en fragmentos
                fragments = split_text(manual_text, max_len=max_length_manual)
                st.write(f"Fragmentos generados: {len(fragments)}")
                
                # Vista previa de fragmentos
                with st.expander("Vista previa de fragmentos"):
                    preview_count = min(3, len(fragments))
                    for i in range(preview_count):
                        st.text_area(f"Fragmento {i+1}/{len(fragments)}", fragments[i], height=100)
                
                if st.button("Guardar contenido manual"):
                    with st.spinner("Generando embeddings..."):
                        fragments_count = save_embeddings(manual_name, fragments)
                        st.success(f"Contenido guardado con éxito como '{manual_name}' ({fragments_count} fragmentos)")
    
    with tab3:
        st.subheader("Fuentes de conocimiento indexadas")
        
        # Mostrar las URLs indexadas
        indexed_urls = get_indexed_urls()
        
        if indexed_urls:
            st.write("Selecciona una fuente para ver detalles o eliminarla:")
            for url in indexed_urls:
                col1, col2 = st.columns([5, 1])
                col1.write(f"📄 {url}")
                
                # Botón para eliminar esta fuente
                if col2.button("Eliminar", key=f"del_{url}"):
                    try:
                        # Eliminar los archivos asociados
                        if os.path.exists(f"data/fragments/{url}.pkl"):
                            os.remove(f"data/fragments/{url}.pkl")
                        if os.path.exists(f"data/embeddings/{url}.faiss"):
                            os.remove(f"data/embeddings/{url}.faiss")
                        st.success(f"Fuente '{url}' eliminada correctamente")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar la fuente: {e}")
                
                # Mostrar detalles de esta fuente
                with st.expander(f"Ver fragmentos de {url}"):
                    fragments = load_fragments(url)
                    if fragments:
                        st.write(f"Total de fragmentos: {len(fragments)}")
                        for i, frag in enumerate(fragments[:5]):  # Mostrar solo los primeros 5
                            st.text_area(f"Fragmento {i+1}", frag, height=100)
                        if len(fragments) > 5:
                            st.write(f"... y {len(fragments) - 5} fragmentos más")
        else:
            st.info("No hay fuentes indexadas. Añade alguna usando las otras pestañas.")

if __name__ == "__main__":
    main()