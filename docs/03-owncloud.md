# ownCloud 7

## Что стоит

- Пакет ZyXEL ownCloud **7.0.15.2**, PHP 5.5.22 как `mod_php5`.
- Корень: `/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/`
- Данные: `/i-data/45f1aca1/.PKG/ownCloud/data/owncloud.db` (SQLite).
- URL: `https://<host>:5001/pkg/ownCloud/`
- Лимиты из `.htaccess`: `memory_limit 512M`, `post_max_size 513M`, `upload_max_filesize 513M`.

Обновлять до ownCloud 10 / Nextcloud **не нужно и не планируется**: данных мало,
а штатное приложение Android 2.14.2 полностью устраивает.

## Клиенты

| Клиент | Статус |
|---|---|
| ownCloud Android **2.14.2** | работает полностью (загрузка/скачивание/список) |
| ownCloud Android 2.15 … 4.x | отказ: `server_not_supported` (требуют сервер ≥ 10) |
| Nextcloud Android 35.x | не работает: нужен `/remote.php/dav` со spaces |
| X-plore, FolderSync, Solid Explorer, RaiDrive, WinSCP | работают по WebDAV |

Адрес для приложения — только база: `https://host:34501/pkg/ownCloud`, без `remote.php/...`.
Логин `admin`.

## Зачем шимы

Приложение 2.14.2 ходит по путям ownCloud 10:

- `remote.php/dav/files/<user>/...`
- `remote.php/dav/uploads/<user>/<transferid>/...` (chunked upload v2)
- `ocs/v2.php/...`

ownCloud 7 знает только `remote.php/webdav/` и `ocs/v1.php`. Вместо апгрейда сервера
поставлены три шима.

### 1. `remote.php` — блок `OC10-DAV-SHIM`

Вставляется сразу после `require_once 'lib/base.php';`:

1. `/dav/files/<user>/<path>` переписывается в `/webdav/<path>`
   (правится и `PATH_INFO`, и `REQUEST_URI`);
2. XML-ответы (`Content-Type: *xml*`) проходят через буфер 1 МБ и `str_replace`:
   `href` `/remote.php/webdav/` → `/remote.php/dav/files/<user>/`.
   Бинарные ответы не трогаются;
3. `/dav/uploads/...` подключает `dav-uploads-shim.php`.

Бэкап оригинала: `remote.php.bak-davshim` рядом.

### 2. `dav-uploads-shim.php` — chunked upload v2

Реализует:

| Метод | Путь | Ответ |
|---|---|---|
| MKCOL | `/dav/uploads/<user>/<id>` | 201 |
| PUT | `.../<id>/<n>` | 201 |
| MOVE | `.../<id>/.file` → целевой путь | 201, сборка чанков |
| DELETE | `.../<id>` | 204 |
| PROPFIND / OPTIONS | | корректные ответы |

Сборка идёт через `\OC\Files\View::file_put_contents`. Временные чанки:
`<datadirectory>/uploads_shim/<user>/<transferid>/`.

### 3. `ocs/v2.php`

Копия `ocs/v1.php`: современные клиенты стучатся в v2 и понимают ответы v1.

## Проверка после установки

```sh
# статус
curl -sk https://127.0.0.1:5001/pkg/ownCloud/status.php

# PROPFIND по новому пути (должно быть 207)
curl -sk -u admin:PASS -X PROPFIND -H "Depth: 1" \
  https://127.0.0.1:5001/pkg/ownCloud/remote.php/dav/files/admin/ | head

# OCS v2
curl -sk -u admin:PASS https://127.0.0.1:5001/pkg/ownCloud/ocs/v2.php/cloud/capabilities
```

## Откат шимов

```sh
cd /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud
cp -p remote.php.bak-davshim remote.php
rm -f dav-uploads-shim.php ocs/v2.php
```

## Мелочи

- В `/etc/pkg_service_conf/httpd_zld2.conf` в vhost 5001 временно включён
  `CustomLog /var/log/httpd/oc_access.log` (бэкап `.bak-log`). После отладки убрать
  и сделать `pkghttpd.sh reload`.
- В `data/owncloud.log` бывают `Unable to parse OCS content for app ...` —
  косметика при `appstoreenabled=false`.
