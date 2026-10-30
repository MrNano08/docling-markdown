---
title: Documentos a Markdown
emoji: 📄
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
suggested_hardware: cpu-basic
short_description: Convierte archivos PDF y otros documentos a Markdown desde una interfaz web.
---

# Docling Markdown Converter

**Conversor de documentos a Markdown con una interfaz web en español.**

Permite cargar un documento, procesarlo, consultar el Markdown generado, revisar una vista previa y descargar el archivo `.md`. La aplicación combina **Docling** para archivos PDF con **MarkItDown** para otros formatos y ofrece controles de OCR y análisis de tablas.

> Este proyecto es una interfaz e integración de herramientas existentes. Los motores de conversión pertenecen a sus respectivos proyectos; la precisión de la salida depende del archivo, del formato y de los modelos utilizados.

## Funcionalidades

- Conversión de un archivo por solicitud, con salida Markdown descargable.
- **PDF con Docling:** extracción estructurada, reconocimiento óptico de caracteres (OCR) y análisis de tablas.
- **Otros formatos con MarkItDown:** DOCX, PPTX, XLSX, XLS, HTML, HTM, CSV, JSON, XML, TXT, MD, EPUB y ZIP (sujetos al soporte efectivo del conversor instalado).
- Tres perfiles de procesamiento PDF: recomendado, tablas complejas y PDF digital rápido.
- Selección de idiomas OCR: español, inglés o ambos.
- Opción para eliminar tablas Markdown completamente vacías.
- Vista de texto, vista previa renderizada, botón de copia y descarga.
- Interfaz responsive creada con **Gradio** y CSS propio.

## Perfiles de PDF

| Perfil | OCR | Procesamiento de tablas | Uso previsto |
| --- | --- | --- | --- |
| **Recomendado** | Activado, sin forzar OCR de página completa | TableFormer preciso con emparejamiento de celdas | PDF general, incluidas tablas |
| **Tablas complejas** | Activado, sin forzar OCR de página completa | TableFormer preciso sin emparejamiento de celdas | Probar cuando las columnas se mezclan |
| **PDF digital rápido** | Desactivado | TableFormer preciso | Archivos con texto seleccionable |

Los perfiles son alternativas de configuración, no garantías de calidad. Revisa el Markdown de salida antes de utilizarlo en otros sistemas.

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Lenguaje | Python 3.12 |
| Interfaz web | Gradio 6.x, CSS |
| Conversión PDF y OCR | Docling, EasyOCR (mediante extra), TableFormer |
| Conversión de otros formatos | MarkItDown |
| Validación de número de páginas PDF | pypdf |
| Inferencia de modelos en CPU | PyTorch |
| Contenedores y despliegue | Docker; compatible con Hugging Face Spaces (SDK Docker) |
| Instalación local orientada a | CachyOS / Arch Linux y shell Fish |

Las versiones admitidas de las bibliotecas están definidas en [`requirements.txt`](requirements.txt). El proyecto no incluye actualmente un archivo de bloqueo de dependencias que garantice versiones idénticas en cada instalación.

## Arquitectura

```text
Navegador
    |
    v
Gradio (app.py)
    |
    v
Validación y conversión (converter_service.py)
    |                         |
    +-- PDF ----------------> Docling + OCR / TableFormer
    |
    +-- Otros formatos -----> MarkItDown
    |
    v
Markdown (.md) + vista previa + descarga
```

Los archivos de salida se almacenan temporalmente en el servidor. Se intenta eliminar resultados con antigüedad superior a seis horas **al iniciar una conversión posterior**; no existe una tarea de limpieza permanente. Los archivos de carga gestionados por Gradio pueden tener un ciclo de retención diferente.

## Requisitos

- Python **3.12**.
- Espacio en disco y memoria suficientes para PyTorch y los modelos de Docling.
- Acceso a Internet durante la instalación y, si los modelos no están descargados, durante su primera obtención.
- En CachyOS: `fish`, `uv`, bibliotecas gráficas del sistema y herramientas de desarrollo utilizadas por los scripts.

## Instalación local en CachyOS

Clona el repositorio:

```bash
git clone https://github.com/MrNano08/docling-markdown.git
cd docling-markdown
```

Instala las herramientas de sistema necesarias (en CachyOS / Arch Linux):

```bash
sudo pacman -S --needed git uv unzip libglvnd glib2
```

Crea un entorno con Python 3.12 e instala PyTorch en CPU y las dependencias:

```bash
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python \
  --index-url https://download.pytorch.org/whl/cpu torch torchvision
uv pip install --python .venv/bin/python -r requirements.txt
```

Opcionalmente, descarga los modelos antes de abrir la aplicación:

```bash
fish scripts/prefetch-models.fish
```

Comprueba las dependencias:

```bash
fish scripts/check.fish
```

Inicia la aplicación vinculada **solo a tu equipo**:

```bash
env GRADIO_SERVER_NAME=127.0.0.1 GRADIO_SERVER_PORT=7860 .venv/bin/python app.py
```

Abre **http://127.0.0.1:7860**.

> `scripts/run.fish` utiliza `0.0.0.0` y puede hacer accesible la aplicación desde otras interfaces de red. Si solo la necesitas localmente, utiliza el comando con `127.0.0.1` que se muestra arriba.

## Ejecución con Docker

```bash
docker build -t docling-markdown .
docker run --rm -p 127.0.0.1:7860:7860 docling-markdown
```

La imagen se basa en Python 3.12 y ejecuta los modelos en CPU. El `Dockerfile` descarga modelos de Docling durante la construcción; por ello puede requerir tiempo, conexión y espacio adicionales.

## Hugging Face Spaces

El repositorio contiene el encabezado YAML necesario para un Space con **SDK Docker** y puerto **7860**. Al crear el Space, sube el contenido del repositorio y conserva el encabezado YAML del `README.md`.

Un Space **público** permite que otras personas utilicen el conversor. No cargues documentos privados, institucionales o confidenciales en una instancia pública que no controles.

## Límites definidos en el código

| Parámetro | Valor |
| --- | --- |
| Tamaño máximo de archivo | 100 MiB |
| Páginas máximas por PDF | 80 |
| Conversiones simultáneas por proceso | 1 |
| Tamaño máximo de cola | 5 solicitudes |
| Limpieza de resultados antiguos | Umbral de 6 horas, evaluado al iniciar nuevas conversiones |

Estos límites reducen algunos riesgos de uso, pero **no constituyen aislamiento de seguridad**, validación profunda de todos los formatos ni protección completa ante archivos maliciosos.

## Pruebas

El repositorio incluye tres pruebas unitarias en [`tests/test_cleanup.py`](tests/test_cleanup.py): eliminación de tablas vacías, conservación de tablas con contenido y normalización del nombre de archivo.

Con el entorno y las dependencias instalados, puedes ejecutar:

```bash
uv pip install --python .venv/bin/python pytest
.venv/bin/python -m pytest -q
```

La suite actual no comprueba conversiones completas de PDF ni los flujos de la interfaz web. Para validar resultados reales, prueba al menos un PDF digital, uno escaneado, una tabla y un documento Office.

## Estructura

```text
.
├── app.py                    # Interfaz Gradio y descarga
├── converter_service.py      # Validación, perfiles y motores de conversión
├── requirements.txt          # Dependencias Python
├── Dockerfile                 # Construcción para CPU / Spaces
├── scripts/
│   ├── check.fish            # Verificación de dependencias
│   ├── install-cachyos.fish  # Instalación asistida en CachyOS
│   ├── prefetch-models.fish  # Descarga anticipada de modelos
│   └── run.fish              # Ejecución de la interfaz
└── tests/
    └── test_cleanup.py       # Pruebas de utilidades
```

## Seguridad y privacidad

- La interfaz del código entregado **no implementa autenticación propia**. Si se publica en Internet, incorpora controles de acceso y límites acordes con el uso previsto.
- Los documentos subidos se procesan en el equipo o servidor que ejecuta la aplicación; los modelos y bibliotecas pueden requerir descargas durante la preparación.
- Los archivos se validan por extensión y tamaño, pero esa validación **no garantiza** que su contenido sea seguro.
- Evita procesar archivos desconocidos o confidenciales en un servicio público sin aislamiento y una política explícita de retención.
- El procesamiento en CPU y la cola de solicitudes no impiden por completo un consumo elevado de recursos.

## Estado y alcance

Es un conversor web orientado a un archivo por operación. No incorpora cuentas, almacenamiento persistente de documentos, edición colaborativa, procesamiento por lotes ni una API de producto con autenticación.

**Licencia:** el repositorio no incluía un archivo `LICENSE` en la versión revisada. Antes de promoverlo como software reutilizable, conviene seleccionar y documentar una licencia compatible con las dependencias y los componentes utilizados.
