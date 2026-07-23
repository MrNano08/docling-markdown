from converter_service import remove_empty_markdown_tables, safe_stem


def test_remove_empty_table():
    source = """
Texto anterior.

|   |   |
|---|---|
|   |   |

Texto posterior.
"""
    result = remove_empty_markdown_tables(source)

    assert "Texto anterior." in result
    assert "Texto posterior." in result
    assert "|---|---|" not in result


def test_keep_non_empty_table():
    source = """
| Nombre | Edad |
|---|---|
| Ana | 20 |
"""
    result = remove_empty_markdown_tables(source)

    assert "| Nombre | Edad |" in result
    assert "| Ana | 20 |" in result


def test_safe_stem():
    assert safe_stem("Mi archivo (1).pdf") == "Mi_archivo_1"
