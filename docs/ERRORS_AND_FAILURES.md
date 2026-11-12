# База знаний ошибок, граблей и неудачных экспериментов (FAILURE LOG)
> **Назначение файла**: Полный реестр всех ошибочных решений, тупиковых гипотез и проверенных антипаттернов.
> **Правило разработчика**: ПЕРЕД любым изменением пинов, регистров или архитектуры ОБЯЗАТЕЛЬНО свериться с этим файлом!

---


---

### [Инцидент 2026-11-12 15:15:28] Windows PATH: php not found locally
- **Симптом и ущерб**: Running php -l in powershell failed with CommandNotFoundException
- **Причина (Root Cause)**: PHP CLI is not installed on Windows host, only on remote NAS
- **Решение и правило**: Check PHP syntax on NAS via SSH or python helper instead of Windows shell
