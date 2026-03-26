# identify_deprecated_images — Contexto del Proyecto

## Que es

Herramienta Python que audita un espacio de Contentful para detectar assets multimedia (imagenes, videos, documentos) que no son referenciados por ninguna entrada, ya sea publicada o en borrador. Resuelve el problema de acumulacion de assets huerfanos que ocupan almacenamiento y generan costos sin aportar valor.

El sistema consulta la Contentful Management API para determinar si cada asset tiene al menos una entrada enlazada. Los assets sin referencias se clasifican como huerfanos y se exportan a un CSV con sus metadatos. El proceso es reanudable: si la ejecucion se interrumpe, retoma desde donde quedo gracias a un archivo de estado en disco.

## Estado (2026-03-26)

El proyecto esta completamente funcional. Todas las funcionalidades criticas estan implementadas y el flujo de extremo a extremo ha sido ejecutado exitosamente.

### Completado

- Clase `ContentfulManager` con paginacion completa de assets
- Consulta de referencias entrantes via `links_to_asset` con reintentos por rate limit (backoff exponencial)
- Filtro de assets con titulo que termina en `-feed` (assets usados externamente como almacenamiento)
- Recopilacion de metadatos por asset huerfano
- Exportacion a CSV (`outputs/orphans.csv`)
- Sistema de checkpoints cada 50 assets procesados (`outputs/checkpoint.csv`)
- Reanudacion automatica desde el ultimo checkpoint si la ejecucion se interrumpe
- Resumen en consola al finalizar (total procesados, total huerfanos)
- Notebook principal funcional (`notebooks/app.ipynb`)
- Visualizacion con pandas en el notebook

## Flujo general

```text
.env (credenciales)
      |
      v
ContentfulManager.__init__()
      |
      v
find_orphan_assets()
      |
      v
_load_state() — retoma desde checkpoint si existe
      |
      v
Paginar todos los assets (100/pagina, skip incremental)
      |
      v
Por cada asset:
  - Filtrar si el titulo termina en '-feed'  -->  saltar
  - _links_to_asset_with_retry(asset_id)
      - Si tiene entradas enlazadas  -->  asset en uso, saltar
      - Si no tiene entradas  -->  recopilar metadatos y agregar a huerfanos
  - Cada 50 assets: guardar checkpoint en disco
  - Cada 100 assets: imprimir progreso en consola
      |
      v
_save_checkpoint()  -->  outputs/checkpoint.csv
_save_state() eliminado al finalizar
      |
      v
outputs/orphans.csv  +  resumen en consola
```

## Arquitectura

```
identify_deprecated_images/
├── notebooks/
│   ├── app.ipynb                              # Punto de entrada principal
│   └── outputs/
│       ├── orphans.csv                        # Reporte final (generado en ejecucion)
│       └── checkpoint.csv                     # CSV parcial de checkpoints (generado en ejecucion)
├── src/
│   └── sources/
│       └── contentful/
│           └── handle_contentful.py           # Clase ContentfulManager + funcion _time_since
├── context/
│   ├── PROJECT_CONTEXT.md                     # Este archivo
│   ├── SOP.md                                 # Procedimiento operativo estandar
│   └── PRD.md                                 # Especificacion funcional original
├── scripts/                                   # Vacio — previsto para CLI futuro
├── env_example                                # Plantilla de variables de entorno
└── .env                                       # Credenciales locales (no versionado)
```

| Archivo | Funcion |
|---|---|
| `src/sources/contentful/handle_contentful.py` | Logica principal: clase `ContentfulManager` con paginacion, consulta de referencias, checkpoints y exportacion CSV |
| `notebooks/app.ipynb` | Orquesta el flujo: instancia `ContentfulManager`, llama `find_orphan_assets()`, muestra resultados con pandas y exporta CSV final |

## Output

### Archivo principal: `notebooks/outputs/orphans.csv`

Una fila por asset huerfano. Se sobreescribe en cada ejecucion completa.

| Columna | Descripcion |
|---|---|
| `id` | ID unico del asset en Contentful |
| `contentful_link` | URL directa al asset en el panel de Contentful |
| `title` | Titulo del asset (ID como fallback si no tiene titulo) |
| `url` | URL publica del archivo (vacia si el asset no tiene archivo asociado) |
| `size_bytes` | Tamano del archivo en bytes (vacio si no aplica) |
| `created_at` | Fecha de creacion en formato `DD/MM/YYYY` |
| `updated_at` | Fecha de ultima modificacion en formato `DD/MM/YYYY` |
| `time_since_update` | Bucket de antiguedad legible (ver tabla abajo) |
| `is_published` | `True` si el asset esta publicado, `False` si esta en borrador |

Valores posibles de `time_since_update`:

| Valor | Rango |
|---|---|
| `Menos de 1 mes` | Menos de 30 dias |
| `1 a 3 meses` | 30 a 89 dias |
| `3 a 6 meses` | 90 a 179 dias |
| `6 meses a 1 año` | 180 a 364 dias |
| `Mas de 1 año` | 365 dias o mas |

### Archivo de checkpoint: `notebooks/outputs/checkpoint.csv`

Mismo formato que `orphans.csv`. Se actualiza cada 50 assets procesados durante la ejecucion. Permite revisar resultados parciales si la ejecucion se interrumpe. Se elimina el archivo de estado JSON al completar correctamente.

## Comportamientos importantes

| Comportamiento | Detalle |
|---|---|
| Filtro `-feed` | Assets cuyo titulo termina en `-feed` se saltan sin consultar la API. Son assets usados externamente como almacenamiento y siempre aparecerian como huerfanos. |
| Idioma fijo `es` | Los campos del asset (`title`, `file`) se leen del locale `es`. Si el espacio usa otro locale por defecto, el titulo puede quedar vacio. |
| Rate limit (429) | Reintento automatico con backoff exponencial: 1s, 2s, 4s, 8s, 16s (hasta 5 intentos). Si se agota, el asset se omite del reporte. |
| Error no-429 | Se registra en consola y el asset se omite. La ejecucion continua. |
| Reanudacion | Si existe `outputs/checkpoint_state.json` al iniciar, la ejecucion retoma desde el `skip` guardado. El archivo de estado se borra al completar exitosamente. |
| Nivel de referencia | La consulta es de un solo nivel directo (`links_to_asset`). No recorre cadenas multi-nivel ni campos rich text. Un asset referenciado solo por una entrada intermedia huerfana aparecera como huerfano. |

## Stack tecnico

| Tecnologia | Uso |
|---|---|
| Python 3.11 | Lenguaje principal |
| `contentful-management` | SDK oficial para la Contentful Management API |
| `python-dotenv` | Carga de variables de entorno desde `.env` |
| `pandas` | Normalizacion y visualizacion de resultados en el notebook |
| `jupyter` | Entorno de ejecucion interactivo |
| `csv`, `json` | Modulos estandar para exportacion y persistencia de estado |

## Requisitos

Variables de entorno obligatorias en `.env`:

| Variable | Descripcion |
|---|---|
| `MANAGEMENT_TOKEN` | Token de acceso a la Contentful Management API (formato `CFPAT-...`) |
| `SPACE_ID` | ID del espacio de Contentful a auditar |
| `ENVIRONMENT` | Entorno a auditar (ej: `master`) |
