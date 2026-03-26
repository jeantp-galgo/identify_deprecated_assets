import contentful_management
import os
import time
import csv
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv() # Carga las variables de entorno

# Carga los datos del JSON
token = os.getenv("MANAGEMENT_TOKEN") # Token de acceso
space_id = os.getenv("SPACE_ID") # ID del espacio
environment_id = os.getenv("ENVIRONMENT") # ID del entorno

def _time_since(dt):
    """Convierte un datetime en un bucket de antigüedad legible."""
    if dt is None:
        return 'Desconocido'
    days = (datetime.now(timezone.utc) - dt).days
    if days < 30:
        return 'Menos de 1 mes'
    elif days < 90:
        return '1 a 3 meses'
    elif days < 180:
        return '3 a 6 meses'
    elif days < 365:
        return '6 meses a 1 año'
    else:
        return 'Más de 1 año'


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

    def _links_to_asset_with_retry(self, asset_id, max_retries=5):
        """Consulta links_to_asset con reintentos ante errores 429."""
        for attempt in range(max_retries):
            try:
                return self.client.entries(self.space_id, self.environment_id).all({
                    'links_to_asset': asset_id,
                    'limit': 1
                })
            except Exception as e:
                if '429' in str(e):
                    wait = 2 ** attempt  # backoff exponencial: 1s, 2s, 4s, 8s, 16s
                    print(f"  Rate limit alcanzado. Esperando {wait}s antes de reintentar...")
                    time.sleep(wait)
                else:
                    print(f"  Error al consultar referencias de {asset_id}: {e}")
                    return None
        print(f"  Máximo de reintentos alcanzado para {asset_id}. Se omite.")
        return None

    def find_orphan_assets(self, max_results=None, checkpoint_file='outputs/checkpoint.csv', checkpoint_every=50):
        """
        Itera los assets y retorna los huérfanos como lista de diccionarios.
        - max_results=None procesa todos los assets del espacio.
        - Guarda un checkpoint cada checkpoint_every assets procesados.
        - Si existe un estado previo, retoma desde donde se dejó.
        """
        state_file = checkpoint_file.replace('.csv', '_state.json')
        orphans, skip, processed = self._load_state(state_file)

        # Carga el último checkpoint
        if skip > 0:
            print(f"Retomando desde asset {processed} (skip={skip}) con {len(orphans)} huérfanos ya encontrados...")

        limit = 100

        while True:
            assets = self.client.assets(self.space_id, self.environment_id).all({
                'skip': skip,
                'limit': limit
            })

            for asset in assets:
                if max_results is not None and len(orphans) >= max_results:
                    break

                fields = asset._fields.get("es", {})
                title = fields.get('title', asset.id)

                # Excluye assets de imágenes que se usan externamente (se usa contentful como almacenamiento)
                # No están asociadas a ninguna entrada
                if str(title).lower().endswith('-feed'):
                    processed += 1
                    continue

                entries_linking = self._links_to_asset_with_retry(asset.id)
                processed += 1

                if entries_linking is None:
                    continue

                if len(entries_linking) == 0:
                    file_info = fields.get('file', {})
                    sys_info = asset.sys
                    orphans.append({
                        'id': asset.id,
                        'contentful_link': f'https://app.contentful.com/spaces/{self.space_id}/assets/{asset.id}',
                        'title': title,
                        'url': f"https:{file_info.get('url')}" if file_info.get('url') else "",
                        'metadata': {
                            'size_bytes': file_info.get('details', {}).get('size', ''),
                            'created_at': sys_info.get('created_at').strftime('%d/%m/%Y') if sys_info.get('created_at') else '',
                            'updated_at': sys_info.get('updated_at').strftime('%d/%m/%Y') if sys_info.get('updated_at') else '',
                            'time_since_update': _time_since(sys_info.get('updated_at')),
                            'is_published': sys_info.get('field_status', {}).get('*', {}).get('es') == 'published',
                        }
                    })

                if processed % 100 == 0:
                    print(f"Procesados: {processed} assets | Huérfanos encontrados: {len(orphans)}")

                if processed % checkpoint_every == 0:
                    self._save_checkpoint(orphans, checkpoint_file)
                    self._save_state(state_file, orphans, skip, processed)

            if max_results is not None and len(orphans) >= max_results:
                break

            if len(assets) < limit:
                break

            skip += limit

        # Guarda estado final y elimina el archivo de estado (proceso completo)
        self._save_checkpoint(orphans, checkpoint_file)
        if os.path.exists(state_file):
            os.remove(state_file)

        print(f"\nTotal assets procesados: {processed}")
        print(f"Total huérfanos encontrados: {len(orphans)}")
        return orphans

    def _save_state(self, state_file, orphans, skip, processed):
        """Guarda el estado de progreso para poder reanudar si se interrumpe."""
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({'skip': skip, 'processed': processed, 'orphans': orphans}, f, ensure_ascii=False)

    def _load_state(self, state_file):
        """Carga el estado previo si existe, o devuelve valores iniciales."""
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            return state['orphans'], state['skip'], state['processed']
        return [], 0, 0

    def _save_checkpoint(self, orphans, filepath):
        """Vuelca la lista de huérfanos al disco como CSV parcial."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'contentful_link', 'title', 'url',
                                                    'size_bytes', 'created_at', 'updated_at',
                                                    'time_since_update', 'is_published'])
            writer.writeheader()
            for row in orphans:
                writer.writerow({**{'id': row['id'], 'contentful_link': row['contentful_link'],
                                    'title': row['title'], 'url': row['url']}, **row['metadata']})
        print(f"  Checkpoint guardado: {len(orphans)} huérfanos en {filepath}")