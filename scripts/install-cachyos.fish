#!/usr/bin/env fish

set -e

set project_dir (realpath (dirname (status filename))/..)
cd $project_dir

echo "Instalando herramientas del sistema..."
sudo pacman -S --needed git uv unzip libglvnd glib2

echo "Instalando Python 3.12..."
uv python install 3.12

echo "Creando un entorno separado..."
rm -rf .venv
uv venv --python 3.12 .venv

echo "Instalando PyTorch para CPU..."
uv pip install \
    --python .venv/bin/python \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchvision

echo "Instalando Docling, Gradio y MarkItDown..."
uv pip install \
    --python .venv/bin/python \
    -r requirements.txt

echo
echo "Instalación terminada."
echo "Siguiente paso opcional:"
echo "fish scripts/prefetch-models.fish"
echo
echo "Para ejecutar:"
echo "fish scripts/run.fish"
