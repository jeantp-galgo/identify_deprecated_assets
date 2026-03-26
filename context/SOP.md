# SOP — identify_deprecated_images

## Proposito

Ejecutar la auditoria de assets huerfanos en un espacio de Contentful y obtener un reporte CSV con los assets no referenciados por ninguna entrada, junto con sus metadatos.

---

## Configuracion inicial (primera vez)

### 1. Variables de entorno

```bash
cp env_example .env
```

Editar `.env` y completar los valores:

```env
MANAGEMENT_TOKEN=<token de acceso a la Contentful Management API, formato CFPAT-...>
SPACE_ID=<ID del espacio de Contentful>
ENVIRONMENT=<entorno a auditar, ej: master>
```

El token se obtiene en Contentful → Settings → API Keys → Content Management Tokens.

### 2. Instalacion de dependencias

```bash
python -m venv venv
venv\Scripts\activate         # Windows
source venv/bin/activate      # Linux / macOS

pip install contentful-management python-dotenv jupyter pandas
```

---

## Ejecucion

### Notebook principal

El unico punto de entrada es `notebooks/app.ipynb`.

1. Activar el entorno virtual

   ```bash
   venv\Scripts\activate
   ```

2. Iniciar Jupyter

   ```bash
   jupyter notebook
   ```

3. Navegar a `notebooks/app.ipynb`

4. Ejecutar todas las celdas en orden (Cell → Run All o Shift+Enter en cada celda)

5. Al finalizar, los resultados quedan en:
   - `notebooks/outputs/orphans.csv` — reporte final con todos los assets huerfanos
   - Consola del notebook — resumen con total de assets procesados y total de huerfanos

### Celdas del notebook

| Celda | Que hace |
|---|---|
| 1 | Importa dependencias y configura `sys.path` para acceder a `src/` |
| 2 | Instancia `ContentfulManager` (carga credenciales desde `.env`) |
| 3 | Llama `find_orphan_assets()` — esta es la operacion larga |
| 4 | Muestra los resultados como DataFrame de pandas |
| 5 | Normaliza el DataFrame (expande la columna `metadata`) |
| 6 | Exporta a `outputs/orphans.csv` |

---

## Reanudacion tras interrupcion

Si la ejecucion de `find_orphan_assets()` se interrumpe (error de red, cierre del kernel, etc.), el progreso queda guardado en `notebooks/outputs/checkpoint_state.json`.

Al volver a ejecutar la celda 3, la funcion detecta ese archivo automaticamente e imprime:

```
Retomando desde asset N (skip=X) con Y huerfanos ya encontrados...
```

No es necesario ninguna accion manual. El archivo de estado se elimina al completar exitosamente.

---

## Notas de operacion

| Situacion | Comportamiento | Accion recomendada |
|---|---|---|
| Asset con titulo que termina en `-feed` | Se salta sin consultar la API | Esperado — son assets usados externamente como almacenamiento |
| Asset referenciado en entrada no publicada | Se considera "en uso" y NO aparece en el reporte | Esperado — evita eliminar contenido en progreso |
| Asset sin titulo en Contentful | Usa el ID del asset como nombre en el reporte | No requiere accion |
| Entrada eliminada (error 404 en API) | Se registra en consola y se continua | Revisar si hay muchos errores al finalizar |
| Rate limit de la API (error 429) | Reintento automatico con backoff exponencial (hasta 5 intentos) | Si persiste, esperar unos minutos y volver a ejecutar |
| El reporte muestra 0 assets | Todos los assets tienen referencias activas | Verificar credenciales y que `ENVIRONMENT` sea correcto |
| Asset solo referenciado por entradas intermedias huerfanas | Aparece en el reporte como huerfano | Revisar manualmente si el asset esta realmente en uso antes de eliminar |

---

## Interpretacion del reporte

El archivo `orphans.csv` contiene una fila por cada asset sin referencias. Columnas clave:

- **`contentful_link`**: URL directa al asset en Contentful para verificarlo antes de eliminar
- **`is_published`**: si es `True`, el asset esta publicado pero ninguna entrada lo referencia — candidato prioritario para revisar
- **`time_since_update`**: antiguedad desde la ultima modificacion. Filtrar por `Mas de 1 año` es un buen punto de partida para identificar candidatos seguros a eliminar
- **`size_bytes`**: permite priorizar por impacto en almacenamiento

---

## Eliminacion de assets

La herramienta solo identifica — no elimina. La eliminacion debe hacerse manualmente:

1. Abrir el `contentful_link` del asset en el navegador
2. Verificar que el asset realmente no esta en uso (aplicar criterio de negocio)
3. En Contentful: Media → seleccionar asset → Delete
4. El Content Manager responsable del espacio debe aprobar cada eliminacion

---

## Frecuencia recomendada

| Situacion | Frecuencia |
|---|---|
| Mantenimiento regular | Mensual |
| Almacenamiento del plan > 80% | Inmediatamente |
| Despues de una migracion de contenido | Una vez al finalizar la migracion |

**Tiempo estimado:** menos de 30 minutos para espacios con hasta 5.000 assets.
