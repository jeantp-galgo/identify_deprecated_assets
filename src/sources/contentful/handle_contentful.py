import contentful_management # Módulo para manejar la API de Contentful
import os # Módulo para manejar variables de entorno
from dotenv import load_dotenv # Módulo para cargar variables de entorno
load_dotenv() # Carga las variables de entorno

# Carga los datos del JSON
token = os.getenv("MANAGEMENT_TOKEN") # Token de acceso
space_id = os.getenv("SPACE_ID") # ID del espacio
environment_id = os.getenv("ENVIRONMENT") # ID del entorno

class ContentfulManager:
    def __init__(self):
        self.client = contentful_management.Client(token) # Cliente de la API de Contentful
        self.space_id = space_id # ID del espacio
        self.environment_id = environment_id # ID del entorno

    def entradas_por_pais(self,content_type_id, country_code, mostrar=True):
        """
        Trae las entradas de un content type por país
        Args:
            content_type_id (str): ID del content type a buscar
            country_code (str): Código del país a buscar
            mostrar (bool): Mostrar las entradas
        Returns:
            all_entries (list): Lista de entradas del content type
        """
        all_entries = []
        skip = 0
        limit = 100  # Límite máximo en Contentful

        while True:
            entries = self.client.entries(self.space_id, self.environment_id).all({
                'content_type': content_type_id,
                'fields.country_code': country_code,
                'skip': skip,
                'limit': limit
            })
            all_entries.extend(entries)
            skip += limit

            if len(entries) < limit:
                break  # Finaliza si no hay más entradas

        if mostrar:
            print(len(all_entries))
            mostrar_respuesta(all_entries)
        return all_entries

    def ver_entrada(self, id_entrada):
        entry = self.client.entries(self.space_id, self.environment_id).find(id_entrada)
        return entry

    def buscar_imagen(self, imagen_id):
        asset = self.client.assets(self.space_id, self.environment_id).find(imagen_id)
        return asset