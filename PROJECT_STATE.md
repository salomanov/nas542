# NAS542 Project State

## Общая информация
- **Устройство:** ZyXEL NAS542 (ARMv7 Dual Core, Marvell Armada 380 88F6820)
- **ОС:** Linux NAS542 3.2.54 armv7l
- **Внешний белый IP (WAN):** `178.140.8.56`
- **Локальный IP NAS (LAN):** `192.168.1.50`
- **Основной пользователь системы:** `admin` / пароль: `12345678` (root через `su -` или `sudo`)

## Сводная таблица доступов, сервисов и паролей
| Сервис | Назначение | Внешний URL (WAN) | Локальный URL (LAN) | Логин | Пароль / Секрет |
|---|---|---|---|---|---|
| **SSH (PuTTY)** | Консоль / SFTP | `178.140.8.56:34522` | `192.168.1.50:22` | `admin` | `12345678` (root: `12345678`) |
| **Веб-интерфейс NAS** | Рабочий стол ZyXEL | `http://178.140.8.56:34502/` | `http://192.168.1.50/` | `admin` | `12345678` |
| **ownCloud 7** | Облачное хранилище | `https://178.140.8.56:34501/pkg/ownCloud/` | `https://192.168.1.50:5001/pkg/ownCloud/` | `admin` | `12345678` |
| **ownCloud WebDAV** | WebDAV для сторонних клиентов | `https://178.140.8.56:34501/pkg/ownCloud/remote.php/webdav/` | `https://192.168.1.50:5001/pkg/ownCloud/remote.php/webdav/` | `admin` | `12345678` |
| **Библиотека (COPS UI)** | Веб-каталог книг | `https://178.140.8.56:34501/apps/cops/` | `https://192.168.1.50:5001/apps/cops/` | `admin` | `12345678` |
| **COPS OPDS** | Каталог для читалок (FBReader) | `https://178.140.8.56:34501/apps/cops/feed.php` | `https://192.168.1.50:5001/apps/cops/feed.php` | `admin` | `12345678` |
| **FileBrowser** | Проводник файлов в браузере | `https://178.140.8.56:34501/apps/fb/` | `https://192.168.1.50:5001/apps/fb/` | `admin` | `12345678` |
| **Syncthing** | Синхронизация файлов | `https://178.140.8.56:34501/apps/sync/` | `https://192.168.1.50:5001/apps/sync/` | `admin` | `12345678` |
| **Transmission** | Торрент-клиент | `https://178.140.8.56:34501/transmission/web/` | `https://192.168.1.50:5001/transmission/web/` | `admin` | `12345678` |
| **Загрузчик медиа (yt-dlp)** | Веб-интерфейс видео/аудио | `https://178.140.8.56:34501/apps/ytdl/` | `https://192.168.1.50:5001/apps/ytdl/` | `admin` | `12345678` |
| **AriaNg (aria2)** | Загрузчик файлов | `https://178.140.8.56:34501/apps/aria/` | `https://192.168.1.50:5001/apps/aria/` | — | Секрет: `Passw0rd` |
| **aria2 JSON-RPC** | RPC для качалки | `https://178.140.8.56:34501/jsonrpc` | `https://192.168.1.50:5001/jsonrpc` | — | Секрет: `Passw0rd` |

## Карта портов и сервисов
| Сервис | Порт на роутере (WAN) | Внутренний порт NAS | Протокол / Доступ |
|---|---|---|---|
| **SSH (PuTTY)** | **34522** | 22 | OpenSSH 6.7 (`admin` / пароль из `scripts/00-secrets.env`) |
| **Веб-интерфейс NAS (Рабочий стол)** | **34502** | 80 | HTTP (`/r51209,/desktop,/index.html`) |
| **Веб-пакеты (pkg_httpd HTTP)** | **34503** | 5000 | HTTP |
| **Веб-пакеты (pkg_httpd HTTPS)** | **34501** | 5001 | HTTPS (ownCloud, etc.) |
| **Веб-пакеты (UPnP fallback)** | **34504** | 5001 | HTTPS (запасной порт Keenetic UPnP) |
| **WebDAV** | **34503** | 5002/5003 | DAV_httpd |

## Персистентность прокси и портов (добавлено 21.10.2026)
При удалении/установке пакетов через веб-интерфейс ZyXEL перегенерирует `/etc/pkg_service_conf/` и сбрасывает UPnP-правила роутера.
Для автоматического восстановления развернуты демоны автозапуска Entware:
1. `/opt/etc/init.d/S98apps-proxy` (`/i-data/45f1aca1/Apps/restore_proxy.sh`): восстанавливает `apps_proxy.conf`, добавляет `AuthZyxelSkipPattern /apps/ /transmission/ /jsonrpc` в `httpd2.conf` и `Entware-ng.conf`, делает `pkghttpd.sh reload`.
2. `/opt/etc/init.d/S99upnp-ports` (`/i-data/45f1aca1/Apps/ensure_upnp_ports.py`): обращается по SOAP к MiniUPnPd на Keenetic (`192.168.1.1:1900`) и автоматически закрепляет проброс портов `34501 -> 5001`, `34502 -> 80`, `34522 -> 22`, `34523 -> 23`.

## Статус установленных пакетов
1. **ownCloud:**
   - URL: `https://178.140.8.56:34501/pkg/ownCloud/`
   - Статус: Активен, версия 7.0.15.2, пользователь `admin`.
   - WebDAV: `https://178.140.8.56:34501/pkg/ownCloud/remote.php/webdav/` (полностью рабочий, проверено: PROPFIND 207).
   - Причина сбоя официального мобильного приложения: несовместимость версии ownCloud 7 с современным приложением (требующим ownCloud 10+ и OAuth2). Лечится только апгрейдом — сознательно не делаем.
   - PHP 5.5.22 (mod_php5), реальные лимиты: `memory_limit 512M`, `post_max_size 513M`, `upload_max_filesize 513M` (из `.htaccess`, php.ini 128M не мешает).
   - Данные: 6.4 МБ, SQLite `data/owncloud.db`, свободно 1.8 ТБ.

## TLS (обновлено 20.10.2026)
- **Корневой CA:** `Zyxel NAS Root CA` (`C=RU, O=Home Network`), 2048-bit RSA, до 15.10.2036.
  - Файлы у пользователя: `D:\Загрузки\zyxel_nas_ca.crt` + `zyxel_nas_ca.key` (ключ CA — хранить офлайн!).
- **Серверный сертификат перевыпущен с SAN** (старый был только `CN=178.140.8.56` — современные клиенты такое отвергают):
  - SAN: `IP:178.140.8.56`, `IP:192.168.1.50`, `IP:127.0.0.1`, `DNS:nas542.local`, `DNS:nas542`
  - serial `4E415336`, срок до 17.10.2036, подписан тем же CA.
  - Установлен в `/etc/service_conf/CA.cer` **и** `/etc/zyxel/cert/CA.cer`; ключ не менялся.
  - Бэкапы: `*.bak-20261020` в тех же каталогах. Откат: скопировать `.bak` обратно и `reload` сервисы.
  - Скрипт перевыпуска: `E:\Projects\NAS542\tls\install-leaf.sh` (серверный), готовые файлы — `tls\leaf_new.crt`, `tls\root_ca.crt`.
- Один и тот же сертификат используется тремя демонами: `httpd` (веб-интерфейс), `DAV_httpd` (5002/5003), `pkg_httpd` (5000/5001 — ownCloud).
- Reload без простоя: `/etc/init.d/httpd.sh reload`, `/etc/init.d/davhttpd.sh reload`, `/etc/init.d/pkghttpd.sh reload`.
- Корневой CA раздаётся в облаке: `https://178.140.8.56:34501/pkg/ownCloud/remote.php/webdav/Zyxel-NAS-CA.crt`.

## Доступ к облаку (клиенты)
- **Официальное приложение ownCloud для Android 2.14.2 — РАБОТАЕТ** (через шимы, см. следующий раздел).
- **Версии приложения:** работает вся линейка 2.x **до 2.14.2 включительно**. С 2.15 (июнь 2020) в changelog: «End of support for servers older than 10 version»; в APK 2.15+/3.x/4.x есть строка `server_not_supported` = «Your server version is lower than 10 so is not supported». Проверка смотрит на `status.php` (`7.0.15`) — то есть 2.15 … 4.8.4 на сервер не пустят.
- Если приложение обновится само — появится именно это сообщение; лечится установкой APK 2.14.2 обратно.
- URL для приложения: `https://178.140.8.56:34501/pkg/ownCloud` (только база, без `remote.php/...`), логин `admin`.
- Nextcloud-приложение (35.x) — **не работает**: требует `/remote.php/dav` (spaces), сервер отвечает 404.
- Другие WebDAV-клиенты: Android — X-plore (проверено, 207), FolderSync / Solid Explorer / Owlfiles; iOS — Owlfiles / Documents; Windows — RaiDrive, WinSCP (SFTP/34522) или штатный WebDAV-диск после установки CA.
- WebDAV URL для сторонних клиентов: `https://178.140.8.56:34501/pkg/ownCloud/remote.php/webdav/`, логин `admin`.
- На Windows CA нужно поставить в машинное хранилище (нужен админ): `E:\Projects\NAS542\tls\install-ca-admin.cmd` (ПКМ → «Запуск от имени администратора»).

## Шимы совместимости для современного приложения (OC10 DAV)
Файлы на NAS в `/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/`:
- **`remote.php`** — патчен блоком `OC10-DAV-SHIM` (бэкап `remote.php.bak-davshim`):
  1. `/dav/files/<user>/...` → переписывается на `/webdav/...` (PATH_INFO + REQUEST_URI);
  2. XML-ответы (`Content-Type: *xml*`) проходят через `str_replace`: `href` `/remote.php/webdav/` → `/remote.php/dav/files/<user>/` (фильтр только для XML, бинарные скачивания не трогаются, буфер 1 МБ);
  3. `/dav/uploads/...` → подключает `dav-uploads-shim.php`.
- **`dav-uploads-shim.php`** — реализация chunked upload v2: `MKCOL` (201), `PUT` чанка (201), `MOVE` `.file` → сборка чанков и запись через `\OC\Files\View::file_put_contents` (201), `DELETE` (204), `PROPFIND`/`OPTIONS`. Временные чанки: `<datadirectory>/uploads_shim/<user>/<transferid>/`.
- **`ocs/v2.php`** — копия `v1.php` (современные клиенты стучатся в v2, ответы в формате v1).
- Локальные копии/скрипты: `E:\Projects\NAS542\debug\dav-shim.block`, `dav-uploads-shim.php`, `oc-dav-shim-fix.sh`, `enable-oc-log.sh`.
- Откат: вернуть `remote.php.bak-davshim` на место, удалить `dav-uploads-shim.php`, `ocs/v2.php`.
- Проверено: PROPFIND 207 с правильными href, полный цикл загрузки, скачивание PDF 2 025 905 б без искажений.

## Известные мелочи
- **Временно включён** `CustomLog /var/log/httpd/oc_access.log` в `/etc/pkg_service_conf/httpd_zld2.conf` (бэкап `.bak-log`) — для диагностики приложения. Лог в памяти (tmpfs), после стабилизации убрать и сделать `pkghttpd.sh reload`.
- WAN `34500` (HTTP пакетов → 5000) не отвечает, хотя порт 5000 на NAS слушает — смотреть проброс на роутере. Для работы не критично (используем HTTPS 34501).
- В `data/owncloud.log` периодически `Unable to parse OCS content for app ...` — косметика при `appstoreenabled=false`.
- Временные файлы на NAS после работ удалены (`/tmp`), ключ CA на NAS не хранится.
2. **Entware:**
   - Успешно установлен актуальный репозиторий: `armv7sf-k3.2` (3026 пакетов).
   - Менеджер пакетов `opkg` работает штатно (`/opt/bin/opkg`).
   - Пути `/opt/bin` и `/opt/sbin` прописаны в профиль `admin`.
   - Автозапуск интегрирован в `/i-data/45f1aca1/.PKG/Entware-ng/etc/init.d/Entware-ng`.
3. **Plex, MetaRepository, pyLoad, Darkstat, Syncthing:** активны.

## Сервисы Entware (добавлено 20.10.2026)

Всё крутится от `admin`, данные в `/i-data/45f1aca1/Apps/`, логи в `Apps/logs/`.

| Сервис | Порт | Путь через прокси | Версия |
|---|---|---|---|
| Syncthing | 5004 (+22001 sync) | `/apps/sync/` | 2.0.15 |
| COPS (OPDS) | 5005 | `/apps/cops/` | master 1.2.0-dev |
| AriaNg | 5006 | `/apps/aria/` | 1.3.15 |
| FileBrowser | 5007 | `/apps/fb/` | 2.62.1 |
| Transmission | 5008 | `/transmission/` | 4.0.6 |
| yt-dlp Web UI | 5009 | `/apps/ytdl/` | 2026.08.19 (Web UI + yt-dlp) |
| aria2 RPC | 6800 | `/jsonrpc` | 1.37 |

- **Прокси:** `mod_proxy` в `pkg_httpd` (Apache 2.2), правила —
  `/etc/pkg_service_conf/apps_proxy.conf`, подключаются в конец `httpd2.conf`.
  В `AuthZyxelSkipPattern` добавлены `/apps/ /transmission/ /jsonrpc`.
  Наружу нужен только один проброс: `34501 → 5001`.
- **WebSocket через прокси не работает** — Syncthing GUI без живых обновлений (F5).
- **Syncthing:** ID `NLZHYJA-H5GBSIH-XNOIAPR-WVLCULU-PWWLB2V-JANRRO7-4GO3KB5-7NSBAAY`,
  папка `apps` → `Apps/sync`, телефон `XGIKJLI-...-LQ7KVA5` добавлен и подключён к папке.
  Пакетный `S92syncthing` отключён (`.disabled`), вместо него `S90syncthing`.
- **FileBrowser:** `users add` в этой сборке сломан, пользователь создан через
  `users import` с bcrypt (`$2y$` → `$2a$`).
- **COPS:** для composer доставлены `php8-mod-filter/intl/openssl/xml/ctype`;
  сборка только на диске (`/tmp` — рамдиск); пропатчен `create_function` в dot-php.
  Старая версия лежит в `Apps/cops-1.1.3` для отката.
- **COPS, доработки (20.10.2026):** русский интерфейс (`cops_language=ru`),
  своя тема `templates/nas542` (навбар с логотипом + `styles/custom.css`),
  иконка `images/favicon.ico` (генерируется `make_icon.py`, без Pillow),
  HTTP Basic по `COPS_USER`/`COPS_PASS`, скрыты полки series/publisher/rating/language,
  кэш обложек на диске (`calibre/.thumbs`), 12 недавних книг и 30 на страницу.
- **Современный интерфейс библиотеки (20.10.2026):** `Apps/cops/ui/` — отдельный
  лёгкий каталог на чистом JS (без сборки и лишней RAM), читает `metadata.db` через
  свой `api.php` (PDO sqlite, Basic auth наследуется от COPS). Сетка обложек,
  поиск, авторы/жанры, карточка книги, скачивание, читалка EPUB, тёмная тема.
  `/apps/cops/` теперь отдаёт 302 на `/ui/`; старый вид — `index.php?page=1`,
  настройки COPS — `index.php?page=19`.
- **Настройки COPS вернулись (20.10.2026):** шестерёнка в шапке нового каталога и старой
  темы, страница `index.php?page=19`. Пропатчены `lib/PageCustomize.php` (выбор шаблона
  `NAS542`/`Bootstrap`/`Default` вместо одной ссылки «switch to Bootstrap») и
  `templates/nas542/main.html` (bootstrap-шаблон не выводил `entry.content`, поэтому
  поля настроек были пустыми). Cookie `template`/`style` снова работают — выбор темы
  хранится в браузере.
- **Библиотекой владеет Calibre на ПК (20.10.2026):** библиотека пересобрана
  Calibre 9 (schema v28, 11 книг), живёт на ПК (`E:\Библиотека Calibre`), на NAS
  публикуется `scripts/tools/publish-calibre.ps1` по SFTP (снимок `metadata.db` через
  sqlite backup, `synchronize -delete`, проверка числа книг). Автоимпорт выключен
  (`CALIBRE_IMPORTER=0`), `S91bookimport` убран из автозапуска. Старая самодельная база
  (`mklib.py`) в Calibre недопустима: Calibre считает её нулевой версией и стирает книги.
- **Автоимпорт книг (опционально, `CALIBRE_IMPORTER=1`):** `Apps/calibre/inbox` → `S91bookimport` (раз в 60 с) →
  `cops-tools/import_books.py` (EPUB/FB2 с метаданными, остальное по имени файла) →
  запись в `metadata.db` + файл в структуре Calibre. Лог `Apps/logs/bookimport.log`.
- **Calibre-Web/Kavita/Komga не ставим:** нет gcc, Python 3.13 без колёс под ARMv7,
  ~200 МБ RAM при свободных ~90 МБ.
- Свободно после всего: ~75–90 МБ RAM, swap не тронут.

## Репозиторий и восстановление

- Код и конфиги: `https://github.com/salomanov/nas542/`
- Локальная копия: `E:\Projects\NAS542` (она же рабочая).
- Установка/восстановление: `docs/06-recovery.md`, скрипты `scripts/01..10`, запуск
  `scripts/tools/deploy.ps1`.
- Секреты — в `scripts/00-secrets.env` (в `.gitignore`, в репозиторий не попадают).
- Проверка состояния: `scripts/tools/healthcheck.sh` (31 проверка, все OK на 20.10.2026).

## Где остановились (20.10.2026)

Сделано и проверено на живой машине:

- COPS: русский интерфейс, тема `nas542`, иконка, HTTP Basic, автоимпорт EPUB/FB2.
- Новый каталог `Apps/cops/ui/` (плоский JS, свой `api.php` к `metadata.db`):
  обложки-заглушки, поиск, авторы/жанры, карточка книги, скачивание, читалка,
  тёмная тема, мобильная вёрстка. `/apps/cops/` редиректит на `/ui/`.
- Починен «вид из 2005-го»: в `config_local.php` сбрасываются cookie
  `template`/`style`, которые перебивали тему.
- Healthcheck: 31/31 OK. Коммит `99a6f60`, запушен в `main`, дерево чистое.
- Настройки COPS снова доступны (шестерёнка): выбор шаблона `NAS542`, стиль, число книг
  на странице, e-mail, скрытые полки. Проверены на живой машине.
- Библиотека переведена на Calibre-ПК: 11 книг (3 пользовательские + 8 классики),
  на NAS — копия; каталог/OPDS/скачивание проверены (total=11, обложки 200).
  Публикация одной кнопкой проверена: «на NAS 11 книг, как и локально».
  Бэкап старой библиотеки: `E:\Calibre Backup\calibre-old-20261020.tgz`.
- Написан и проверен скрипт `scripts/tools/publish-calibre.ps1` (SFTP, sqlite backup,
  дедупликация, проверка числа книг), создан ярлык на рабочем столе.
- Добавлена инструкция по установке корневого сертификата на macOS в `docs/05-tls.md`
  (через `security add-trusted-cert` и Связку ключей).

### Контекст владельца и обсуждение (21.10.2026)
- **NAS принадлежит другу-стоматологу**: система готовится для него.
- **Хранение профессиональной литературы**:
  - `ownCloud` — основное файлохранилище для всего: статьи, руководства, протоколы,
    презентации, видеозаписи вебинаров (иерархия `Стоматология / 01 Терапия / ...`,
    именование `Год - Автор - Название`).
  - `Каталог (Calibre / COPS)` — витрина для книг/учебников (EPUB/PDF) с обложками
    и OPDS-доступом для читалок.
  - `Zotero` — альтернатива/дополнение для научной периодики и клинических статей
    (сохранение в 1 клик с PubMed по DOI/PMID, аннотации в PDF, конспекты, связка
    по WebDAV с ownCloud на NAS для бесплатного безлимитного хранения PDF).
  - Варианты добавления книг для владельца:
    - Модель A (простая для владельца): папка приёма в ownCloud (`Apps/calibre/inbox`) +
      автоимпорт на NAS (потребует обновления `import_books.py` под schema v28 и разбор имени `Автор - Название`).
    - Модель B (текущая): Calibre на ПК как мастер + скрипт публикации `publish-calibre.ps1`.
- Перед передачей NAS другу: завести ему отдельную учётку ownCloud, сменить дефолтные пароли
  (`admin`/`12345678`), настроить еженедельный бэкап.

Открытые вопросы к следующей сессии:

- Решить по целевой модели для друга: модель A (автоимпорт на NAS) или модель B (Calibre на его ПК).
- Calibre-демо «Quick Start Guide» и скачанная новость «Правда» попали на NAS —
  удалить их в Calibre и опубликовать заново при необходимости.
- Демо-книги из Gutenberg (Dracula, Frankenstein, Metamorphosis, Moby Dick,
  The Time Machine) — оставить как пример или удалить.
- Косметика нового каталога: шрифты, плотность сетки, цвет акцента — по вкусу.
- Старые демо-книги (Pride and Prejudice, Alice, Sherlock) без обложек — можно
  дорисовать обложки или удалить.
- Проверить на телефоне OPDS-клиент после смены пароля/темы (адрес и логин те же:
  `/apps/cops/feed.php`, `admin` / `COPS_PASS`).
