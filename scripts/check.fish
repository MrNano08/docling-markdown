#!/usr/bin/env fish

set project_dir (realpath (dirname (status filename))/..)
cd $project_dir

if not test -x .venv/bin/python
    echo "No existe el entorno .venv."
    exit 1
end

.venv/bin/python -c "
import gradio
import docling
import markitdown
import torch
from docling.document_converter import DocumentConverter

print('Gradio:', gradio.__version__)
print('Docling importado correctamente')
print('MarkItDown importado correctamente')
print('PyTorch:', torch.__version__)
print('CUDA disponible:', torch.cuda.is_available())
print('DocumentConverter:', DocumentConverter.__name__)
"
