# Железо и система

| Параметр | Значение |
|---|---|
| Модель | ZyXEL NAS542 |
| CPU | Marvell Armada 380 88F6820, ARMv7, 2 × 1.3 ГГц |
| RAM | 1 ГБ |
| Swap | 2 ГБ |
| Ядро | Linux 3.2.54 armv7l |
| Системный том | `/i-data/45f1aca1` (1.8 ТБ свободно) |
| Диски | 4 отсека, RAID (md) |

## Особенности платформы

- **Нет Docker** и не будет: ядро 3.2, cgroups нет.
- **glibc 2.27**, пакеты Entware — `armv7sf-k3.2`.
- Entware живёт в `/i-data/45f1aca1/.PKG/Entware-ng`, в системе виден как `/opt`.
  Автозапуск: `/i-data/45f1aca1/.PKG/Entware-ng/etc/init.d/Entware-ng`.
- Пакеты ZyXEL (ownCloud, PHP 5.5) лежат в `/i-data/45f1aca1/.PKG/`,
  их конфиги — в `/etc/pkg_service_conf/`.
- **`/tmp` — рамдиск** (tmpfs). Тяжёлые сборки (composer, распаковка) делаем только
  в `/i-data/...`, иначе «no space left».
- **`nohup` отсутствует** — демоны запускаем через
  `start-stop-daemon --background --make-pidfile --chuid`.
- **`gcc` отсутствует** — всё ставится только готовыми пакетами opkg.
  Собрать что-то из исходников на NAS нельзя.

## Память

После запуска всех сервисов:

```
total 988 MB, used ~900 MB, free ~90 MB, swap не тронут
```

Syncthing — самый прожорливый (~60 МБ RSS), остальные по 30–50 МБ.
Если запускать ещё что-то тяжёлое (например Calibre-Web на Python), начнётся активный swap
и NAS станет вялым. Это одна из причин, почему выбран COPS на PHP.
