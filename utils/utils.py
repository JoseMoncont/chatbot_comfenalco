import os
import pickle
import numpy as np
import faiss
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

# Configuración de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_clean_text(url):
    """Obtiene el texto limpio de una URL, eliminando etiquetas HTML y contenido no deseado"""
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        return f"Error al obtener el texto de la URL: {e}"

def split_text(text, max_len=1000):
    """Divide un texto en fragmentos de un tamaño máximo especificado"""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

def generate_embeddings(fragments):
    """Genera embeddings para una lista de fragmentos de texto usando OpenAI API"""
    embeddings = []
    for frag in fragments:
        response = client.embeddings.create(
            input=frag,
            model="text-embedding-ada-002"
        )
        embeddings.append(response.data[0].embedding)
    return embeddings

def save_embeddings(name, fragments):
    """Guarda los embeddings en un índice FAISS y los fragmentos en un archivo pickle"""
    os.makedirs("data/embeddings", exist_ok=True)
    os.makedirs("data/fragments", exist_ok=True)

    embeddings = generate_embeddings(fragments)
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.stack(embeddings))
    faiss.write_index(index, f"data/embeddings/{name}.faiss")

    with open(f"data/fragments/{name}.pkl", "wb") as f:
        pickle.dump(fragments, f)
    
    return len(fragments)

def load_fragments(name):
    """Carga los fragmentos guardados de un archivo pickle"""
    path = f"data/fragments/{name}.pkl"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None

def load_index(name):
    """Carga un índice FAISS guardado"""
    index_path = f"data/embeddings/{name}.faiss"
    if os.path.exists(index_path):
        return faiss.read_index(index_path)
    return None

def search_fragments(query, name, k=5):
    """Busca los fragmentos más cercanos a una consulta en el índice especificado"""
    index = load_index(name)
    if index is None:
        return None

    # Generamos el embedding de la consulta
    response = client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    )
    query_embedding = np.array(response.data[0].embedding, dtype=np.float32)

    # Realizamos la búsqueda en el índice
    distances, indices = index.search(np.array([query_embedding]), k=k)
    fragments = load_fragments(name)
    
    if fragments is None:
        return None

    # Recuperar fragmentos y sus distancias (scores de similitud)
    results = []
    for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
        if idx < len(fragments):
            # Solo incluir fragmentos con una distancia razonable (menor distancia = mayor similitud)
            # Filtrar fragmentos demasiado distintos
            if dist < 1.5:  # Umbral ajustable según necesidades
                results.append({
                    "fragment": fragments[idx],
                    "distance": float(dist),
                    "position": i + 1
                })
    
    # Si no encontramos resultados con buena similitud, devolvemos None
    if not results:
        return None
        
    # Ordenar por distancia (menor primero)
    results.sort(key=lambda x: x["distance"])
    
    # Devolver solo los fragmentos
    return [r["fragment"] for r in results]

def get_indexed_urls():
    """Obtiene una lista de todas las URLs indexadas"""
    archivos = os.listdir("data/fragments") if os.path.exists("data/fragments") else []
    return [os.path.splitext(f)[0] for f in archivos]