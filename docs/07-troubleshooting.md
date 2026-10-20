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

## BOM в конфигах

Windows-редакторы (и `Set-Content -Encoding utf8` в PowerShell 5.1) пишут UTF-8 с BOM.
Для PHP это фатально: BOM попадает в вывод до `header()`, и страница падает с
`Cannot modify header information - headers already sent by (...config_local.php:1)`.
Для shell-конфигов BOM ломает первую строку (`#: not found`).

`scripts/lib.sh` при рендеринге конфигов вырезает BOM. Если правите файлы вручную —
сохраняйте без BOM (UTF-8 no BOM). Проверка:

```sh
head -c 3 file | hexdump -C     # не должно быть ef bb bf
```

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

## COPS

- **Пароль не принимается, хотя введён верный.** COPS работает под `php -S`, а
  встроенный сервер не всегда заполняет `$_SERVER['PHP_AUTH_USER']`, и проверка
  в `config.php` всегда видит пустого пользователя. Лечится в `config_local.php`
  (этот блок уже есть в шаблоне): разобрать `HTTP_AUTHORIZATION` вручную **до**
  проверки, потому что `config_local.php` подключается раньше неё.

  ```php
  if (!isset($_SERVER['PHP_AUTH_USER']) && !empty($_SERVER['HTTP_AUTHORIZATION'])
      && preg_match('/^Basic\s+(.+)$/i', $_SERVER['HTTP_AUTHORIZATION'], $m)) {
      $pair = base64_decode($m[1]);
      if (strpos($pair, ':') !== false) {
          list($_SERVER['PHP_AUTH_USER'], $_SERVER['PHP_AUTH_PW']) = explode(':', $pair, 2);
      }
  }
  ```

- **Своя тема не подхватилась.** `cops_template` — это *имя каталога* в `templates/`.
  Каталог `nas542` должен содержать все файлы bootstrap (`header/footer/main/page/
  bookdetail/suggestion/file.html`, `scripts/`, `styles/`), иначе клиентский рендер
  молча ничего не выведет. CSS подключается в `file.html`: у bootstrap там нет
  ссылки на `current_css`, поэтому свой `<link>` добавляется вручную.

- **Клиент OPDS не видит книгу.** Проверьте `feed.php` с паролем
  (`curl -u user:pass .../feed.php`): без авторизации COPS отдаёт `401` и пустое тело.

- **Каталог выглядит как голый HTML из 2005-го, тема «пропала».** Скорее всего в браузере
  осталась cookie `template` (например `default`) от экспериментов с переключением
  шаблонов: COPS читает cookie раньше конфига. Откройте шестерёнку → «Шаблон интерфейса» →
  `NAS542 (с логотипом)` и обновите страницу (`Ctrl+F5`). Если шестерёнки не видно —
  зайдите напрямую на `index.php?page=19`.

- **Настройки на `index.php?page=19` не применяются.** Они хранятся в cookie этого
  браузера и вступают в силу после перезагрузки страницы; в другом браузере/режиме
  инкогнито их не будет. Если список шаблонов пуст — патч `lib/PageCustomize.php`
  не применился: перезапустите `07-cops.sh`.

- **`/apps/cops/` редиректит на `/ui/`, а нужен старый экран.** Так и задумано: редирект
  срабатывает только когда в запросе нет `page/query/id/db`. Старый шаблон —
  `index.php?page=1`, настройки COPS (тема, язык, стиль) — `index.php?page=19`,
  OPDS — `feed.php`.

- **Новый интерфейс пустой: «Не удалось загрузить каталог».** Проверьте API с паролем:
  `curl -u user:pass 'http://127.0.0.1:5005/ui/api.php?action=list&limit=1'`. Если там
  `500` — `metadata.db` недоступна для чтения (права/битый файл), если `401` — не
  разобрался `Authorization` (см. пункт выше), если JSON есть, а полка пустая —
  смотрите консоль браузера (например, старый кэш `app.js`, лечится `Ctrl+F5`).

## Импортёр книг

- **Файл лежит в `inbox`, но ничего не происходит, лог пустой.** Демон
  `S91bookimport` работает от `admin`, а лог-файл/каталоги созданы `root` — шелл не
  может открыть `>>log`, команда не запускается, и ошибка уходит в `/dev/null`.
  В `07-cops.sh` есть `chown admin:root` для `Apps/logs` и `Apps/calibre`; проверка:

  ```sh
  ls -l /i-data/45f1aca1/Apps/logs/bookimport.log
  tail -f /i-data/45f1aca1/Apps/logs/bookimport.log
  ```

- **`Permission denied` при заливке в inbox по SFTP.** Каталог создан скриптом под
  `root`, у `admin` нет прав на запись — тот же `chown -R admin:root`.

- **Книга «не появилась».** Дубликат по паре «название + автор» пропускается и уезжает в
  `inbox/_skipped/`. PDF/MOBI/AZW3 импортируются без метаданных (название = имя файла,
  автор `Unknown`) — так и задумано, парсера PDF на этой машине нет.

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
