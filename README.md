---
title: Convertir documento a Markdown
emoji: 📄
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
suggested_hardware: cpu-basic
short_description: Convierte PDF con análisis de tablas y otros documentos a Markdown.
---

# Convertir documento a Markdown — interfaz pastel

Aplicación separada para convertir documentos sin modificar la versión anterior.

## Arquitectura

```text
PDF
 └── Docling
      ├── orden de lectura
      ├── estructura de tablas
      ├── OCR no forzado
      └── Markdown

DOCX / PPTX / XLSX / HTML / TXT / otros
 └── MarkItDown
      └── Markdown
```

## Perfiles de PDF

### Estructurado recomendado

- OCR activado, pero no forzado a toda la página.
- TableFormer en modo preciso.
- Emparejamiento de celdas activado.

### Tablas complejas

- OCR activado, pero no forzado.
- TableFormer en modo preciso.
- Emparejamiento de celdas desactivado.
- Puede mejorar documentos donde varias columnas aparecen mezcladas.

### PDF digital rápido

- OCR desactivado.
- Mantiene el análisis preciso de tablas.
- Adecuado cuando todo el texto del PDF es seleccionable.

## Límites predeterminados

- 100 MB por archivo.
- 80 páginas por PDF.
- Una conversión simultánea.
- Cola máxima de cinco solicitudes.
- Archivos de salida temporales durante seis horas.

Los límites se encuentran al inicio de `converter_service.py`.

# Desarrollo local en CachyOS

## 1. Extraer el proyecto

```fish
cd ~/Descargas
unzip docling-markdown-webapp.zip
cd docling-markdown-webapp
```

## 2. Instalar

```fish
fish scripts/install-cachyos.fish
```

## 3. Descargar los modelos antes de probar

```fish
fish scripts/prefetch-models.fish
```

Este paso es opcional. Si se omite, Docling descargará los modelos durante la
primera conversión.

## 4. Revisar la instalación

```fish
fish scripts/check.fish
```

## 5. Ejecutar

```fish
fish scripts/run.fish
```

Abre:

```text
http://127.0.0.1:7860
```

# Instalación manual en CachyOS

```fish
sudo pacman -S --needed git uv unzip libglvnd glib2

uv python install 3.12
uv venv --python 3.12 .venv

uv pip install \
  --python .venv/bin/python \
  --index-url https://download.pytorch.org/whl/cpu \
  torch torchvision

uv pip install \
  --python .venv/bin/python \
  -r requirements.txt
```

Ejecutar:

```fish
.venv/bin/python app.py
```

# Publicar como un Space nuevo

## Método por la interfaz web

1. Crea un Space nuevo.
2. Selecciona **Docker** como SDK.
3. Usa un nombre distinto al Space anterior.
4. Sube todos los archivos de esta carpeta.
5. Espera a que termine `Building`.
6. Abre la pestaña de la aplicación.

No subas el archivo ZIP dentro del Space. Debes subir su contenido.

## Método con Git desde CachyOS

Autentícate:

```fish
uvx hf auth login
```

Clona el Space vacío:

```fish
git clone https://huggingface.co/spaces/TU_USUARIO/TU_SPACE
cd TU_SPACE
```

Copia los archivos del proyecto:

```fish
cp -r ~/Descargas/docling-markdown-webapp/. .
```

Publica:

```fish
git add .
git commit -m "Agregar webapp Docling"
git push
```

# Primera construcción del Docker Space

El `Dockerfile` instala PyTorch para CPU y descarga previamente los modelos de
Docling. Por ello, la primera construcción puede tardar bastante más que una
aplicación Gradio pequeña.

Si la construcción falla específicamente durante:

```dockerfile
RUN docling-tools models download
```

puedes comentar esa instrucción. El Space construirá más rápido, pero la
primera conversión descargará los modelos en tiempo de ejecución.

# Privacidad

La aplicación solo acepta archivos subidos. No habilita conversión desde URL ni
servicios remotos de análisis. Los documentos se procesan dentro del contenedor.

En un Space público:

- el código es público;
- la aplicación también es pública;
- cualquier persona con acceso puede subir documentos.

No uses un Space público para documentos confidenciales.

# Archivos principales

```text
.
├── app.py
├── converter_service.py
├── requirements.txt
├── Dockerfile
├── README.md
├── .gitignore
├── .dockerignore
├── scripts/
│   ├── install-cachyos.fish
│   ├── prefetch-models.fish
│   ├── check.fish
│   └── run.fish
└── tests/
    └── test_cleanup.py
```


## Interfaz ligera

Esta variante conserva exactamente el mismo motor de conversión y modifica
únicamente la presentación visual.

- No utiliza imágenes de fondo.
- No descarga fuentes externas.
- No agrega bibliotecas JavaScript.
- No agrega dependencias Python.
- Usa CSS responsivo y compatible con los modos claro y oscuro de Gradio.
- Respeta la preferencia del sistema para reducir animaciones.


## Cambios de esta interfaz

- Fondo blanco.
- Paleta pastel en tonos lavanda, durazno, menta, azul y rosa.
- Textos simplificados para usuarios sin conocimientos técnicos.
- Opciones técnicas ocultas dentro de “Opciones adicionales”.
- Diseño adaptable para computadoras, tabletas y celulares.
- Botones de ancho completo en pantallas pequeñas.
- Sin imágenes, fuentes externas ni nuevas dependencias.
