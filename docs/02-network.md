# Сеть, порты и обратный прокси

## Схема

```
Интернет ──► роутер ──► NAS:5001 (pkg_httpd, HTTPS, сертификат от своего CA)
                           ├── /pkg/ownCloud/     → PHP 5.5 (ownCloud 7, файлы на диске)
                           ├── /apps/sync/        → 127.0.0.1:5004  Syncthing GUI
                           ├── /apps/cops/        → 127.0.0.1:5005  COPS (PHP CLI)
                           ├── /apps/aria/        → 127.0.0.1:5006  AriaNg (PHP CLI)
                           ├── /apps/fb/          → 127.0.0.1:5007  FileBrowser
                           ├── /transmission/     → 127.0.0.1:5008  Transmission
                           └── /jsonrpc           → 127.0.0.1:6800  aria2
```

Наружу достаточно **одного** проброса: `34501 → 5001/TCP`. Всё остальное — внутри.

## Почему прокси, а не отдельные порты

Изначально каждый сервис жил на своём порту (5004–5008) и предполагалось пробросить
34502–34506. На практике:

- роутер упорно отдавал 34502–34506 на 5000/5001 (веб-админку NAS), а не на 5004–5008;
- на нестандартном порту веб-интерфейс ZyXEL ломается (`/DYNAMIC_STRING/desktop,/`, 404);
- для каждого сервиса пришлось бы держать отдельный TLS-сертификат.

`pkg_httpd` умеет `mod_proxy` (модули `mod_proxy.so` + `mod_proxy_http.so` уже
подгружаются в `/etc/pkg_service_conf/httpd2.conf`), поэтому все приложения были
повешены на пути под 5001. Побочный плюс: единый HTTPS с доверенным сертификатом.

## Правила прокси

Файл `/etc/pkg_service_conf/apps_proxy.conf` (подключается в конец `httpd2.conf`):

```
ProxyPass        /apps/sync/ http://127.0.0.1:5004/
ProxyPassReverse /apps/sync/ http://127.0.0.1:5004/
...
```

Плюс в `httpd2.conf` в строку `AuthZyxelSkipPattern` добавлены пути
`/apps/ /transmission/ /jsonrpc`, иначе `mod_auth_zyxel` заворачивает запросы
на форму логина NAS.

Перезагрузка без простоя:

```sh
/i-data/.system/zy-pkgs/pkg_httpd -t -f /etc/pkg_service_conf/httpd2.conf   # проверка
/etc/init.d/pkghttpd.sh reload
```

## Приложения и их «родные» порты

| Порт | Сервис | Путь через прокси |
|---|---|---|
| 5004 | Syncthing GUI (`--gui-address=0.0.0.0:5004`) | `/apps/sync/` |
| 5005 | COPS (`php-cli -S 0.0.0.0:5005`) | `/apps/cops/` |
| 5006 | AriaNg (`php-cli -S 0.0.0.0:5006` + router) | `/apps/aria/` |
| 5007 | FileBrowser (`-p 5007 -b /apps/fb`) | `/apps/fb/` |
| 5008 | Transmission (`rpc-port 5008`) | `/transmission/` |
| 6800 | aria2 JSON-RPC | `/jsonrpc` |
| 22001 | Syncthing sync (не через прокси) | — |
| 51413 | Transmission peer | — |

Порты **5002/5003 заняты** системным `DAV_httpd` (WebDAV), поэтому сервисы начинаются с 5004.

## Текущие пробросы на роутере

Проброс 34501 → 5001 — единственный обязательный. Остальные (34500, 34502–34506)
сейчас указывают на 5000/5001 и просто дублируют веб-интерфейс; вреда не несут.
Если понадобится прямой доступ к Syncthing (из-за WebSocket) — добавить
`34507 → 5004/TCP`.

## Важное ограничение

`mod_proxy_http` из Apache 2.2 **не умеет WebSocket**. Для Syncthing это значит:

- страница GUI и REST API работают;
- живые события (статус устройств, прогресс) не приходят — обновляйте страницу вручную.

Transmission, AriaNg, FileBrowser и COPS WebSocket не используют — у них всё в порядке.
