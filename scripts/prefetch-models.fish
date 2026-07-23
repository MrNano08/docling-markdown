#!/usr/bin/env fish

set project_dir (realpath (dirname (status filename))/..)
cd $project_dir

if not test -x .venv/bin/docling-tools
    echo "No se encontró Docling en .venv."
    echo "Ejecuta primero: fish scripts/install-cachyos.fish"
    exit 1
end

set -x DOCLING_ARTIFACTS_PATH "$HOME/.cache/docling/models"

echo "Descargando modelos de Docling..."
.venv/bin/docling-tools models download

echo
echo "Modelos descargados en:"
echo "$DOCLING_ARTIFACTS_PATH"
