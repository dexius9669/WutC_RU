#!/usr/bin/env python3
"""Сборка статического сайта WutC-RU из мастер-файла Markdown.

Запуск:  python3 build.py
Результат: index.html, magic.html, treasure.html в корне репозитория.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "WutC_Rules.ru.md"

BOOKS = [
    {
        "file": "index.html",
        "title": "Книга 1 — Правила",
        "short": "Книга 1",
        "nav_levels": (2, 3),
    },
    {
        "file": "magic.html",
        "title": "Книга 2 — Магия",
        "short": "Книга 2",
        "nav_levels": (2,),
    },
    {
        "file": "treasure.html",
        "title": "Treasure",
        "short": "Treasure",
        "nav_levels": (2,),
    },
]

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ru" data-bs-theme="light">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Wolves Upon the Coast — перевод на русский: {short}">
    <title>{title} — Wolves Upon the Coast</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Aladin&family=Alegreya:ital,wght@0,400;0,700;1,400;1,700&family=Averia+Serif+Libre:ital,wght@0,300;0,400;0,700;1,300;1,400&family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="assets/style.css" rel="stylesheet">
</head>
<body>
<a class="visually-hidden-focusable" href="#main">К содержанию</a>
<nav class="navbar navbar-expand-md sticky-top wutc-navbar">
    <div class="container-xxl">
        <a class="navbar-brand" href="index.html">WUTC-RU</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#wutcNav"
                aria-controls="wutcNav" aria-expanded="false" aria-label="Переключить навигацию">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="wutcNav">
            <ul class="navbar-nav me-auto">
{nav}
            </ul>
            <button id="themeToggle" class="btn btn-sm wutc-theme-toggle ms-lg-2 mt-2 mt-lg-0"
                    type="button" aria-label="Переключить тему">
                <span class="theme-icon theme-icon-light" aria-hidden="true">&#9788;</span>
                <span class="theme-icon theme-icon-dark" aria-hidden="true">&#9790;</span>
            </button>
        </div>
    </div>
</nav>
<div class="container-xxl wutc-shell">
    <main id="main" class="wutc-content">
{content}
    </main>
    <footer class="wutc-footer">
        <p>Wolves Upon the Coast · перевод на русский:
            <a href="https://t.me/pcspeoplestoo" target="_blank" rel="noopener">@pcspeoplestoo</a>
            · <a href="index.html">Книга 1</a> · <a href="magic.html">Книга 2</a> · <a href="treasure.html">Treasure</a></p>
    </footer>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.S)
        if m:
            return text[m.end():]
    return text


def split_books(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith("# ")]
    if len(starts) != 3:
        raise SystemExit(f"Ожидалось 3 книги (# ...), найдено {len(starts)}")
    chunks = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        chunks.append("".join(lines[start:end]))
    return chunks


def pandoc(markdown: str) -> str:
    proc = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none", "--no-highlight"],
        input=markdown,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit("pandoc завершился с ошибкой")
    return proc.stdout


def toc_entries(soup: BeautifulSoup, levels: tuple[int, ...]) -> list[tuple[int, str, str]]:
    entries = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        level = int(heading.name[1])
        if level not in levels:
            continue
        hid = heading.get("id")
        if not hid:
            continue
        text = heading.get_text(" ", strip=True)
        entries.append((level, hid, text))
    return entries


def add_anchors(soup: BeautifulSoup) -> None:
    for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
        hid = heading.get("id")
        if not hid:
            continue
        anchor = soup.new_tag("a")
        anchor["class"] = "header-anchor"
        anchor["href"] = f"#{hid}"
        anchor["aria-hidden"] = "true"
        anchor["tabindex"] = "-1"
        anchor["title"] = "Ссылка на раздел"
        anchor.string = "#"
        heading.insert(0, anchor)


def extract_subtitle(soup: BeautifulSoup) -> None:
    """Переносит «## Книга N — …» в подзаголовок внутри h1."""
    h1 = soup.find("h1")
    if h1 is None:
        return

    h2s = soup.find_all("h2")
    subtitle = None
    if h2s and re.match(r"^Книга\s+\d", h2s[0].get_text(" ", strip=True)):
        subtitle = h2s[0]

    title = h1.get_text(" ", strip=True)
    h1.clear()
    h1.append(title)
    h1["class"] = h1.get("class", []) + ["text-center"]

    if subtitle is not None:
        sub_id = subtitle.get("id")
        sub_text = subtitle.get_text(" ", strip=True)
        subtitle.decompose()
        span = soup.new_tag("span")
        span["class"] = "wutc-subtitle"
        if sub_id:
            span["id"] = sub_id
        span.string = sub_text
        h1.append(span)


def style_quotes(soup: BeautifulSoup, spec: dict) -> None:
    """Оформляет вступление Книги 1 и эпиграф как wutc-quote."""
    if spec["file"] == "index.html":
        paragraphs = soup.find_all("p")
        texts = [p.get_text(" ", strip=True) for p in paragraphs]
        author_idx = next(
            (i for i, text in enumerate(texts) if text == "Luke Gearing"), None
        )
        if author_idx is not None:
            end_idx = next(
                (
                    i
                    for i, text in enumerate(texts)
                    if i > author_idx and text.startswith("Только для использования")
                ),
                None,
            )
            if end_idx is not None:
                group = paragraphs[author_idx + 1:end_idx]
                if group:
                    quote = soup.new_tag("p")
                    quote["class"] = "wutc-quote"
                    for idx, paragraph in enumerate(group):
                        text = paragraph.get_text(" ", strip=True)
                        parts = re.split(r"(?<=\.)\s+", text) if idx == 0 else [text]
                        for part_idx, part in enumerate(parts):
                            span = soup.new_tag("span")
                            classes = ["d-block"]
                            if idx > 0 and part_idx == 0:
                                classes.append("mt-3")
                            span["class"] = classes
                            span.string = part
                            quote.append(span)
                    group[0].insert_before(quote)
                    for paragraph in group:
                        paragraph.extract()

    for paragraph in soup.find_all("p"):
        if paragraph.get_text(" ", strip=True) == "Великий инструмент Творения — нож.":
            paragraph["class"] = paragraph.get("class", []) + ["wutc-quote"]


def prepare_tables(soup: BeautifulSoup) -> None:
    numeric_re = re.compile(r"^[\d\s.,%×xX*+:/()\-–—dD]+(sp)?$")
    cost_words = ("стоимость", "цена", "плата", "ценность", "cost")

    for table in soup.find_all("table"):
        table["class"] = ["table", "table-light", "table-striped", "table-sm"]

        for row in table.find_all("tr"):
            cells = row.find_all("td", recursive=False)
            if not cells:
                continue
            first = cells[0]
            header = soup.new_tag("th")
            header["scope"] = "row"
            header["class"] = "fw-normal"
            for child in list(first.children):
                header.append(child.extract())
            first.replace_with(header)

        head = table.find("thead")
        rows = table.select("tbody tr")
        if head is None or not rows:
            wrapper = soup.new_tag("div")
            wrapper["class"] = "table-responsive"
            table.wrap(wrapper)
            continue

        head_cells = head.find_all(["th", "td"], recursive=False)
        column_count = max(
            len(head_cells),
            max(len(row.find_all(["th", "td"], recursive=False)) for row in rows),
        )
        for column in range(1, column_count):
            values = []
            numeric = True
            for row in rows:
                cells = row.find_all(["th", "td"], recursive=False)
                if column >= len(cells):
                    numeric = False
                    break
                text = cells[column].get_text(" ", strip=True)
                if not text:
                    continue
                if not numeric_re.match(text) or not any(ch.isdigit() for ch in text):
                    numeric = False
                    break
                values.append(cells[column])
            if not numeric or not values:
                continue
            head_text = (
                head_cells[column].get_text(" ", strip=True).lower()
                if column < len(head_cells)
                else ""
            )
            align = "text-end" if any(word in head_text for word in cost_words) else "text-center"
            if column < len(head_cells):
                head_cells[column]["class"] = head_cells[column].get("class", []) + [align]
            for cell in values:
                cell["class"] = cell.get("class", []) + [align]

        wrapper = soup.new_tag("div")
        wrapper["class"] = "table-responsive"
        table.wrap(wrapper)


def render_navbar(books: list[dict]) -> str:
    parts = []
    for book in books:
        items = "".join(
            f'<li><a class="dropdown-item" href="{book["file"]}#{hid}">{escape(text)}</a></li>'
            for _, hid, text in book["nav"]
        )
        parts.append(
            '<li class="nav-item dropdown">'
            f'<a class="nav-link dropdown-toggle" href="{book["file"]}" role="button" '
            'data-bs-toggle="dropdown" aria-expanded="false">'
            f'{escape(book["short"])}</a>'
            f'<ul class="dropdown-menu">{items}</ul>'
            "</li>"
        )
    return "\n".join("                " + line for line in parts)


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> None:
    source = strip_frontmatter(SRC.read_text(encoding="utf-8"))
    chunks = split_books(source)

    processed = []
    for spec, chunk in zip(BOOKS, chunks):
        soup = BeautifulSoup(pandoc(chunk), "html.parser")
        extract_subtitle(soup)
        style_quotes(soup, spec)
        nav = toc_entries(soup, spec["nav_levels"])
        prepare_tables(soup)
        add_anchors(soup)

        processed.append(
            {
                **spec,
                "content": "".join(str(x) for x in soup.contents),
                "nav": nav,
                "table_count": len(soup.find_all("table")),
            }
        )

    navbar = render_navbar(processed)
    for page in processed:
        html = PAGE_TEMPLATE.format(
            lang="ru",
            title=escape(page["title"]),
            short=escape(page["short"]),
            nav=navbar,
            content=page["content"],
        )
        (ROOT / page["file"]).write_text(html, encoding="utf-8")
        print(f'{page["file"]}: таблиц {page["table_count"]}')

    print("Готово.")


if __name__ == "__main__":
    main()
