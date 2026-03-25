# identify_deprecated_images — Contexto del Proyecto

## Que es

Herramienta Python que audita un espacio de Contentful para detectar assets multimedia (imagenes, videos, documentos) que no son referenciados por ninguna entrada, ya sea publicada o en borrador. Resuelve el problema de acumulacion de assets huerfanos que ocupan almacenamiento y generan costos sin aportar valor.

El sistema recorre el grafo completo de referencias de Contentful (asset → entrada intermedia → entrada padre → ...) para determinar con certeza si un asset esta en uso o no, y genera un reporte CSV con los assets inutilizados y sus metadatos.

## Estado (2026-03-25)

### Completado
- Estructura de directorios del proyecto
- Documentacion (PRD y SOP)
- Clase `ContentfulManager` con metodos basicos (paginacion, buscar entrada, buscar asset)
- Esqueleto del notebook principal

### En progreso
-

### Por hacer
- Implementar enumeracion completa de assets con paginacion
- Implementar recorrido del grafo de referencias (`links_to_asset`)
- Detectar referencias embebidas en campos rich text
- Recopilar metadatos de cada asset (titulo, fecha, tamano, MIME type)
- Generar reporte CSV con marca de tiempo
- Manejo de rate limits con backoff exponencial
- Completar notebook de extremo a extremo
- Tests unitarios

## Flujo general

```text
.env (credenciales)
      ↓
Contentful Management API
      ↓
Paginar todos los assets (100/pagina)
      ↓
Por cada asset → consultar referencias entrantes (links_to_asset)
      ↓
Recorrer grafo multi-nivel + detectar referencias en rich text
      ↓
Sin referencias → asset huerfano
      ↓
Recopilar metadatos (ID, titulo, fecha, tamano, URL, MIME)
      ↓
outputs/unused_assets_YYYYMMDD_HHMMSS.csv
```

## Arquitectura

```
identify_deprecated_images/
├── notebooks/
│   └── app.ipynb                          # Punto de entrada principal
├── src/
│   └── sources/
│       └── contentful/
│           └── handle_contentful.py       # Clase ContentfulManager
├── scripts/                               # (vacio — previsto para CLI)
├── prd.md                                 # Especificacion funcional detallada
├── SOP.md                                 # Procedimiento operativo
├── env_example                            # Plantilla de variables de entorno
└── .env                                   # Credenciales locales (no versionado)
```

| Archivo | Funcion |
|---|---|
| `src/sources/contentful/handle_contentful.py` | Clase principal que interactua con la Contentful Management API |
| `notebooks/app.ipynb` | Orquesta el flujo completo: conexion, auditoria, generacion de reporte |

## Output

Archivo CSV en `outputs/unused_assets_YYYYMMDD_HHMMSS.csv` con una fila por asset no referenciado.

| Columna | Descripcion |
|---|---|
| `asset_id` | ID unico del asset en Contentful |
| `title` | Titulo del asset (ID como fallback si no tiene titulo) |
| `last_updated` | Fecha ISO de ultima modificacion |
| `days_unused` | Dias transcurridos desde la ultima modificacion |
| `time_since_update` | Formato legible (ej: "7 meses") |
| `file_url` | URL publica del archivo |
| `mime_type` | Tipo MIME (image/jpeg, video/mp4, etc.) |
| `file_size_bytes` | Tamano en bytes |
| `file_size_mb` | Tamano en MB |

Ademas imprime en consola un resumen con el total de assets escaneados, assets huerfanos encontrados y espacio recuperable.

## Stack tecnico

| Tecnologia | Uso |
|---|---|
| Python 3.x | Lenguaje principal |
| `contentful-management` | SDK oficial para la Contentful Management API |
| `python-dotenv` | Carga de variables de entorno desde `.env` |
| `jupyter` | Entorno de ejecucion interactivo |
| Contentful Management API | Fuente de datos: assets, entradas, referencias |

## Requisitos

Variables de entorno obligatorias en `.env`:

| Variable | Descripcion |
|---|---|
| `MANAGEMENT_TOKEN` | Token de acceso a la Contentful Management API (CFPAT-...) |
| `SPACE_ID` | ID del espacio de Contentful a auditar |
| `ENVIRONMENT` | Entorno a auditar (ej: `master`) |
