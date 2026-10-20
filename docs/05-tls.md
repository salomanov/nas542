# TLS

## Что используется

Один самоподписанный CA и один серверный сертификат на все демоны NAS.

| | |
|---|---|
| CA | `Zyxel NAS Root CA`, `C=RU, O=Home Network`, RSA 2048, до 15.10.2036 |
| Серверный | SAN: `IP:178.140.8.56`, `IP:192.168.1.50`, `IP:127.0.0.1`, `DNS:nas542.local`, `DNS:nas542` |
| Серийный | `4E415336`, до 17.10.2036 |
| Подпись | тем же CA |

Сертификат используется тремя демонами:

- `httpd` (веб-интерфейс, 80/443);
- `DAV_httpd` (WebDAV, 5002/5003);
- `pkg_httpd` (5000/5001 — ownCloud и все прокси-приложения).

## Файлы на NAS

| Путь | Что |
|---|---|
| `/etc/service_conf/CA.cer` | серверный сертификат + цепочка |
| `/etc/service_conf/CA_key.cer` | приватный ключ сервера |
| `/etc/zyxel/cert/CA.cer` | копия сертификата для веб-интерфейса |

Бэкапы оригиналов: `*.bak-20261020`.

## Файлы в репозитории

```
tls/
  root_ca.crt        — корневой CA (публичный, можно раздавать)
  chain.crt          — цепочка
  leaf_new.crt       — текущий серверный сертификат (SAN)
  leaf_old.crt       — старый (только CN=IP), для истории
  make-cert.sh       — генерация CA + первого сертификата
  install-leaf.sh    — выпуск серверного сертификата с SAN
  reissue-leaf.sh    — перевыпуск
  add-ca-api.ps1     — установка CA в хранилище Windows (текущий пользователь)
  add-ca-serialized.ps1
  install-ca-admin.cmd — установка CA в машинное хранилище (нужен админ)
  install-ca-machine.ps1
```

**Ключ CA (`zyxel_nas_ca.key`) в репозиторий не входит и на NAS не хранится.**
Он лежит офлайн у владельца (`D:\Загрузки\zyxel_nas_ca.key`).
Без него нельзя выпустить новый серверный сертификат — только использовать текущий.

## Установка сертификата

```sh
cp tls/leaf_new.crt /etc/service_conf/CA.cer
cp tls/leaf_new.crt /etc/zyxel/cert/CA.cer
# ключ уже на месте: /etc/service_conf/CA_key.cer
/etc/init.d/httpd.sh reload
/etc/init.d/davhttpd.sh reload
/etc/init.d/pkghttpd.sh reload
```

## Выпуск нового сертификата

Нужен ключ CA. На машине с openssl:

```sh
sh tls/install-leaf.sh          # создаёт leaf_new.crt с SAN
```

Затем скопировать на NAS (см. выше) и перезагрузить демоны.

## Клиенты

- **Windows**: `tls\install-ca-admin.cmd` от имени администратора (машинное хранилище),
  иначе WebDAV-диск не подключится.
- **Android**: сертификат можно скачать из облака —
  `https://host:34501/pkg/ownCloud/remote.php/webdav/Zyxel-NAS-CA.crt`
  и установить как «сертификат ЦС».
- **iOS**: установить профиль вручную, затем «О сертификате» → доверять.

## Проверка

```sh
openssl s_client -connect 192.168.1.50:5001 -servername nas542.local </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -ext subjectAltName -dates
```
