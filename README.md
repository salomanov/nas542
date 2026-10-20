# NAS542 — домашний сервер

Всё, что нужно, чтобы поднять и восстановить сервисы на ZyXEL NAS542 после сброса настроек:
скрипты установки, рабочие конфиги и документация.

Проверено на боевой машине 20.10.2026.

---

## Что работает

| Сервис | Внешний адрес | Локально | Вход |
|---|---|---|---|
| ownCloud 7 | `https://<WAN>:34501/pkg/ownCloud/` | `https://192.168.1.50:5001/pkg/ownCloud/` | `admin` |
| Syncthing | `https://<WAN>:34501/apps/sync/` | `http://192.168.1.50:5000/apps/sync/` | из `00-secrets.env` |
| COPS (OPDS, книги) | `https://<WAN>:34501/apps/cops/feed.php` | `http://192.168.1.50:5000/apps/cops/feed.php` | из `00-secrets.env` |
| Библиотека (веб-каталог) | `https://<WAN>:34501/apps/cops/` | `http://192.168.1.50:5000/apps/cops/` | из `00-secrets.env` |
| FileBrowser | `https://<WAN>:34501/apps/fb/` | `http://192.168.1.50:5000/apps/fb/` | `admin` |
| AriaNg (aria2) | `https://<WAN>:34501/apps/aria/` | `http://192.168.1.50:5000/apps/aria/` | RPC-секрет |
| Transmission | `https://<WAN>:34501/transmission/web/` | `http://192.168.1.50:5000/transmission/web/` | `admin` |

`<WAN>` — внешний IP, порт `34501` (HTTPS, сертификат от собственного CA).

Всё это отдаётся через `mod_proxy` внутри `pkg_httpd`, поэтому **роутер трогать не нужно**:
достаточно одного проброса `34501 → 5001`.

### Как добавить книгу

Положите файл в папку `Apps/calibre/inbox` любым удобным способом — FileBrowser,
Syncthing (папка `apps`), WinSCP по SSH. Через минуту книга сама появится в каталоге
COPS: обложка, автор, жанры и аннотация берутся из EPUB/FB2. Подробности —
[docs/04-services.md](docs/04-services.md#автоимпорт-книг).

Каталог открывается по адресу `.../apps/cops/` — это собственный лёгкий интерфейс
(сетка обложек, поиск, авторы и жанры, тёмная тема), см.
[docs/04-services.md](docs/04-services.md#современный-интерфейс-appscopsui).
Телефонные читалки по-прежнему подключаются к OPDS `.../apps/cops/feed.php`.

---

## Быстрый старт (восстановление)

```powershell
git clone https://github.com/salomanov/nas542.git
cd nas542

copy scripts\00-secrets.env.example scripts\00-secrets.env
notepad scripts\00-secrets.env      # вписать пароли и IP

.\scripts\tools\deploy.ps1          # заливает всё на NAS и запускает install-all.sh
```

Требуется: SSH на NAS, WinSCP (путь можно поменять в `deploy.ps1`), Entware в `/opt`.

Подробный порядок действий после заводского сброса — [docs/06-recovery.md](docs/06-recovery.md).

---

## Состав репозитория

```
scripts/
  install-all.sh          — запуск всех шагов по порядку
  00-secrets.env.example  — шаблон секретов (реальный файл не коммитится)
  01-entware.sh           — проверка Entware
  02-packages.sh          — установка пакетов opkg
  03-syncthing.sh         — Syncthing + папка Apps
  04-filebrowser.sh       — FileBrowser + пользователь
  05-transmission.sh      — Transmission
  06-aria2-ariang.sh      — aria2 + AriaNg
  07-cops.sh              — COPS (OPDS): тема, иконка, пароль, импортёр книг
  08-httpd-proxy.sh       — mod_proxy в pkg_httpd
  09-owncloud-shims.sh    — шимы OC10 для ownCloud 7
  lib.sh                  — общие функции
  tools/                  — deploy.ps1, nasrun.ps1, healthcheck.sh, backup.sh
configs/
  httpd/                  — apps_proxy.conf
  init/                   — init-скрипты сервисов
  filebrowser/ transmission/ aria2/ cops/ ariang/ owncloud/
tls/                      — CA и серверный сертификат, скрипты выпуска
docs/                     — документация
archive/metarepository/   — старые файлы ZyXEL-пакета MetaRepository (не используются)
PROJECT_STATE.md          — журнал состояния и история решений
```

---

## Порты (внутренние)

| Порт | Что |
|---|---|
| 22 | SSH |
| 80 / 443 | штатный Apache ZyXEL (веб-интерфейс) |
| 5000 / 5001 | `pkg_httpd`: HTTP / HTTPS, пакеты + прокси |
| 5002 / 5003 | `DAV_httpd` (WebDAV) |
| 5004 | Syncthing GUI |
| 5005 | COPS |
| 5006 | AriaNg |
| 5007 | FileBrowser |
| 5008 | Transmission (RPC + web) |
| 6800 | aria2 JSON-RPC |
| 22001 | Syncthing (sync) |
| 51413 | Transmission (peer) |

---

## Ограничения

- **WebSocket через прокси не работает** (Apache 2.2 + `mod_proxy_http`). Syncthing GUI
  открывается и настройки сохраняются, но живые статусы не обновляются сами — помогает F5.
  Для полноценной работы нужен прямой проброс на `5004`.
- ownCloud 7 не обновляем: официальное приложение Android 2.14.2 работает через шимы,
  более новые версии приложения требуют сервер ≥ 10.
- Свободной RAM мало (~100 МБ), поэтому тяжёлые альтернативы (Calibre-Web, Kavita, Komga)
  не ставим. COPS остаётся OPDS-сервером, а современный вид даёт собственный каталог
  `/apps/cops/ui/` на чистом JS — без сборки, зависимостей и лишней памяти.

---

## Лицензия и безопасность

Репозиторий публичный: **пароли, внешний IP и ключи в него не попадают**.
Всё чувствительное — в `scripts/00-secrets.env` (в `.gitignore`).
CA-ключ (`zyxel_nas_ca.key`) хранится только офлайн у владельца.
