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
        "toc_levels": (2, 3),
        "nav_levels": (2, 3),
    },
    {
        "file": "magic.html",
        "title": "Книга 2 — Магия",
        "short": "Книга 2",
        "toc_levels": (2, 3),
        "nav_levels": (2,),
    },
    {
        "file": "treasure.html",
        "title": "Treasure",
        "short": "Treasure",
        "toc_levels": (2, 3),
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
    <link href="https://fonts.googleapis.com/css2?family=Aladin&family=Averia+Serif+Libre:ital,wght@0,300;0,400;0,700;1,300;1,400&family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="assets/style.css" rel="stylesheet">
</head>
<body>
<a class="visually-hidden-focusable" href="#main">К содержанию</a>
<nav class="navbar navbar-expand-lg sticky-top wutc-navbar">
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
        <p>Wolves Upon the Coast · перевод на русский · <a href="index.html">Книга 1</a> · <a href="magic.html">Книга 2</a> · <a href="treasure.html">Treasure</a></p>
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


def prepare_tables(soup: BeautifulSoup) -> None:
    for table in soup.find_all("table"):
        classes = table.get("class", [])
        table["class"] = classes + ["table", "table-striped", "table-sm", "align-middle"]
        wrapper = soup.new_tag("div")
        wrapper["class"] = "table-responsive"
        table.wrap(wrapper)


def render_toc(entries: list[tuple[int, str, str]]) -> str:
    items = []
    for level, hid, text in entries:
        cls = "toc-h2" if level == 2 else "toc-h3"
        items.append(
            f'<li class="{cls}"><a href="#{hid}">{escape(text)}</a></li>'
        )
    is_open = " open" if len(entries) <= 60 else ""
    return (
        f'<details class="wutc-toc"{is_open}>'
        '<summary class="wutc-toc-title">Содержание</summary>'
        f'<ul>{"".join(items)}</ul>'
        "</details>"
    )


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
        entries = toc_entries(soup, spec["toc_levels"])
        nav = [(lvl, hid, text) for lvl, hid, text in entries if lvl in spec["nav_levels"]]
        prepare_tables(soup)
        add_anchors(soup)

        h1 = soup.find("h1")
        h2s = soup.find_all("h2")
        toc_node = BeautifulSoup(render_toc(entries), "html.parser")
        first_heading = entries[0][2] if entries else ""
        if re.match(r"^Книга\s+\d", first_heading) and len(h2s) > 1:
            # «Книга 1/2 — …» — подзаголовок; ставим оглавление после интро.
            h2s[1].insert_before(toc_node)
        elif h2s:
            # У Treasure подзаголовка нет — ставим перед первым разделом.
            h2s[0].insert_before(toc_node)
        elif h1 is not None:
            h1.insert_after(toc_node)

        processed.append(
            {
                **spec,
                "content": "".join(str(x) for x in soup.contents),
                "nav": nav,
                "toc_count": len(entries),
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
        print(
            f'{page["file"]}: таблиц {page["table_count"]}, '
            f'пунктов оглавления {page["toc_count"]}'
        )

    print("Готово.")


if __name__ == "__main__":
    main()
