# Восстановление после сброса

Сценарий: NAS сброшен к заводским настройкам (или заменён диск/система).
Цель — вернуть ownCloud и все сервисы.

Время: ~15–20 минут, из них большая часть — `opkg install` и `composer`.

---

## 0. Предварительно

Нужно с ПК:

- WinSCP (`C:\Program Files (x86)\WinSCP\WinSCP.com`);
- git;
- клон репозитория;
- `scripts/00-secrets.env` с паролями (в репозитории его нет — хранится отдельно);
- ключ CA, если понадобится перевыпускать сертификат (обычно не нужен, текущий
  сертификат просто копируется).

На NAS:

- включён SSH (веб-интерфейс → Network → Terminal), порт 22;
- NAS в сети, есть интернет.

---

## 1. Вернуть системные пакеты ZyXEL

Через веб-интерфейс NAS (App Center / Пакеты) поставить:

1. **PHP-MySQL-phpMyAdmin** — от него зависит `pkg_httpd` (`libphp5.so`, PHP 5.5).
2. **ownCloud** — сам сервер 7.0.15.
3. **Entware-ng** (из MetaRepository) — окружение `/opt`.

Без PHP-пакета `pkg_httpd` не стартует, без Entware нет `opkg`.

Проверка:

```sh
ls /opt/bin/opkg                                   # Entware
ls /i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/lib/libphp5.so
ls /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/index.php
```

Если Entware ставился вручную — распаковать
`Entware-ng_armv7sf-k3.2_*.tar.gz` в `/i-data/45f1aca1/.PKG/Entware-ng`,
симлинк `/opt` и автозапуск делает установщик пакета.

---

## 2. Секреты

```powershell
copy scripts\00-secrets.env.example scripts\00-secrets.env
notepad scripts\00-secrets.env
```

Заполнить: внешний IP, пароль `admin`, пароли для FileBrowser/Transmission/aria2/Syncthing.
Файл в `.gitignore` — в репозиторий не попадёт.

---

## 3. Установка сервисов

```powershell
.\scripts\tools\deploy.ps1
```

Скрипт заливает `scripts/` и `configs/` в `/tmp/nas542` и запускает
`install-all.sh` под sudo. Шаги идут по порядку:

| Шаг | Что делает |
|---|---|
| 01 | проверяет Entware и `opkg` |
| 02 | `opkg update` + установка пакетов (может идти 10+ минут) |
| 03 | Syncthing: init, GUI-пароль, папка `apps` |
| 04 | FileBrowser: конфиг, БД, пользователь |
| 05 | Transmission: каталоги, settings.json |
| 06 | aria2 + AriaNg |
| 07 | COPS: composer, патч PHP 8, конфиг |
| 08 | `mod_proxy` в pkg_httpd |

Отдельный шаг:

```powershell
.\scripts\tools\deploy.ps1 -Script 08-httpd-proxy.sh
```

---

## 4. Шимы ownCloud

```powershell
.\scripts\tools\deploy.ps1 -Script 09-owncloud-shims.sh
```

Скрипт делает бэкап `remote.php.bak-davshim`, вставляет блок `OC10-DAV-SHIM`,
кладёт `dav-uploads-shim.php` и создаёт `ocs/v2.php`.

Проверка:

```sh
curl -sk https://127.0.0.1:5001/pkg/ownCloud/status.php
curl -sk -u admin:PASS -X PROPFIND -H "Depth: 1" \
  https://127.0.0.1:5001/pkg/ownCloud/remote.php/dav/files/admin/
```

---

## 5. TLS

Если сертификат на NAS отсутствует или старый (без SAN):

```sh
cp tls/leaf_new.crt /etc/service_conf/CA.cer
cp tls/leaf_new.crt /etc/zyxel/cert/CA.cer
/etc/init.d/httpd.sh reload
/etc/init.d/davhttpd.sh reload
/etc/init.d/pkghttpd.sh reload
```

Приватный ключ `/etc/service_conf/CA_key.cer` после сброса может остаться прежним —
тогда достаточно положить только сертификат.

Бэкапы перед заменой: `cp -p /etc/service_conf/CA.cer /etc/service_conf/CA.cer.bak-$(date +%Y%m%d)`.

---

## 6. Роутер

Единственный обязательный проброс:

```
TCP 34501 → 192.168.1.50:5001
```

Плюс SSH `34522 → 22`, если нужен доступ снаружи.

Для прямого Syncthing (WebSocket) можно добавить `34507 → 5004`.
Остальные пробросы не нужны.

---

## 7. Проверка

```powershell
.\scripts\tools\deploy.ps1 -Script tools/healthcheck.sh
```

Скрипт проверяет порты, HTTP-коды, RPC aria2/Transmission, OPDS-фид и Syncthing REST.

Ожидаемый результат — все пункты `OK`.

---

## 8. Клиенты

- **ownCloud Android 2.14.2**: сервер `https://<host>:34501/pkg/ownCloud`, логин `admin`.
- **Syncthing на телефоне**: добавить устройство NAS и принять папку `Apps`.
  Device ID NAS: `curl -s -H "X-API-Key: $KEY" http://127.0.0.1:5004/rest/system/status`
  (поле `myID`).
- **OPDS**: `https://<host>:34501/apps/cops/feed.php`.

---

## Если что-то пошло не так

Смотри [07-troubleshooting.md](07-troubleshooting.md). Основное:

- `opkg` занят другим процессом — дождаться (`ps w | grep opkg`), не запускать дважды;
- composer падает на `filter_var` — не хватает `php8-mod-filter`;
- `no space left` — сборка попала в `/tmp` (рамдиск);
- 404 `/DYNAMIC_STRING/desktop,/` — попал не на тот порт, это админка ZyXEL.
