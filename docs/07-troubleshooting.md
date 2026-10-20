# Грабли и решения

Собрано по реальным ошибкам в процессе настройки.

## opkg

**`opkg` продолжает работать после выхода из SSH.**
Долгая установка не обрывается при закрытии сессии, а следующий `opkg install`
падает с «lock». Проверять:

```sh
ps w | grep opkg
```

и ждать, а не запускать второй раз.

## Рамдиск /tmp

`/tmp` — tmpfs. Composer, распаковка архивов и всё, что пишет больше ~50 МБ,
должно идти в `/i-data/45f1aca1/Apps/...`.

Симптом: `The disk hosting /tmp/.../vendor has less than 100MiB of free space`,
`syntax error: unexpected end of file` при распаковке.

## Демоны

`nohup` в системе **нет**. Запуск:

```sh
start-stop-daemon --start --background --make-pidfile --pidfile /opt/var/run/x.pid \
  --chuid admin --exec /opt/bin/x -- --args
```

`--background` обязателен, иначе start-stop-daemon не форкается и SSH-сессия висит.

## PHP / composer

- **`Call to undefined function filter_var()`** от composer — это не баг composer,
  а отсутствующий `php8-mod-filter`. Доставить также `intl`, `openssl`, `xml`, `ctype`.
- `create_function()` удалён в PHP 8 — COPS-патч в
  `vendor/seblucas/dot-php/doT.php`:
  `return @eval('return function ($it) { ' . $func . ' };');`
- В `sudo sh script.sh` **нет** `/opt/bin` в PATH. Всегда писать полные пути:
  `/opt/bin/php-cli`, `/opt/bin/curl`.

## pkg_httpd / прокси

- Проверка конфига требует библиотек PHP-пакета:

  ```sh
  LD_LIBRARY_PATH=/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/lib \
    /i-data/.system/zy-pkgs/pkg_httpd -t -f /etc/pkg_service_conf/httpd2.conf
  ```

- Без записи `/apps/ /transmission/ /jsonrpc` в `AuthZyxelSkipPattern`
  запросы уходят на форму логина ZyXEL (302 на `/r51209,...`).
- `mod_proxy_http` (Apache 2.2) не поддерживает WebSocket → Syncthing GUI
  без живых обновлений.
- Порт 5000 и 5001 — разные vhost'ы одного `pkg_httpd`; host-заголовок с портом
  может давать редирект на `http://host` без порта. Для внешнего доступа
  используем только 5001/HTTPS.

## Ошибка `/DYNAMIC_STRING/desktop,/` (404)

Это веб-интерфейс ZyXEL, а не наш сервис. Возникает, когда проброс ведёт на 80/5000
вместо 5004–5008. Лечится правильным внутренним портом или (как сейчас)
использованием общего прокси на 5001.

## FileBrowser

- `users add` молча возвращает rc=1 — не работает в этой сборке.
  Только `users import` с bcrypt-хешем.
- Go-библиотека bcrypt не принимает `$2y$` — менять на `$2a$`.
- CLI-команды падают с `Error: timeout`, пока демон держит Bolt DB.
  Останавливать сервис, делать операцию, запускать обратно.

## Transmission

`S88transmission` пишет «failed», хотя демон поднялся — гонка в `pidof`.
Ориентироваться на порт 5008 и `ps`.

## Syncthing

- Пакетный `S92syncthing` конфликтует со старым Syncthing из Pulse
  (`pidof syncthing` находит чужой процесс). Отключён, вместо него `S90syncthing`.
- Порт 22000 держит Pulse, поэтому синхронизация на 22001.
- CLI v2: только `--home`, нельзя `--config` + `--data`.
- Device ID — ровно 63 символа (8 групп по 7). 62 символа → «invalid device ID».

## Сеть

- Порты 5002/5003 заняты системным `DAV_httpd`.
- `127.0.0.1` внутри NAS — это не то же самое, что внешний IP; hairpin NAT
  с ПК работает, но проверять лучше и изнутри.
- Проброс проверяется только снаружи: `curl.exe -sk https://<WAN>:34501/...`.

## WinSCP / автоматизация

- Скрипты заливаются и запускаются так:

  ```
  put local.sh /tmp/x.sh
  call echo PASS | sudo -S sh /tmp/x.sh 2>&1
  ```

- В PowerShell-строках избегать `<`, `>` и кириллицы в `.ps1` (кодировка ломается).
- Файлы готовить в UTF-8 без BOM.
