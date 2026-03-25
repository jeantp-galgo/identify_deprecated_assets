# SOP — identify_deprecated_images

## Proposito

Ejecutar la auditoria de assets no referenciados en un espacio de Contentful y obtener un reporte CSV con los assets huerfanos, sus metadatos y el espacio de almacenamiento recuperable.

## Configuracion inicial

### Variables de entorno

```bash
cp env_example .env
```

Editar `.env` y completar los valores:

```env
MANAGEMENT_TOKEN=<token de acceso a Contentful Management API, formato CFPAT-...>
SPACE_ID=<ID del espacio de Contentful>
ENVIRONMENT=<entorno a auditar, ej: master>
```

El token se obtiene en Contentful → Settings → API Keys → Content Management Tokens.

### Instalacion

```bash
python -m venv venv
venv\Scripts\activate         # Windows
source venv/bin/activate      # Linux / macOS

pip install contentful-management python-dotenv jupyter
```

---

## Ejecucion

**Notebook principal**: `notebooks/app.ipynb`

1. Activar el entorno virtual (`venv\Scripts\activate`)
2. Abrir Jupyter: `jupyter notebook`
3. Navegar a `notebooks/app.ipynb`
4. Ejecutar todas las celdas en orden (Cell → Run All)
5. Al finalizar, el reporte CSV se guarda en `outputs/unused_assets_YYYYMMDD_HHMMSS.csv`

---

## Notas

| Situacion | Comportamiento | Solucion |
|---|---|---|
| Asset referenciado en entrada no publicada | Se considera "en uso" y NO aparece en el reporte | Esperado — evita eliminar contenido en progreso |
| Asset sin titulo en Contentful | Usa el ID del asset como nombre en el reporte | No requiere accion |
| Entrada eliminada (error 404 en API) | Se registra en log y se continua sin interrumpir | Revisar log al finalizar si hay muchos errores |
| Rate limit de la API (error 429) | Reintento automatico con backoff exponencial | Si persiste, esperar unos minutos y volver a ejecutar |
| El reporte muestra 0 assets | Todos los assets tienen referencias activas | Verificar credenciales y que `ENVIRONMENT` sea correcto |
| Referencia en campo rich text | El sistema analiza nodos `embedded-asset-block` | Incluido en la logica de recorrido del grafo |

**Frecuencia recomendada de ejecucion:**
- Mantenimiento regular: mensual
- Si el almacenamiento supera el 80% del plan: inmediatamente
- Despues de una migracion de contenido: una vez al finalizar

**Tiempo estimado:** menos de 30 minutos para espacios con hasta 5.000 assets.

**Importante:** La herramienta solo identifica assets para eliminar — no los elimina automaticamente. La eliminacion debe hacerse manualmente en Contentful (Media → seleccionar asset → Delete) por el Content Manager responsable.
