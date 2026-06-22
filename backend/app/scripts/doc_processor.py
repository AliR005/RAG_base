from typing import List

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


# 📄 Итерация по всем блокам
def iter_block_items(parent):
    for child in parent.element.body:
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


# 📊 Таблицы в markdown
def table_to_markdown(table):
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append("| " + " | ".join(cells) + " |")
    if len(rows) > 1:
        header = rows[0]
        separator = "| " + " | ".join(["---"] * len(table.columns)) + " |"
        return "\n".join([header, separator] + rows[1:])
    else:
        return "\n".join(rows)


# 🧩 Основная логика
def split_docx_with_tables(file_path, marker="##"):
    doc = Document(file_path)
    chunks = []
    current_chunk = []
    header = None
    first_found = False  # индикатор первого заголовка

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if marker in text:
                if first_found and current_chunk:
                    chunks.append(
                        {
                            "title": header,
                            "content": "\n".join(current_chunk).strip(),
                        }
                    )
                header = text
                current_chunk = []
                first_found = True
            elif first_found:
                current_chunk.append(text)
        elif isinstance(block, Table) and first_found:
            table_text = table_to_markdown(block)
            current_chunk.append(table_text)

    # сохранить последний чанк (если это не первый)
    if first_found and header and current_chunk:
        chunks.append(
            {"title": header, "content": "\n".join(current_chunk).strip()}
        )

    return chunks


def read_docx_and_split(file_path: str) -> List[str]:
    chunks = split_docx_with_tables(file_path)
    return [f"{chunk['title']}\n{chunk['content']}" for chunk in chunks]
