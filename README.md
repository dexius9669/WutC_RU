# WutC-RU

Русский перевод «Wolves Upon the Coast» в виде статического сайта.

- Книга 1 — правила: `index.html`
- Книга 2 — магия: `magic.html`
- Treasure: `treasure.html`

Оформление сделано по мотивам [callmepartario.github.io/wutc](https://callmepartario.github.io/wutc/):
Bootstrap 5, липкая навигация, светлая и тёмная темы, адаптивные таблицы.

## Структура

```
src/WutC_Rules.ru.md   исходный Markdown (мастер-файл)
build.py               сборка страниц
assets/style.css       оформление
assets/app.js          переключатель темы, мобильное меню
```

## Сборка

Требуются `pandoc` 3.x и Python 3 с `beautifulsoup4`.

```bash
python3 build.py
```

Скрипт режет `src/WutC_Rules.ru.md` по трём заголовкам `# `, конвертирует
каждую часть через pandoc, добавляет якоря, оглавление и обёртки для таблиц,
затем записывает `index.html`, `magic.html`, `treasure.html`.

## Публикация

Сайт отдаётся GitHub Pages из ветки `main`, каталог `/ (root)`.
Файл `.nojekyll` отключает обработку Jekyll, поэтому HTML и `assets/`
публикуются как есть.

## Правки текста

Текст перевода меняется только в `src/WutC_Rules.ru.md`, после чего нужно
запустить `python3 build.py` и закоммитить и исходник, и собранные страницы.
