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
| OPDS | `/apps/cops/feed.php` |
| Библиотека | `/i-data/45f1aca1/Apps/calibre/` (`metadata.db` + книги) |
| Конфиг | `config_local.php` |

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

Клиенты OPDS: Moon+ Reader, KOReader, Librera, Aldiko, Calibre iOS.
В них добавляется каталог `https://host:34501/apps/cops/feed.php`, пароль не нужен.

Демо-библиотеку (3 книги с Project Gutenberg) собирает `tools/mklib.py` —
он создаёт `metadata.db`, файлы книг и обложки.
