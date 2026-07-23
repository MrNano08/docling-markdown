#!/usr/bin/env fish

set project_dir (realpath (dirname (status filename))/..)
cd $project_dir

if not test -x .venv/bin/python
    echo "No existe .venv."
    echo "Ejecuta primero: fish scripts/install-cachyos.fish"
    exit 1
end

set -x GRADIO_SERVER_NAME "0.0.0.0"
set -x GRADIO_SERVER_PORT "7860"
set -x GRADIO_ANALYTICS_ENABLED "False"
set -x DOCLING_DEVICE "cpu"
set -x DOCLING_NUM_THREADS "2"
set -x OMP_NUM_THREADS "2"
set -x MKL_NUM_THREADS "2"

exec .venv/bin/python app.py
