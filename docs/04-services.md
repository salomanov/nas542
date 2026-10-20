# Сервисы Entware

Все приложения запускаются от пользователя `admin`, данные — в `/i-data/45f1aca1/Apps/`,
логи — в `/i-data/45f1aca1/Apps/logs/`.

Общий шаблон init-скрипта: `start-stop-daemon --background --make-pidfile --chuid admin`
(в системе нет `nohup`).

---

## Syncthing

| | |
|---|---|
| Версия | 2.0.15 (opkg) |
| GUI | `0.0.0.0:5004`, путь `/apps/sync/` |
| Синхронизация | `0.0.0.0:22001` (22000 занят старым Pulse) |
| Дом | `/i-data/45f1aca1/Apps/syncthing` |
| Папка | `apps` → `/i-data/45f1aca1/Apps/sync` |
| Init | `/opt/etc/init.d/S90syncthing` |

Особенности:

- Штатный `S92syncthing` из пакета **отключён** (`S92syncthing.disabled`): он конфликтует
  со старым Syncthing из пакета Pulse — `pidof` находит чужой процесс.
- Старый Pulse Syncthing надо убить, иначе он держит 22000 и лезет в ту же папку.
- CLI v2 принимает только `--home=...` (`--config` + `--data` вместе нельзя).
- Device ID: `syncthing device-id --home=/i-data/45f1aca1/Apps/syncthing`.

Добавление телефона (REST API, ключ из `<apikey>` в `config.xml`):

```sh
KEY=$(sed -n 's|.*<apikey>\([^<]*\)</apikey>.*|\1|p' /i-data/45f1aca1/Apps/syncthing/config.xml)
curl -s -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"deviceID":"<ID>","name":"phone","addresses":["dynamic"]}' \
  http://127.0.0.1:5004/rest/config/devices
```

Затем добавить `{"deviceID":"<ID>"}` в `devices` папки `apps` через
`GET/PUT /rest/config/folders/apps`.

Device ID телефона — 63 символа (8 групп по 7). Если групп 8, а символов меньше —
ID введён с ошибкой, Syncthing его не примет.

---

## FileBrowser

| | |
|---|---|
| Версия | 2.62.1 (opkg) |
| Порт | 5007, baseurl `/apps/fb` |
| Root | `/i-data/45f1aca1` |
| БД | `/i-data/45f1aca1/Apps/filebrowser/filebrowser.db` |
| Конфиг | `/opt/etc/filebrowser/filebrowser.conf` |

Важные грабли:

- **`filebrowser users add` в этой сборке не работает** — возвращает rc=1 молча.
  Пользователь создаётся через `users import` с заранее посчитанным bcrypt-хешем.
- Хеш генерируем PHP: `password_hash($pass, PASSWORD_BCRYPT)` и меняем префикс
  `$2y$` → `$2a$` (Go-библиотека bcrypt не понимает `$2y$`).
- Пока демон держит Bolt DB, любые CLI-операции падают с `Error: timeout`.
  Останавливать сервис перед `users import` / `config set`.
- `users rm` не даст удалить единственного администратора.

---

## Transmission

| | |
|---|---|
| Версия | 4.0.6 |
| RPC + web | `0.0.0.0:5008`, URL `/transmission/` |
| Скачивание | `/i-data/45f1aca1/Apps/transmission/downloads` |
| Недокачанное | `/i-data/45f1aca1/Apps/transmission/incomplete` |
| Настройки | `/opt/etc/transmission/settings.json` |

- `rpc-password` можно положить открытым текстом — демон при старте заменит его хешем.
- `rpc-whitelist-enabled: false`, иначе прокси с 127.0.0.1 не пустит.
- Штатный `S88transmission` печатает «failed», но демон стартует — у него гонка
  с `pidof`. Проверять `ps`/порт, а не вывод скрипта.
- Web UI отвечает 401 без авторизации — это норма, не ошибка.

---

## aria2 + AriaNg

| | |
|---|---|
| aria2 | 1.37, RPC `0.0.0.0:6800`, секрет в `aria2.conf` |
| AriaNg | 1.3.15, статика на 5006, путь `/apps/aria/` |
| Скачивание | `/i-data/45f1aca1/Apps/aria2/downloads` |

AriaNg — чистая статика, поэтому запускается встроенным сервером PHP с роутером:

```
php-cli -S 0.0.0.0:5006 -t /i-data/45f1aca1/Apps/ariang /i-data/45f1aca1/Apps/ariang/router.php
```

`router.php` проксирует `/jsonrpc` на `127.0.0.1:6800`, остальное отдаёт как файлы.
Дополнительно `/jsonrpc` проброшен и на уровне `pkg_httpd`, так что AriaNg работает
и через общий HTTPS-прокси (RPC-адрес `https://host:34501/jsonrpc`).

---

## COPS (OPDS)

| | |
|---|---|
| Версия | master (1.2.0-dev), PHP 8.4 |
| Порт | 5005, путь `/apps/cops/` |
| Веб-каталог | `/apps/cops/` (редирект на `/apps/cops/ui/`) |
| OPDS | `/apps/cops/feed.php` |
| Библиотека | `/i-data/45f1aca1/Apps/calibre/` (`metadata.db` + книги) |
| Входящие книги | `/i-data/45f1aca1/Apps/calibre/inbox/` |
| Конфиг | `config_local.php` (генерируется из `configs/cops/config_local.php`) |
| Логин | `COPS_USER` / `COPS_PASS` из `scripts/00-secrets.env` |

Почему не Calibre-Web/Kavita/Komga: нужен компилятор (нет `gcc`), Python 3.13 без готовых
колёс под ARMv7 и ~200 МБ RAM (свободно ~90 МБ). COPS на PHP — единственный адекватный
вариант для этой машины.

Установка вручную (что делает `07-cops.sh`):

1. PHP-модули: `php8-cli` + `sqlite3`, `pdo-sqlite`, `dom`, `simplexml`, `mbstring`,
   `gd`, `fileinfo`, `session`, `iconv`, `curl`, `phar`, `xmlwriter`, `zip`,
   **`filter`, `intl`, `openssl`, `xml`, `ctype`**.
   Без `filter` composer падает с `Call to undefined function filter_var()`
   (это не баг composer, а отсутствующий модуль).
2. `git` + `git-http` — нужны для dev-зависимостей.
3. Сборка **только на диске**: `/tmp` — рамдиск, composer упрётся в «no space left».
4. `composer install --no-dev` в каталоге COPS.
5. Патч PHP 8: в `vendor/seblucas/dot-php/doT.php` заменить
   `return @create_function ('$it', $func);`
   на `return @eval('return function ($it) { ' . $func . ' };');`
   (`create_function` удалён в PHP 8).

### Что донастроено сверх стока

**Русский интерфейс.** `$config['cops_language'] = 'ru'` — COPS берёт
`lang/Localization_ru.json`, поэтому все подписи (Авторы, Жанры, Недавние поступления,
Резюме) на русском. Название — «Библиотека NAS542», подзаголовок — «Домашняя библиотека».

**Своя тема `nas542`.** Каталог `templates/nas542` — копия `bootstrap`, в которой:

* `header.html` — свой навбар: логотип-книжка, название, поиск, кнопка «О программе».
  Кнопка переключения на «дефолтный шаблон COPS» убрана (незачем на бытовом сервере);
* `styles/custom.css` — синий градиент в шапке, скруглённые карточки с тенью при наведении,
  аккуратные обложки, оранжевые бейджи;
* `file.html` — добавлен `<link>` на `custom.css` и путь к `scripts/cops.js` поправлен
  на `templates/nas542/`.

Шаблон подключается через `$config['cops_template'] = 'nas542'`; COPS берёт тему просто
по имени каталога, поэтому правки не затрагивают штатные `bootstrap`/`default`.

**Иконка.** `images/favicon.ico` (16/32/48 px) и `images/nas542-logo.png` рисует
`configs/cops/theme/make_icon.py` — чистый Python без Pillow, чтобы не тянуть зависимости.
Скрипт создаёт PNG и ICO вручную (zlib + struct).

**Пароль.** `$config['cops_basic_authentication']` — обычный HTTP Basic, работает и в
браузере, и в OPDS-клиентах (Moon+ Reader спрашивает логин/пароль при добавлении каталога).
Тонкость: COPS под `php -S` не всегда получает `PHP_AUTH_USER`, поэтому в
`config_local.php` заголовок `Authorization` разбирается вручную (см. `docs/07-troubleshooting.md`).

**Чистка навигации.** `$config['cops_ignored_categories']` убирает с главной полки
«Серии», «Издательства», «Рейтинг», «Языки» — остаются авторы, жанры, названия,
недавние поступления. `cops_recentbooks_limit = 12`, `cops_max_item_per_page = 30`.

**Кэш обложек на диске.** `cops_thumbnail_cache_directory = calibre/.thumbs/`
(`/tmp` — рамдиск на ~10 МБ, туда кэш складывать нельзя).

**Старые cookie не перебивают конфиг.** В `config_local.php` добавлено
`unset($_COOKIE['template'], $_COOKIE['style']);`. Иначе браузер, у которого когда-то
осталась cookie `template=default`, показывает голый шаблон «из 2005-го», игнорируя тему.

### Современный интерфейс (`/apps/cops/ui/`)

Штатные темы COPS — это Bootstrap 3, и «осовременить» их косметикой не получается.
Поэтому рядом с COPS живёт собственный каталог: `Apps/cops/ui/` (`index.php`,
`api.php`, `assets/app.css`, `assets/app.js`), который ставит тот же `07-cops.sh`.

* **Ничего не ест.** Чистый JS/CSS без сборки, фреймворков и CDN; отдаётся тем же
  `php -S`, что и COPS. Дополнительной RAM не требуется.
* **API.** `ui/api.php` открывает `metadata.db` через PDO (только чтение):
  `action=list` (поиск, фильтры по автору/жанру, сортировка, пагинация),
  `action=book` (полная карточка), `action=facets` (авторы, жанры, счётчики),
  `action=cover` и `action=download` (файлы отдаются из библиотеки, путь проверяется
  через `realpath`). Авторизация — та же HTTP Basic из `config.php`, достаточно
  подключить его первой строкой.
* **Что умеет.** Сетка обложек (у книг без обложки — аккуратная заглушка с инициалами),
  мгновенный поиск, полки «Все книги» / «Недавние», фильтры по авторам и жанрам,
  карточка книги с аннотацией и метаданными, скачивание EPUB/PDF, «Читать онлайн»
  (штатная читалка COPS `epubreader.php`), светлая и тёмная тема (запоминается),
  ссылки на книгу/автора/жанр в адресе (`#book-4`, `#author-2`), мобильная вёрстка.
* **Точка входа.** `07-cops.sh` патчит `index.php`: если в запросе нет `page/query/id/db`,
  отдаётся `302` на `ui/`. OPDS (`feed.php`), читалка и прямые ссылки не затронуты.
* **Старый вид и настройки** — ссылки внизу левой колонки: `index.php?page=1`
  (шаблон COPS) и `index.php?page=19` (выбор темы/языка COPS).
* Файлы UI лежат в репозитории: `configs/cops/ui/`. После правок достаточно
  скопировать их в `Apps/cops/ui/` и обновить страницу (PHP-кеша нет).

### Автоимпорт книг

Кладёте файл в `calibre/inbox/` — через минуту он появляется в каталоге.
Работает демон `S91bookimport` (`cops-tools/bookimport-loop.sh`), он раз в 60 секунд
запускает `cops-tools/import_books.py`.

* **EPUB** — заголовок, авторы, язык, издательство, дата, жанры (subject), аннотация,
  ISBN, серия и обложка (`cover-image` / `meta name="cover"`).
* **FB2** — title-info, авторы, язык, жанры, аннотация, обложка из `<binary>`.
* **PDF/MOBI/AZW3/DJVU** — без метаданных: название из имени файла, автор «Unknown»
  (парсить PDF без сторонних библиотек на ARMv7 нечем).

Книга копируется в структуру Calibre (`Автор/Название (id)/Название.epub`), обложка — в
`cover.jpg`, запись добавляется в `metadata.db`. Дубликаты (то же название + автор)
пропускаются и складываются в `inbox/_skipped/`. Лог — `Apps/logs/bookimport.log`.

Ручной запуск:

```sh
/opt/bin/python3 /i-data/45f1aca1/Apps/cops-tools/import_books.py --dry-run   # что будет
/opt/bin/python3 /i-data/45f1aca1/Apps/cops-tools/import_books.py             # импорт
```

Клиенты OPDS: Moon+ Reader, KOReader, Librera, Aldiko, Calibre iOS.
В них добавляется каталог `https://host:34501/apps/cops/feed.php` + логин/пароль COPS.

Демо-библиотеку (3 книги с Project Gutenberg) собирает `tools/mklib.py` —
он создаёт `metadata.db`, файлы книг и обложки. Запускается только при `07-cops.sh --demo`.

