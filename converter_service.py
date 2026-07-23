from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import gc
import re
import threading
import time

from docling.datamodel.accelerator_options import (
    AcceleratorDevice,
    AcceleratorOptions,
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    TableStructureOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from markitdown import MarkItDown
from pypdf import PdfReader


MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 80

PDF_PROFILE_LABELS = {
    "recommended": "Estructurado recomendado",
    "complex_tables": "Tablas complejas",
    "digital_fast": "PDF digital rápido",
}

OCR_LANGUAGE_LABELS = {
    "es_en": "Español + inglés",
    "es": "Español",
    "en": "Inglés",
}

OCR_LANGUAGES = {
    "es_en": ("es", "en"),
    "es": ("es",),
    "en": ("en",),
}

MARKITDOWN_EXTENSIONS = {
    ".docx",
    ".pptx",
    ".xlsx",
    ".xls",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".xml",
    ".txt",
    ".md",
    ".epub",
    ".zip",
}

ALLOWED_EXTENSIONS = {".pdf"} | MARKITDOWN_EXTENSIONS


@dataclass(frozen=True)
class ConversionReport:
    markdown: str
    engine: str
    profile: str
    elapsed_seconds: float
    page_count: int | None


_markitdown = MarkItDown(enable_plugins=False)

_converter_lock = threading.Lock()
_converter_key: tuple[str, tuple[str, ...]] | None = None
_pdf_converter: DocumentConverter | None = None


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = re.sub(r"[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ_-]+", "_", stem)
    return cleaned.strip("_") or "documento"


def validate_source(source: Path) -> None:
    if not source.exists() or not source.is_file():
        raise ValueError("El archivo temporal no está disponible.")

    extension = source.suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Formato no permitido: {extension or 'sin extensión'}."
        )

    size = source.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"El archivo supera el límite de {MAX_FILE_SIZE_MB} MB."
        )


def count_pdf_pages(source: Path) -> int:
    try:
        reader = PdfReader(str(source))

        if reader.is_encrypted:
            try:
                unlocked = reader.decrypt("")
            except Exception as error:
                raise ValueError(
                    "El PDF está cifrado y no pudo abrirse."
                ) from error

            if unlocked == 0:
                raise ValueError(
                    "El PDF requiere contraseña. Esta versión no admite "
                    "documentos protegidos."
                )

        page_count = len(reader.pages)

    except ValueError:
        raise
    except Exception as error:
        raise ValueError(
            "No se pudo leer la estructura del PDF."
        ) from error

    if page_count > MAX_PDF_PAGES:
        raise ValueError(
            f"El PDF tiene {page_count} páginas. El límite configurado es "
            f"{MAX_PDF_PAGES} páginas."
        )

    return page_count


def _build_pdf_converter(
    profile: str,
    languages: tuple[str, ...],
) -> DocumentConverter:
    if profile not in PDF_PROFILE_LABELS:
        raise ValueError("El perfil de PDF no es válido.")

    pipeline_options = PdfPipelineOptions()
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=2,
        device=AcceleratorDevice.CPU,
    )

    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options = TableStructureOptions(
        do_cell_matching=(profile != "complex_tables")
    )
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    if profile == "digital_fast":
        pipeline_options.do_ocr = False
    else:
        pipeline_options.do_ocr = True

        # Docling usa EasyOCR cuando está instalado el extra easyocr.
        # No se fuerza OCR de página completa: el texto digital se conserva.
        pipeline_options.ocr_options.lang = list(languages)

        if hasattr(pipeline_options.ocr_options, "use_gpu"):
            pipeline_options.ocr_options.use_gpu = False

    return DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        },
    )


def get_pdf_converter(
    profile: str,
    languages: tuple[str, ...],
) -> DocumentConverter:
    """
    Conserva únicamente el último convertidor configurado.

    Esto evita mantener varios juegos de modelos en RAM cuando el usuario
    cambia entre perfiles de tabla o idiomas.
    """
    global _converter_key, _pdf_converter

    key = (profile, languages)

    with _converter_lock:
        if _converter_key == key and _pdf_converter is not None:
            return _pdf_converter

        previous = _pdf_converter
        _pdf_converter = _build_pdf_converter(profile, languages)
        _converter_key = key

        del previous
        gc.collect()

        return _pdf_converter


def remove_empty_markdown_tables(markdown: str) -> str:
    """
    Elimina únicamente tablas Markdown cuyos datos están completamente vacíos.

    No modifica tablas que contengan al menos una celda con contenido.
    """
    lines = markdown.splitlines()
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if not line.strip().startswith("|"):
            output.append(line)
            index += 1
            continue

        block: list[str] = []
        while index < len(lines) and lines[index].strip().startswith("|"):
            block.append(lines[index])
            index += 1

        has_separator = any(
            re.fullmatch(
                r"\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*",
                row,
            )
            for row in block
        )

        content_cells: list[str] = []
        for row in block:
            if re.search(r"-{3,}", row):
                continue
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            content_cells.extend(cells)

        has_content = any(content_cells)

        if not (has_separator and not has_content):
            output.extend(block)

    cleaned = "\n".join(output)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    return cleaned.strip()


def convert_document(
    source: Path,
    pdf_profile: str,
    language_key: str,
    clean_empty_tables: bool,
) -> ConversionReport:
    validate_source(source)

    extension = source.suffix.lower()
    started = time.perf_counter()
    page_count: int | None = None

    if extension == ".pdf":
        page_count = count_pdf_pages(source)

        languages = OCR_LANGUAGES.get(language_key)
        if languages is None:
            raise ValueError("El idioma OCR seleccionado no es válido.")

        converter = get_pdf_converter(pdf_profile, languages)
        result = converter.convert(
            source,
            max_num_pages=MAX_PDF_PAGES,
            max_file_size=MAX_FILE_SIZE_BYTES,
        )
        markdown = result.document.export_to_markdown()
        engine = "Docling"
        profile = PDF_PROFILE_LABELS[pdf_profile]

    else:
        result = _markitdown.convert_local(source)
        markdown = result.text_content or ""
        engine = "MarkItDown"
        profile = "Conversión directa"

    markdown = markdown.strip()

    if clean_empty_tables:
        markdown = remove_empty_markdown_tables(markdown)

    if not markdown:
        raise ValueError(
            "La conversión terminó, pero no se encontró texto utilizable."
        )

    elapsed = time.perf_counter() - started

    return ConversionReport(
        markdown=markdown,
        engine=engine,
        profile=profile,
        elapsed_seconds=elapsed,
        page_count=page_count,
    )
