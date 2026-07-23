from __future__ import annotations

from pathlib import Path
import os
import shutil
import tempfile
import time
import traceback
import uuid

import gradio as gr

from converter_service import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    MAX_PDF_PAGES,
    convert_document,
    safe_stem,
)


OUTPUT_TTL_SECONDS = 6 * 60 * 60
OUTPUT_ROOT = Path(tempfile.gettempdir()) / "docling_markdown_webapp"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def cleanup_old_outputs() -> None:
    now = time.time()

    for item in OUTPUT_ROOT.iterdir():
        try:
            if now - item.stat().st_mtime <= OUTPUT_TTL_SECONDS:
                continue

            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)

        except OSError:
            continue


def convert_from_ui(
    file_path: str | None,
    pdf_profile: str,
    language_key: str,
    clean_empty_tables: bool,
):
    cleanup_old_outputs()

    if not file_path:
        raise gr.Error("Primero selecciona un documento.")

    source = Path(file_path)
    job_directory = OUTPUT_ROOT / uuid.uuid4().hex
    job_directory.mkdir(parents=True, exist_ok=False)

    try:
        report = convert_document(
            source=source,
            pdf_profile=pdf_profile,
            language_key=language_key,
            clean_empty_tables=clean_empty_tables,
        )

        output_name = f"{safe_stem(source.name)}.md"
        output_path = job_directory / output_name
        output_path.write_text(report.markdown, encoding="utf-8")

        status = f"""
        <div class="success-message">
            <div class="success-mark">✓</div>
            <div class="success-copy">
                <strong>Documento convertido</strong>
                <span>{source.name}</span>
                <div class="success-details">
                    <span>{report.engine}</span>
                    <span>{report.elapsed_seconds:.1f} s</span>
                    {
                        f"<span>{report.page_count} páginas</span>"
                        if report.page_count is not None
                        else ""
                    }
                </div>
            </div>
        </div>
        """

        return (
            report.markdown,
            report.markdown,
            str(output_path),
            status,
        )

    except gr.Error:
        raise
    except Exception as error:
        traceback.print_exc()
        shutil.rmtree(job_directory, ignore_errors=True)
        raise gr.Error(str(error))


FORCE_LIGHT_HEAD = """
<script>
(() => {
    const applyLightMode = () => {
        document.documentElement.classList.remove("dark");
        document.body.classList.remove("dark");
        document.documentElement.style.colorScheme = "light";
        localStorage.setItem("theme", "light");
    };

    applyLightMode();

    new MutationObserver(applyLightMode).observe(
        document.documentElement,
        {attributes: true, attributeFilter: ["class"]}
    );
})();
</script>
"""


CSS = r"""
:root,
.dark {
    color-scheme: light !important;

    --page: #ffffff;
    --surface: #ffffff;
    --text: #2f3138;
    --muted: #777983;
    --line: #ebe8ef;

    --lilac-50: #faf8ff;
    --lilac-100: #f0ebff;
    --lilac-200: #dfd4ff;
    --lilac-500: #8b74d7;
    --lilac-600: #715bbd;

    --peach-100: #fff0e7;
    --peach-500: #d98a61;

    --mint-100: #e8f8f1;
    --mint-500: #4c9b7c;

    --sky-100: #eaf5ff;
    --sky-500: #5c8eb8;

    --rose-100: #fdebf2;
    --rose-500: #b86886;

    --shadow: 0 14px 38px rgba(49, 48, 60, 0.065);
    --radius-xl: 24px;
    --radius-lg: 18px;
    --radius-md: 14px;
}

html,
body {
    width: 100%;
    min-height: 100%;
    margin: 0;
    background: var(--page) !important;
    color: var(--text) !important;
}

body,
.gradio-container,
.gradio-container * {
    color-scheme: light !important;
}

.gradio-container {
    width: 100% !important;
    max-width: none !important;
    min-height: 100vh !important;
    margin: 0 !important;
    padding: 26px 34px 46px !important;
    background: var(--page) !important;
    color: var(--text) !important;

    --body-background-fill: #ffffff !important;
    --body-text-color: #2f3138 !important;
    --background-fill-primary: #ffffff !important;
    --background-fill-secondary: #ffffff !important;
    --block-background-fill: #ffffff !important;
    --block-label-background-fill: #ffffff !important;
    --block-border-color: #ebe8ef !important;
    --input-background-fill: #ffffff !important;
    --input-border-color: #ded9e7 !important;
    --input-placeholder-color: #9a98a1 !important;
    --button-secondary-background-fill: #f0ebff !important;
    --button-secondary-background-fill-hover: #e7dfff !important;
    --button-secondary-text-color: #715bbd !important;
    --checkbox-background-color: #ffffff !important;
    --checkbox-border-color: #cfc7df !important;
    --panel-background-fill: #ffffff !important;
}

.main-layout {
    display: flex;
    width: 100%;
    flex-direction: column;
    gap: 18px;
}

.header-card {
    width: 100%;
    padding: 34px 38px;
    border: 1px solid var(--line);
    border-radius: var(--radius-xl);
    background:
        linear-gradient(
            110deg,
            var(--lilac-100) 0%,
            #ffffff 48%,
            var(--sky-100) 100%
        );
    box-shadow: var(--shadow);
}

.header-card h1 {
    max-width: 880px;
    margin: 0;
    color: var(--text);
    font-size: clamp(2rem, 4vw, 3.2rem);
    font-weight: 790;
    line-height: 1.08;
    letter-spacing: -0.045em;
}

.header-card p {
    max-width: 790px;
    margin: 15px 0 0;
    color: #696b74;
    font-size: 1rem;
    line-height: 1.68;
}

.card {
    min-height: 100%;
    padding: 23px !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-lg) !important;
    background: #ffffff !important;
    box-shadow: 0 10px 30px rgba(49, 48, 60, 0.05);
}

.card-heading {
    margin-bottom: 15px;
}

.card-heading h2 {
    margin: 0;
    color: var(--text);
    font-size: 1.08rem;
    font-weight: 760;
    letter-spacing: -0.02em;
}

.card-heading p {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 0.88rem;
    line-height: 1.52;
}

.upload-zone {
    min-height: 0 !important;
    background: #ffffff !important;
}

/* Solo estiliza el botón real de carga. No altera la vista previa del archivo. */
.upload-zone button[aria-dropeffect="copy"] {
    width: 100% !important;
    min-height: 245px !important;
    border: 2px dashed var(--lilac-200) !important;
    border-radius: var(--radius-md) !important;
    background: #ffffff !important;
    color: var(--text) !important;
    box-shadow: none !important;
    overflow: hidden !important;
    transition:
        border-color 150ms ease,
        background 150ms ease;
}

.upload-zone button[aria-dropeffect="copy"]:hover {
    border-color: var(--lilac-500) !important;
    background: var(--lilac-50) !important;
}

/* Contenedor interno del mensaje de carga de Gradio. */
.upload-zone button[aria-dropeffect="copy"] > .wrap,
.upload-zone button[aria-dropeffect="copy"] .wrap.svelte-1vmd51o {
    width: 100% !important;
    min-height: 245px !important;
    margin: 0 !important;
    padding: 24px 18px !important;
    background: transparent !important;
    color: var(--text) !important;
}

/* Evita que el selector genérico [class*="wrap"] agrande el icono. */
.upload-zone button[aria-dropeffect="copy"] .icon-wrap {
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    min-height: 34px !important;
    margin: 0 0 12px !important;
    padding: 0 !important;
    background: transparent !important;
}

.upload-zone button[aria-dropeffect="copy"] .icon-wrap svg {
    display: block !important;
    width: 34px !important;
    height: 34px !important;
    color: var(--lilac-500) !important;
    fill: none !important;
    stroke: currentColor !important;
}

.upload-zone button[aria-dropeffect="copy"] p,
.upload-zone button[aria-dropeffect="copy"] span {
    max-width: 100% !important;
    color: var(--muted) !important;
    text-align: center !important;
}

/* El input nativo sigue disponible para Gradio, pero no ocupa espacio visual. */
.upload-zone input[type="file"] {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: -1px !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    clip-path: inset(50%) !important;
    white-space: nowrap !important;
    border: 0 !important;
    opacity: 0 !important;
}

/* Vista previa posterior a la carga: nombre, extensión y tamaño visibles. */
.upload-zone:has(.file-preview-holder) {
    min-height: 0 !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}

.upload-zone .file-preview-holder {
    width: 100% !important;
    max-width: none !important;
    max-height: none !important;
    overflow: visible !important;
    padding: 8px 46px 8px 10px !important;
    border: 1px solid var(--lilac-200) !important;
    border-radius: 12px !important;
    background: #ffffff !important;
}

.upload-zone table.file-preview {
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    table-layout: fixed !important;
    background: #ffffff !important;
}

.upload-zone table.file-preview tbody,
.upload-zone table.file-preview tr.file {
    width: 100% !important;
    background: #ffffff !important;
}

.upload-zone table.file-preview tr.file {
    display: flex !important;
    min-height: 42px !important;
    align-items: center !important;
}

.upload-zone table.file-preview td.filename {
    display: flex !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
    align-items: center !important;
    padding: 8px 10px !important;
    color: var(--text) !important;
    line-height: 1.35 !important;
}

.upload-zone table.file-preview .stem {
    min-width: 0 !important;
    overflow: hidden !important;
    color: var(--text) !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}

.upload-zone table.file-preview .ext {
    flex: 0 0 auto !important;
    color: var(--text) !important;
    white-space: nowrap !important;
}

.upload-zone table.file-preview td.download {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: max-content !important;
    padding: 8px 4px 8px 10px !important;
    color: var(--sky-500) !important;
    text-align: right !important;
    white-space: nowrap !important;
}

/* Mantiene el botón de limpiar en la esquina superior derecha. */
.upload-zone .icon-button-wrapper {
    top: 8px !important;
    right: 8px !important;
    left: auto !important;
    width: auto !important;
    max-width: max-content !important;
    margin: 0 !important;
    padding: 2px !important;
    background: #ffffff !important;
}

.upload-zone .icon-button-wrapper button {
    width: 28px !important;
    min-width: 28px !important;
    height: 28px !important;
    min-height: 28px !important;
    margin: 0 !important;
    padding: 5px !important;
    border-radius: 8px !important;
    background: var(--lilac-100) !important;
    color: var(--lilac-600) !important;
}

.upload-zone .icon-button-wrapper button svg {
    width: 16px !important;
    height: 16px !important;
    color: currentColor !important;
}

.settings-accordion {
    overflow: hidden;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-lg) !important;
    background: #ffffff !important;
    box-shadow: none !important;
}

.settings-accordion,
.settings-accordion > div,
.settings-accordion .wrap,
.settings-accordion .form,
.settings-accordion .label-wrap {
    background: #ffffff !important;
    color: var(--text) !important;
}

.settings-accordion > .label-wrap {
    min-height: 58px;
    padding: 0 18px !important;
    border: 0 !important;
    border-bottom: 1px solid transparent !important;
    background: #ffffff !important;
    color: var(--text) !important;
    font-weight: 740 !important;
}

.settings-accordion[open] > .label-wrap {
    border-bottom-color: var(--line) !important;
    background: var(--peach-100) !important;
}

.settings-accordion svg {
    color: var(--peach-500) !important;
}

.settings-accordion label,
.settings-accordion span,
.settings-accordion p {
    color: var(--text) !important;
}

.settings-accordion input,
.settings-accordion textarea,
.settings-accordion select {
    border-color: #ded9e7 !important;
    background: #ffffff !important;
    color: var(--text) !important;
}

.settings-accordion [role="radiogroup"],
.settings-accordion [role="listbox"],
.settings-accordion .secondary-wrap {
    background: #ffffff !important;
}

.settings-note {
    padding: 13px 14px;
    border: 1px solid #cfe9dd;
    border-radius: var(--radius-md);
    background: var(--mint-100);
    color: #5d7168;
    font-size: 0.84rem;
    line-height: 1.52;
}

.settings-note strong {
    color: var(--mint-500);
}

.convert-button {
    width: 100%;
    min-height: 54px !important;
    border: 0 !important;
    border-radius: var(--radius-md) !important;
    background: linear-gradient(
        135deg,
        var(--lilac-500),
        #ad98e8
    ) !important;
    color: #ffffff !important;
    box-shadow: 0 12px 25px rgba(113, 91, 189, 0.19) !important;
    font-size: 1rem !important;
    font-weight: 760 !important;
    transition:
        transform 150ms ease,
        box-shadow 150ms ease;
}

.convert-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 16px 31px rgba(113, 91, 189, 0.24) !important;
}

.convert-button:active {
    transform: translateY(0);
}

.status-area:empty {
    display: none;
}

.success-message {
    display: flex;
    align-items: flex-start;
    gap: 13px;
    padding: 16px;
    border: 1px solid #ccebdd;
    border-radius: var(--radius-md);
    background: var(--mint-100);
}

.success-mark {
    display: grid;
    flex: 0 0 auto;
    place-items: center;
    width: 31px;
    height: 31px;
    border-radius: 999px;
    background: var(--mint-500);
    color: #ffffff;
    font-size: 0.92rem;
    font-weight: 850;
}

.success-copy {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 4px;
}

.success-copy strong {
    color: var(--text);
    font-size: 0.96rem;
}

.success-copy > span {
    overflow: hidden;
    color: #69736f;
    font-size: 0.85rem;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.success-details {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin-top: 7px;
}

.success-details span {
    padding: 5px 8px;
    border: 1px solid rgba(76, 155, 124, 0.14);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.78);
    color: #5b7167;
    font-size: 0.74rem;
    font-weight: 650;
}

.output-card {
    width: 100%;
    padding: 22px !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-lg) !important;
    background: #ffffff !important;
    box-shadow: 0 10px 30px rgba(49, 48, 60, 0.05);
}

.output-title {
    margin-bottom: 13px;
}

.output-title h2 {
    margin: 0;
    color: var(--text);
    font-size: 1.08rem;
    font-weight: 760;
}

.output-title p {
    margin: 5px 0 0;
    color: var(--muted);
    font-size: 0.86rem;
}

.output-tabs,
.output-tabs > div,
.output-tabs .tabitem {
    background: #ffffff !important;
    color: var(--text) !important;
}

.output-tabs {
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
}

.output-tabs .tab-nav {
    padding: 6px 7px 0 !important;
    border-bottom: 1px solid var(--line) !important;
    background: #ffffff !important;
}

.output-tabs .tab-nav button {
    border: 0 !important;
    border-radius: 10px 10px 0 0 !important;
    background: transparent !important;
    color: var(--muted) !important;
    font-weight: 670 !important;
}

.output-tabs .tab-nav button.selected {
    background: var(--rose-100) !important;
    color: var(--rose-500) !important;
}

.markdown-box,
.markdown-box > div,
.markdown-box .wrap,
.markdown-box textarea {
    background: #ffffff !important;
    color: var(--text) !important;
}

.markdown-box textarea {
    min-height: 440px !important;
    padding: 18px !important;
    border: 0 !important;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        Monaco,
        Consolas,
        "Liberation Mono",
        monospace !important;
    font-size: 0.89rem !important;
    line-height: 1.65 !important;
}

.markdown-box button {
    border: 0 !important;
    background: var(--sky-100) !important;
    color: var(--sky-500) !important;
}

.preview-box {
    min-height: 440px;
    padding: 20px !important;
    background: #ffffff !important;
    color: var(--text) !important;
}

.preview-box * {
    color: inherit;
}

.download-button {
    min-height: 48px !important;
    margin-top: 12px !important;
    border: 1px solid #f0cddd !important;
    border-radius: var(--radius-md) !important;
    background: var(--rose-100) !important;
    color: var(--rose-500) !important;
    box-shadow: none !important;
    font-weight: 730 !important;
}

.download-button:hover {
    background: #f8dfe9 !important;
}

footer {
    display: none !important;
}

@media (max-width: 900px) {
    .gradio-container {
        padding: 18px 16px 38px !important;
    }

    .header-card {
        padding: 28px 24px;
    }
}

@media (max-width: 760px) {
    .gradio-container {
        padding: 10px 9px 30px !important;
    }

    .main-layout {
        gap: 13px;
    }

    .header-card {
        padding: 24px 19px;
        border-radius: 19px;
    }

    .header-card h1 {
        font-size: 1.92rem;
        line-height: 1.1;
    }

    .header-card p {
        font-size: 0.92rem;
        line-height: 1.58;
    }

    .card,
    .output-card {
        padding: 16px !important;
        border-radius: 16px !important;
    }

    .upload-zone {
        min-height: 0 !important;
    }

    .upload-zone button[aria-dropeffect="copy"],
    .upload-zone button[aria-dropeffect="copy"] > .wrap,
    .upload-zone button[aria-dropeffect="copy"] .wrap.svelte-1vmd51o {
        min-height: 185px !important;
    }

    .convert-button {
        min-height: 52px !important;
    }

    .markdown-box textarea,
    .preview-box {
        min-height: 335px !important;
    }

    .success-copy > span {
        white-space: normal;
    }
}

@media (max-width: 460px) {
    .header-card h1 {
        font-size: 1.68rem;
    }

    .header-card {
        padding: 21px 17px;
    }

    .card,
    .output-card {
        padding: 14px !important;
    }

    .output-tabs .tab-nav button {
        padding-left: 8px !important;
        padding-right: 8px !important;
        font-size: 0.79rem !important;
    }
}



/* =========================================================
   CORRECCIONES DE COMPONENTES GRADIO
   ========================================================= */

/* Radio: elimina el gris y hace visible la opción seleccionada. */
.settings-accordion [role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 10px !important;
    width: 100% !important;
    background: #ffffff !important;
}

.settings-accordion [role="radiogroup"] > label,
.settings-accordion label:has(input[type="radio"]) {
    display: flex !important;
    min-height: 46px !important;
    align-items: center !important;
    gap: 9px !important;
    padding: 10px 12px !important;
    border: 1px solid #ded7ee !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    color: var(--text) !important;
    box-shadow: none !important;
    cursor: pointer !important;
    transition:
        border-color 140ms ease,
        background 140ms ease,
        box-shadow 140ms ease !important;
}

.settings-accordion [role="radiogroup"] > label:hover,
.settings-accordion label:has(input[type="radio"]):hover {
    border-color: var(--lilac-500) !important;
    background: var(--lilac-50) !important;
}

.settings-accordion [role="radiogroup"] > label:has(input[type="radio"]:checked),
.settings-accordion label:has(input[type="radio"]:checked) {
    border-color: var(--lilac-500) !important;
    background: var(--lilac-100) !important;
    color: var(--lilac-600) !important;
    box-shadow: 0 0 0 2px rgba(139, 116, 215, 0.13) !important;
}

.settings-accordion input[type="radio"] {
    flex: 0 0 auto !important;
    width: 17px !important;
    height: 17px !important;
    margin: 0 !important;
    accent-color: var(--lilac-500) !important;
}

.settings-accordion label:has(input[type="radio"]:checked) span {
    color: var(--lilac-600) !important;
    font-weight: 720 !important;
}

/* Checkbox: estado seleccionado visible. */
.settings-accordion input[type="checkbox"] {
    width: 18px !important;
    height: 18px !important;
    accent-color: var(--mint-500) !important;
}

.settings-accordion label:has(input[type="checkbox"]:checked) {
    color: var(--mint-500) !important;
}

/* Dropdown y paneles: siempre blancos, nunca grises. */
.settings-accordion .secondary-wrap,
.settings-accordion [role="listbox"],
.settings-accordion [role="combobox"],
.settings-accordion fieldset,
.settings-accordion .block,
.settings-accordion .container,
.settings-accordion .wrap,
.settings-accordion .form {
    background: #ffffff !important;
    color: var(--text) !important;
    box-shadow: none !important;
}

.settings-accordion [role="combobox"] {
    border: 1px solid #ded7ee !important;
    border-radius: 12px !important;
}

/* Elimina fondos neutros de botones secundarios dentro de ajustes. */
.settings-accordion button:not(.convert-button) {
    background: #ffffff !important;
    color: var(--text) !important;
    box-shadow: none !important;
}

/* En móvil las opciones se apilan y el cargador conserva todo su ancho. */
@media (max-width: 760px) {
    .settings-accordion [role="radiogroup"] {
        grid-template-columns: 1fr !important;
    }

    .upload-zone button[aria-dropeffect="copy"],
    .upload-zone button[aria-dropeffect="copy"] > .wrap,
    .upload-zone button[aria-dropeffect="copy"] .wrap.svelte-1vmd51o {
        min-height: 185px !important;
    }

    .upload-zone button[aria-dropeffect="copy"] > .wrap,
    .upload-zone button[aria-dropeffect="copy"] .wrap.svelte-1vmd51o {
        padding: 20px 14px !important;
    }

    .upload-zone .file-preview-holder {
        padding-right: 42px !important;
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation: none !important;
        scroll-behavior: auto !important;
        transition: none !important;
    }
}
"""


with gr.Blocks(
    title="Convertir documento a Markdown",
    theme=gr.themes.Base(),
    css=CSS,
    head=FORCE_LIGHT_HEAD,
) as demo:
    with gr.Column(elem_classes=["main-layout"]):
        gr.HTML(
            """
            <section class="header-card">
                <h1>Convierte documentos a Markdown</h1>
                <p>
                    Selecciona un archivo, conviértelo y descarga el resultado
                    en formato .md.
                </p>
            </section>
            """
        )

        with gr.Row():
            with gr.Column(
                scale=7,
                min_width=330,
                elem_classes=["card"],
            ):
                gr.HTML(
                    """
                    <div class="card-heading">
                        <h2>Selecciona el documento</h2>
                        <p>
                            Arrastra el archivo o presiónalo para buscarlo en tu
                            equipo.
                        </p>
                    </div>
                    """
                )

                file_input = gr.File(
                    label="Documento",
                    show_label=False,
                    file_count="single",
                    type="filepath",
                    file_types=sorted(ALLOWED_EXTENSIONS),
                    elem_classes=["upload-zone"],
                )

            with gr.Column(
                scale=5,
                min_width=300,
            ):
                with gr.Accordion(
                    "Ajustes del PDF",
                    open=False,
                    elem_classes=["settings-accordion"],
                ):
                    pdf_profile_input = gr.Radio(
                        choices=[
                            (
                                "Recomendado",
                                "recommended",
                            ),
                            (
                                "Mejorar tablas difíciles",
                                "complex_tables",
                            ),
                            (
                                "Conversión rápida",
                                "digital_fast",
                            ),
                        ],
                        value="recommended",
                        label="Tipo de procesamiento",
                    )

                    language_input = gr.Dropdown(
                        choices=[
                            ("Español e inglés", "es_en"),
                            ("Español", "es"),
                            ("Inglés", "en"),
                        ],
                        value="es_en",
                        label="Idioma del documento",
                        allow_custom_value=False,
                        filterable=False,
                    )

                    clean_tables_input = gr.Checkbox(
                        value=True,
                        label="Quitar tablas completamente vacías",
                    )

                    gr.HTML(
                        """
                        <div class="settings-note">
                            <strong>Recomendado</strong> funciona bien en la
                            mayoría de documentos. Usa “Mejorar tablas
                            difíciles” cuando las columnas queden mezcladas.
                        </div>
                        """
                    )

                convert_button = gr.Button(
                    "Convertir documento",
                    variant="primary",
                    elem_classes=["convert-button"],
                )

        status_output = gr.HTML(
            value="",
            elem_classes=["status-area"],
        )

        with gr.Column(elem_classes=["output-card"]):
            gr.HTML(
                """
                <div class="output-title">
                    <h2>Resultado</h2>
                    <p>
                        Copia el texto, revisa la vista previa o descarga el
                        archivo.
                    </p>
                </div>
                """
            )

            with gr.Tabs(elem_classes=["output-tabs"]):
                with gr.Tab("Markdown"):
                    raw_output = gr.Textbox(
                        label="",
                        lines=24,
                        max_lines=50,
                        buttons=["copy"],
                        elem_classes=["markdown-box"],
                    )

                with gr.Tab("Vista previa"):
                    preview_output = gr.Markdown(
                        elem_classes=["preview-box"],
                    )

            download_output = gr.DownloadButton(
                label="Descargar archivo .md",
                elem_classes=["download-button"],
            )

    convert_button.click(
        fn=convert_from_ui,
        inputs=[
            file_input,
            pdf_profile_input,
            language_input,
            clean_tables_input,
        ],
        outputs=[
            raw_output,
            preview_output,
            download_output,
            status_output,
        ],
        api_name="convert",
    )


if __name__ == "__main__":
    demo.queue(
        default_concurrency_limit=1,
        max_size=5,
    ).launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        show_error=True,
    )
