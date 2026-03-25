# PRD: Identificación de Assets Obsoletos en Contentful

## 1. Descripción general del producto

### 1.1 Título del documento y versión

- PRD: Identificación de Assets Obsoletos en Contentful
- Versión: 1.0.0

### 1.2 Resumen del producto

Este proyecto es una utilidad interna desarrollada en Python para identificar y reportar assets multimedia (imágenes, videos, documentos, etc.) que se encuentran almacenados en un espacio de Contentful CMS pero que ya no son referenciados por ningún contenido publicado ni en borrador. El problema central que resuelve es la acumulación de almacenamiento innecesario: con el tiempo, los assets se acumulan en Contentful sin que ninguna entrada los utilice, ocupando espacio y generando costos sin aportar valor.

La herramienta funciona iterando sobre cada asset del entorno de Contentful configurado, resolviendo la cadena completa de referencias desde el asset hasta las entradas intermedias y las entradas de nivel superior, y marcando como obsoleto cualquier asset que quede fuera de ese grafo de referencias. Para cada asset no referenciado, la herramienta recopila su ID, título, fecha de última actualización y el tiempo transcurrido desde su última modificación, generando un reporte estructurado sobre el cual el equipo puede actuar.

El resultado final es un reporte exportable (en formato CSV) que los gestores de contenido o los desarrolladores pueden revisar antes de realizar eliminaciones masivas en Contentful, reduciendo el consumo de almacenamiento y manteniendo la biblioteca de medios ordenada.

## 2. Objetivos

### 2.1 Objetivos de negocio

- Reducir el consumo de almacenamiento en Contentful identificando assets que pueden eliminarse de forma segura.
- Proveer un proceso repetible y auditable para la limpieza de la biblioteca de medios, en lugar de revisiones manuales ad hoc.
- Disminuir el riesgo de eliminaciones accidentales generando un reporte para revisión humana antes de realizar cualquier operación destructiva.
- Sentar las bases para auditorías programadas o bajo demanda a medida que crece la biblioteca de contenido.

### 2.2 Objetivos del usuario

- Obtener rápidamente una lista completa de assets no utilizados sin necesidad de navegar manualmente por la interfaz de Contentful.
- Conocer cuánto tiempo lleva sin usarse cada asset para facilitar la priorización de la limpieza.
- Confiar en que la herramienta recorre correctamente las cadenas de referencias de múltiples niveles y no marca como obsoletos assets que están en uso a través de entradas intermedias.
- Exportar los resultados en un formato que pueda compartirse con gestores de contenido no técnicos.

### 2.3 Lo que está fuera del alcance

- Eliminar assets automáticamente sin confirmación humana explícita — la eliminación queda fuera del alcance de esta versión.
- Modificar, actualizar o publicar ninguna entrada ni asset en Contentful.
- Dar soporte a plataformas CMS distintas a Contentful.
- Construir una interfaz gráfica o un panel web.
- Monitoreo en tiempo real o basado en webhooks del uso de assets.

## 3. Personas de usuario

### 3.1 Tipos de usuario principales

- Desarrollador o ingeniero de datos que ejecuta la herramienta y es propietario del código.
- Gestor de contenido que recibe el reporte generado y actúa en consecuencia.

### 3.2 Detalles básicos de cada persona

- **Desarrollador**: Ingeniero con dominio de Python, familiarizado con APIs REST y configuración basada en variables de entorno. Ejecuta la herramienta desde la línea de comandos o desde un notebook de Jupyter, revisa los logs y comparte el reporte de salida con el equipo de contenido.
- **Gestor de contenido**: Usuario no técnico que consume el reporte CSV o Excel, valida si los assets listados realmente están en desuso (aplicando contexto de negocio que la herramienta no puede inferir) y aprueba su eliminación.

### 3.3 Acceso basado en roles

- **Desarrollador (operador de la herramienta)**: Requiere un token de la API de Gestión de Contentful (Content Management API) con acceso de lectura a assets y entradas en el espacio y entorno de destino. No se necesitan permisos de escritura en esta versión.
- **Gestor de contenido (consumidor del reporte)**: No tiene acceso directo a la herramienta ni a la API de Contentful; interactúa únicamente con el archivo de reporte exportado.

## 4. Requisitos funcionales

- **Enumeración de assets** (Prioridad: Crítica)

  - La herramienta debe recuperar todos los assets del espacio y entorno de Contentful configurados mediante paginación, gestionando de forma transparente el límite de 100 ítems por página de la API hasta obtener todos los assets.
  - Deben incluirse assets de todos los tipos MIME (imágenes, videos, PDFs, etc.) salvo que se configure un filtro explícito.

- **Recorrido del grafo de referencias** (Prioridad: Crítica)

  - Para cada asset, la herramienta debe determinar si está vinculado desde al menos una entrada, siguiendo cadenas de referencias de múltiples niveles (asset → entrada intermedia → entrada padre → ... → entrada de nivel superior).
  - El recorrido debe manejar ciclos en el grafo de referencias sin entrar en un bucle infinito.
  - Un asset se considera "en uso" si y solo si al menos un camino alcanzable conduce a una entrada dentro del espacio, independientemente del estado de publicación de esa entrada.
  - La herramienta también debe contemplar assets referenciados a través de campos de texto enriquecido (rich text), que embeben enlaces de forma diferente a los campos de referencia estándar.

- **Identificación de assets no utilizados** (Prioridad: Crítica)

  - Un asset se clasifica como no utilizado si ninguna cadena de referencias lo conecta con alguna entrada del espacio.
  - La herramienta debe producir una lista completa de todos los assets no utilizados encontrados en cada ejecución.

- **Recolección de metadatos de assets no utilizados** (Prioridad: Alta)

  - Para cada asset no utilizado, la herramienta debe recopilar:
    - ID del asset (`sys.id`)
    - Título del asset (del campo `fields.title` en el idioma configurado; si no existe, usar el ID como valor de respaldo)
    - Fecha de última actualización (`sys.updatedAt`)
    - Tiempo transcurrido desde la última actualización, expresado en días y en formato legible (por ejemplo, "14 meses")
    - URL del archivo y tipo MIME del asset (para que los gestores puedan previsualizarlo antes de eliminarlo)
    - Tamaño del archivo en bytes y en formato legible (MB/KB), para cuantificar el almacenamiento potencialmente recuperable

- **Generación del reporte** (Prioridad: Alta)

  - La herramienta debe exportar un reporte estructurado como archivo CSV con una fila por asset no utilizado.
  - El CSV debe incluir todos los campos de metadatos listados anteriormente.
  - El reporte debe guardarse en una ruta de salida configurable (con valor predeterminado en el directorio `outputs/` en la raíz del proyecto).
  - El nombre del archivo debe incluir una marca de tiempo para evitar sobrescribir reportes anteriores (por ejemplo, `unused_assets_20260325_143000.csv`).

- **Configuración mediante variables de entorno** (Prioridad: Crítica)

  - Todas las credenciales de Contentful (`MANAGEMENT_TOKEN`, `SPACE_ID`, `ENVIRONMENT`) deben cargarse exclusivamente desde variables de entorno; nunca deben estar escritas directamente en el código.
  - El archivo `env_example` debe documentar todas las variables requeridas.

- **Registro de progreso y logs** (Prioridad: Media)

  - La herramienta debe emitir logs de progreso que indiquen cuántos assets se han procesado y cuántos quedan, para que las ejecuciones largas sean observables.
  - Los errores al recuperar assets o entradas individuales deben registrarse con el ID correspondiente y omitirse de forma controlada, sin interrumpir la ejecución completa.
  - Al finalizar debe imprimirse un resumen: total de assets analizados, total de assets no utilizados encontrados y tamaño total estimado de los archivos no utilizados.

- **Interfaz de notebook** (Prioridad: Media)

  - Un notebook de Jupyter (`notebooks/app.ipynb`) debe demostrar el flujo de trabajo completo de extremo a extremo — inicialización, recorrido y generación del reporte — sirviendo como entorno de desarrollo y como ejemplo de uso.

## 5. Experiencia de usuario

### 5.1 Puntos de entrada y flujo del primer uso

- El usuario clona el repositorio y copia `env_example` a `.env`, completando sus credenciales de Contentful.
- El usuario crea un entorno virtual, instala las dependencias y ejecuta la herramienta bien desde la línea de comandos (`python scripts/run_audit.py`) o bien ejecutando el notebook de Jupyter.
- En la primera ejecución, la herramienta valida que todas las variables de entorno requeridas estén presentes y lanza un error claro y descriptivo si alguna falta.

### 5.2 Experiencia principal

- **Inicialización**: La clase `ContentfulManager` se instancia y las credenciales se validan contra la API antes de iniciar el procesamiento.

  - Garantiza que el usuario esté correctamente autenticado antes de invertir tiempo en un escaneo prolongado.

- **Paginación de assets**: La herramienta recupera los assets en lotes de 100, registrando el progreso tras cada lote.

  - Hace que una operación potencialmente lenta (miles de assets) sea observable y confiable.

- **Resolución de referencias**: Para cada asset, la herramienta consulta la API de entradas para encontrar cualquier entrada que lo referencie, y luego verifica de forma recursiva si esas entradas son a su vez referenciadas, hasta un límite de profundidad configurable.

  - Maneja correctamente las cadenas de referencias de múltiples niveles sin falsos positivos.

- **Exportación del reporte**: Tras procesar todos los assets, la herramienta escribe el archivo CSV e imprime en consola un resumen legible.

  - Proporciona al operador retroalimentación inmediata y un artefacto compartible.

### 5.3 Funcionalidades avanzadas y casos borde

- Los assets referenciados únicamente desde entradas no publicadas (en borrador) deben seguir considerarse "en uso" para evitar la eliminación accidental de contenido en progreso.
- Los assets sin valor en `fields.title` deben usar el ID del asset como valor de respaldo en la columna de título del reporte.
- Las entradas que ya no existen (eliminadas pero aún referenciadas por un enlace) deben manejarse de forma controlada: un error 404 de la API no debe interrumpir la ejecución.
- La herramienta debe gestionar la limitación de tasa de Contentful (respuestas 429) implementando retroceso exponencial con lógica de reintento.
- Los entornos con bibliotecas de assets muy grandes (más de 10.000 assets) deben completar su ejecución en un tiempo razonable; la herramienta debe procesar las consultas de referencias de forma concurrente donde los límites de tasa de la API lo permitan.
- Si la variable `ENVIRONMENT` no está definida, la herramienta debe usar `master` como valor predeterminado y registrar una advertencia.

### 5.4 Aspectos destacados de la experiencia

- La salida en consola utiliza mensajes de progreso claros y legibles (por ejemplo, "Procesando asset 450 de 1.200...").
- El reporte CSV incluye una columna numérica `days_unused` para facilitar el ordenamiento en Excel o cualquier herramienta de hojas de cálculo.
- El resumen final incluye la ruta completa al archivo de reporte generado, para que el operador pueda localizarlo inmediatamente.

## 6. Narrativa

Un gestor de contenido advierte que el panel de almacenamiento de Contentful está aproximándose al límite del plan, pero no está claro qué assets están generando ese desbordamiento. En lugar de pasar horas navegando por miles de entradas multimedia en la interfaz de Contentful, un desarrollador ejecuta esta herramienta, que de forma autónoma itera sobre cada asset, recorre cada cadena de referencias y produce en minutos un reporte CSV ordenado. El gestor de contenido abre el archivo, filtra los assets sin uso durante más de seis meses, contrasta un puñado de casos borde con el equipo de desarrollo y luego elimina en lote los huérfanos confirmados directamente en Contentful, recuperando gigabytes de almacenamiento sin riesgo alguno de afectar el contenido publicado.

## 7. Métricas de éxito

### 7.1 Métricas centradas en el usuario

- El tiempo para generar un reporte de auditoría completo en un espacio con hasta 5.000 assets es inferior a 15 minutos.
- Cero falsos positivos: ningún asset marcado como no utilizado está realmente referenciado por una entrada publicada o en borrador.
- El reporte no requiere ningún postprocesamiento ni formato manual de columnas para poder abrirse en Excel.

### 7.2 Métricas de negocio

- Reducción de almacenamiento de al menos el 20% en el espacio de Contentful de destino tras el primer ciclo de limpieza guiado por el reporte de la herramienta.
- La auditoría puede repetirse mensualmente con un esfuerzo mínimo del desarrollador (menos de 5 minutos de configuración manual por ejecución).

### 7.3 Métricas técnicas

- La herramienta gestiona los límites de tasa de la API de Contentful de forma transparente: ninguna ejecución debe fallar por un error 429.
- El uso de memoria se mantiene por debajo de 512 MB incluso en espacios con más de 10.000 assets, transmitiendo los resultados en lugar de cargar todos los datos en memoria simultáneamente.
- Todas las funciones susceptibles de prueba unitaria alcanzan al menos el 80% de cobertura de código.

## 8. Consideraciones técnicas

### 8.1 Puntos de integración

- **API de Gestión de Contentful (CMA)**: Se usa para leer assets y entradas. El SDK de Python `contentful_management` encapsula esta API. La paginación, el filtrado por tipo de contenido y las consultas de referencias se realizan a través de esta interfaz.
- **`python-dotenv`**: Carga las credenciales del archivo `.env` en las variables de entorno en tiempo de ejecución.
- **Jupyter**: El notebook `notebooks/app.ipynb` provee una interfaz interactiva para el desarrollo y la demostración.

### 8.2 Almacenamiento de datos y privacidad

- Las credenciales de Contentful (`MANAGEMENT_TOKEN`) nunca deben confirmarse en el control de versiones. El archivo `.gitignore` ya excluye `.env`.
- El reporte CSV generado puede contener títulos internos de assets y URLs; debe tratarse como documentación interna y no compartirse públicamente.
- Ningún dato de assets se escribe en ningún sistema externo: la herramienta es estrictamente de solo lectura respecto a Contentful.
- Los archivos CSV de salida están excluidos del control de versiones mediante el `.gitignore` (los directorios `outputs/` y los archivos `*.csv` ya están listados).

### 8.3 Escalabilidad y rendimiento

- La paginación debe implementarse tanto para la recuperación de assets como para la de entradas, ya que ambos endpoints limitan las respuestas a 100 ítems por solicitud.
- La resolución de referencias es el cuello de botella de rendimiento: para cada asset se necesita al menos una llamada a la API para verificar las entradas que lo referencian. El enfoque recomendado es el uso masivo del parámetro `links_to_asset` en el endpoint de entradas, ya que permite recuperar en una sola llamada todas las entradas que referencian un asset dado.
- Para espacios grandes, debe considerarse la paralelización del procesamiento de assets mediante `concurrent.futures.ThreadPoolExecutor` con un límite de concurrencia que respete el límite de tasa de la API de Contentful (típicamente 10 solicitudes por segundo para la CMA).
- Los resultados intermedios deben volcarse periódicamente al disco para evitar perder progreso si la ejecución se interrumpe.

### 8.4 Desafíos potenciales

- **Cadenas de referencias profundas**: Un asset puede estar vinculado desde una entrada intermedia (por ejemplo, una entrada de tipo "Bloque multimedia") que a su vez está vinculada desde una entrada de página. El recorrido debe manejar profundidades arbitrarias, no solo un nivel.
- **Referencias circulares**: Contentful no impide que las entradas se referencien entre sí de forma cíclica. El algoritmo de recorrido debe rastrear los IDs de entradas visitadas para evitar bucles infinitos.
- **Campos de texto enriquecido**: Los enlaces embebidos en el texto enriquecido de Contentful (CFDA rich text) se almacenan en el formato `nodeType: embedded-asset-block` dentro del JSON del documento, no como campos de referencia estándar. La herramienta debe analizarlos explícitamente.
- **Múltiples idiomas**: Si el espacio utiliza varios idiomas, es posible que los títulos de assets y los valores de campo deban obtenerse para un idioma específico. La herramienta debe usar el idioma predeterminado del espacio y permitir configurarlo.
- **Limitación de tasa de la API**: La CMA impone límites de tasa que pueden interrumpir escaneos prolongados. Debe implementarse retroceso exponencial con variación aleatoria (jitter).

## 9. Hitos y secuenciación

### 9.1 Estimación del proyecto

- Pequeño a mediano: 1 a 2 semanas para un solo desarrollador

### 9.2 Tamaño y composición del equipo

- 1 desarrollador: backend en Python, integración con la API, generación del reporte

### 9.3 Fases sugeridas

- **Fase 1**: Infraestructura base y enumeración de assets (2 a 3 días)

  - Configurar la estructura del proyecto (ya parcialmente realizada).
  - Implementar `ContentfulManager` con recuperación paginada completa de assets.
  - Agregar validación de variables de entorno y manejo de errores.
  - Escribir pruebas unitarias para la lógica de paginación usando respuestas de API simuladas.

- **Fase 2**: Recorrido del grafo de referencias (3 a 4 días)

  - Implementar la consulta `links_to_asset` para encontrar las entradas que referencian cada asset.
  - Implementar el recorrido recursivo de la cadena de referencias con detección de ciclos.
  - Gestionar el análisis de enlaces en campos de texto enriquecido.
  - Escribir pruebas unitarias para la lógica de recorrido, incluyendo escenarios de referencias circulares y cadenas profundas.

- **Fase 3**: Recolección de metadatos y generación del reporte (1 a 2 días)

  - Recopilar todos los campos de metadatos requeridos para los assets no utilizados.
  - Implementar la exportación CSV con nombres de archivo que incluyan marca de tiempo.
  - Agregar la salida del resumen en consola.

- **Fase 4**: Pulido, rendimiento y documentación (1 día)

  - Agregar retroceso exponencial para solicitudes con límite de tasa.
  - Optimizar el rendimiento con procesamiento concurrente donde sea apropiado.
  - Finalizar el notebook de Jupyter como ejemplo de uso.
  - Actualizar `env_example` y agregar un `README.md` con instrucciones de configuración y uso.

## 10. Historias de usuario

### 10.1 Obtener todos los assets de un espacio de Contentful

- **ID**: ID-001
- **Descripción**: Como desarrollador, quiero que la herramienta recupere automáticamente todos los assets del espacio y entorno de Contentful configurados, incluyendo espacios con más de 100 assets, para que ningún asset quede fuera de la auditoría.
- **Criterios de aceptación**:
  - La herramienta usa paginación con un tamaño de página de 100 y continúa recuperando datos hasta que el número total de assets obtenidos coincida con el total reportado por la API.
  - La herramienta registra en el log el número total de assets encontrados antes de iniciar el procesamiento.
  - Si la variable `ENVIRONMENT` no está definida, la herramienta usa `master` como valor predeterminado y registra una advertencia.
  - Si las credenciales faltan o son inválidas, la herramienta lanza un error descriptivo de inmediato y termina la ejecución sin procesar nada.

### 10.2 Identificar assets no referenciados por ninguna entrada

- **ID**: ID-002
- **Descripción**: Como desarrollador, quiero que la herramienta determine qué assets no están referenciados por ninguna entrada del espacio, para que solo los assets genuinamente no utilizados aparezcan en el reporte.
- **Criterios de aceptación**:
  - Para cada asset, la herramienta consulta la API de entradas usando el parámetro `links_to_asset` para encontrar todas las entradas que lo referencian directamente.
  - Si un asset es referenciado directamente por al menos una entrada, se clasifica como "en uso" y se excluye del reporte.
  - Si un asset no tiene referencias directas, se clasifica como "no utilizado" y se incluye en el reporte.
  - El resultado de la clasificación (en uso / no utilizado) se registra por asset a nivel de depuración (debug).

### 10.3 Resolver cadenas de referencias de múltiples niveles

- **ID**: ID-003
- **Descripción**: Como desarrollador, quiero que la herramienta siga las cadenas de referencias a través de entradas intermedias (por ejemplo, asset → entrada de bloque multimedia → entrada de página), para que los assets usados indirectamente no queden marcados falsamente como no utilizados.
- **Criterios de aceptación**:
  - Cuando un asset solo es referenciado por entradas intermedias, la herramienta verifica si esas entradas intermedias son a su vez referenciadas por otras entradas.
  - Si la cadena conecta finalmente con al menos una entrada en cualquier nivel, el asset se clasifica como "en uso".
  - El recorrido maneja correctamente cadenas de al menos tres niveles de profundidad (asset → entrada A → entrada B → entrada C).
  - Una profundidad máxima de recorrido configurable (con valor predeterminado de 10 niveles) previene llamadas excesivas a la API en grafos inusualmente profundos.

### 10.4 Detectar y manejar referencias circulares

- **ID**: ID-004
- **Descripción**: Como desarrollador, quiero que la herramienta maneje las cadenas de referencias circulares en el grafo de entradas sin entrar en un bucle infinito, para que la auditoría se complete de forma fiable independientemente de la estructura de los datos.
- **Criterios de aceptación**:
  - El algoritmo de recorrido mantiene un conjunto de IDs de entradas visitadas por cada camino de recorrido.
  - Si se encuentra un ID de entrada ya visitado durante el recorrido, esa rama se termina sin realizar más llamadas a la API.
  - La herramienta se completa correctamente en un espacio que contiene referencias circulares entre entradas.
  - No ocurre ningún desbordamiento de pila ni error de memoria debido a referencias circulares.

### 10.5 Analizar referencias de assets dentro de campos de texto enriquecido

- **ID**: ID-005
- **Descripción**: Como desarrollador, quiero que la herramienta detecte assets embebidos en campos de texto enriquecido de Contentful, para que los assets usados en cuerpos de texto o contenido editorial no queden marcados incorrectamente como no utilizados.
- **Criterios de aceptación**:
  - La herramienta analiza los nodos del documento de texto enriquecido de tipo `embedded-asset-block` y extrae los IDs de assets referenciados.
  - Los assets encontrados en campos de texto enriquecido se clasifican como "en uso".
  - Este análisis se aplica de forma adicional a la resolución de campos de referencia estándar.

### 10.6 Recopilar metadatos de assets no utilizados

- **ID**: ID-006
- **Descripción**: Como desarrollador, quiero que la herramienta recopile los metadatos clave de cada asset no utilizado, para que el reporte proporcione información suficiente para que los gestores de contenido tomen decisiones informadas sobre su eliminación.
- **Criterios de aceptación**:
  - Para cada asset no utilizado, la herramienta recopila: ID del asset, título del asset (usando el ID como valor de respaldo si el título no existe), fecha de última actualización, días transcurridos desde la última actualización, tiempo legible desde la última actualización, URL del archivo, tipo MIME y tamaño del archivo (en bytes y en MB).
  - Todos los campos están presentes en la salida para cada fila; ningún campo queda en blanco salvo que el dato genuinamente no exista en la respuesta de Contentful.
  - El valor de `days_unused` se calcula relativo a la fecha y hora en que se ejecuta la herramienta.

### 10.7 Exportar los assets no utilizados a un reporte CSV

- **ID**: ID-007
- **Descripción**: Como desarrollador, quiero que la herramienta exporte la lista de assets no utilizados a un archivo CSV, para que los gestores de contenido puedan revisar los hallazgos y actuar sobre ellos sin necesitar acceso a la herramienta ni a Contentful.
- **Criterios de aceptación**:
  - La herramienta genera un archivo CSV en el directorio `outputs/` (o en una ruta alternativa configurada).
  - El nombre del archivo incluye una marca de tiempo en el formato `YYYYMMDD_HHMMSS` para evitar sobrescribir reportes anteriores.
  - El CSV contiene una fila de encabezado y una fila de datos por cada asset no utilizado.
  - El CSV puede abrirse directamente en Excel o Google Sheets sin necesidad de formato adicional.
  - Si no se encuentran assets no utilizados, la herramienta escribe un CSV solo con la fila de encabezado y registra un mensaje apropiado.

### 10.8 Mostrar un resumen de la ejecución en consola

- **ID**: ID-008
- **Descripción**: Como desarrollador, quiero que la herramienta imprima un resumen al final de cada ejecución, para poder evaluar rápidamente los resultados sin necesidad de abrir el archivo de reporte.
- **Criterios de aceptación**:
  - El resumen incluye: total de assets analizados, total de assets no utilizados encontrados, tamaño combinado de los archivos no utilizados (en formato legible) y la ruta completa al archivo de reporte generado.
  - El resumen se imprime siempre, incluso si no se encuentran assets no utilizados.
  - El resumen se imprime después de que el archivo CSV haya sido escrito con éxito.

### 10.9 Gestionar la limitación de tasa de la API de forma controlada

- **ID**: ID-009
- **Descripción**: Como desarrollador, quiero que la herramienta reintente automáticamente las solicitudes cuando la API de Contentful devuelva una respuesta 429, para que las auditorías prolongadas no se interrumpan por los límites transitorios de la API.
- **Criterios de aceptación**:
  - Cuando se recibe una respuesta 429, la herramienta espera la duración especificada en el encabezado `X-Contentful-RateLimit-Reset` (o usa retroceso exponencial con variación aleatoria si el encabezado no está presente) antes de reintentar.
  - La herramienta reintenta hasta un número máximo configurable de veces (con valor predeterminado de 5) antes de registrar un fallo permanente para esa solicitud y continuar.
  - Los reintentos por limitación de tasa se registran a nivel de advertencia (warning), incluyendo la duración de espera y el número de intento.

### 10.10 Omitir y registrar errores individuales de recuperación de assets o entradas

- **ID**: ID-010
- **Descripción**: Como desarrollador, quiero que la herramienta continúe procesando cuando falla la recuperación de un asset o entrada individual (por ejemplo, un error 404 para una entrada eliminada), para que un registro defectuoso no interrumpa la auditoría completa.
- **Criterios de aceptación**:
  - Cuando se recibe un error que no es de limitación de tasa para un asset o entrada específico, la herramienta registra el error con el ID del asset o entrada y el código de estado HTTP, y luego continúa con el siguiente elemento.
  - Los assets que no pudieron evaluarse completamente por errores se excluyen de la lista de assets no utilizados y se listan en una sección separada de "omitidos" en el resumen de consola.
  - El conteo total de elementos omitidos se incluye en el resumen de la ejecución.

### 10.11 Configurar la herramienta mediante variables de entorno

- **ID**: ID-011
- **Descripción**: Como desarrollador, quiero que todas las credenciales de Contentful y los parámetros de ejecución sean configurables mediante variables de entorno, para que la herramienta pueda usarse de forma segura en diferentes espacios y entornos sin modificar el código fuente.
- **Criterios de aceptación**:
  - La herramienta lee `MANAGEMENT_TOKEN`, `SPACE_ID` y `ENVIRONMENT` desde variables de entorno mediante `python-dotenv`.
  - Si `MANAGEMENT_TOKEN` o `SPACE_ID` no están definidas, la herramienta lanza un `EnvironmentError` claro con un mensaje que indica la variable faltante.
  - El archivo `env_example` en la raíz del repositorio documenta todas las variables de entorno compatibles con una breve descripción de cada una.
  - Ningún valor de credencial aparece en los logs, trazas de error ni en el reporte de salida.

### 10.12 Ejecutar la auditoría desde el notebook de Jupyter

- **ID**: ID-012
- **Descripción**: Como desarrollador, quiero poder ejecutar el flujo completo de auditoría desde el notebook de Jupyter, para disponer de un entorno interactivo de exploración y poder demostrar la herramienta sin usar la línea de comandos.
- **Criterios de aceptación**:
  - El notebook importa `ContentfulManager` desde `src/sources/contentful/handle_contentful.py` sin errores de importación.
  - La ejecución secuencial de todas las celdas produce el mismo reporte que ejecutar el script equivalente.
  - El notebook incluye celdas de texto en Markdown que explican cada paso.
  - El notebook no almacena ningún valor de credencial en las salidas de sus celdas.
