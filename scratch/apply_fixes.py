import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

scripts_dir = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts")

# --- 1. Fix checkpoint.ps1 ---
cp_path = scripts_dir / "checkpoint.ps1"
cp_text = cp_path.read_text(encoding="utf-8")

# Extract the old verify block and remove it
old_verify_block = """# 4.2. Верификация тестов (-Verify)
if ($Verify) {
    Write-Host "`n=== [Project Guardian] Запуск верификации тестов (-Verify) ===" -ForegroundColor Cyan
    $testPassed = $true
    $testFound = $false

    # Проверка Python тестов
    if (Test-Path (Join-Path $ProjectPath "tests") -or (Get-ChildItem -Path $ProjectPath -Filter "test_*.py" -Recurse -File -ErrorAction SilentlyContinue)) {
        $testFound = $true
        Write-Host "Обнаружены тесты Python. Запуск pytest..." -ForegroundColor Gray
        & python -m pytest $ProjectPath -q 2>$null
        if ($LASTEXITCODE -ne 0) { $testPassed = $false }
    }

    # Проверка npm test
    $pkgJson = Join-Path $ProjectPath "package.json"
    if (-not $testFound -and (Test-Path $pkgJson)) {
        try {
            $pkg = Get-Content $pkgJson -Raw | ConvertFrom-Json
            if ($pkg.scripts.test -and $pkg.scripts.test -notmatch "no test specified") {
                $testFound = $true
                Write-Host "Обнаружен npm test. Запуск..." -ForegroundColor Gray
                & npm test --prefix $ProjectPath --silent 2>$null
                if ($LASTEXITCODE -ne 0) { $testPassed = $false }
            }
        } catch {}
    }

    if ($testFound) {
        if (-not $testPassed) {
            Write-Error "Верификация тестов провалена! Устраните ошибки перед сохранением чекпоинта."
            return
        } else {
            Write-Host "[OK] Все тесты успешно пройдены!" -ForegroundColor Green
        }
    } else {
        Write-Host "Тесты в проекте не обнаружены, проверка пропущена." -ForegroundColor Gray
    }
}"""

# New verify block to insert before "# 3. Создание бэкапа"
new_verify_block = """# 2.5. Верификация тестов перед созданием бэкапа (-Verify)
if ($Verify) {
    Write-Host "`n=== [Project Guardian] Запуск верификации тестов (-Verify) ===" -ForegroundColor Cyan
    $testPassed = $true
    $testFound = $false

    # Проверка Python тестов: папка tests/ или test/, либо файлы в корне (без тяжелой рекурсии)
    $hasPyTestDir = (Test-Path (Join-Path $ProjectPath "tests")) -or (Test-Path (Join-Path $ProjectPath "test"))
    $pyTestFiles = @()
    if ($hasPyTestDir) {
        $testFound = $true
    } else {
        $pyTestFiles = Get-ChildItem -Path $ProjectPath -Filter "test_*.py" -File -Depth 2 -ErrorAction SilentlyContinue | Where-Object {
            $_.FullName -notmatch "[\\\\/](\\.git|\\.backups|node_modules|\\.venv|venv|scratch)[\\\\/]"
        }
        if ($pyTestFiles.Count -gt 0) { $testFound = $true }
    }

    if ($testFound) {
        Write-Host "Обнаружены тесты Python. Запуск тестов..." -ForegroundColor Gray
        $null = & python -c "import pytest" 2>$null
        if ($LASTEXITCODE -eq 0) {
            & python -m pytest $ProjectPath -q
            if ($LASTEXITCODE -ne 0) { $testPassed = $false }
        } else {
            & python -m unittest discover -s $ProjectPath -q 2>$null
            if ($LASTEXITCODE -ne 0) { $testPassed = $false }
        }
    }

    # Проверка npm test
    $pkgJson = Join-Path $ProjectPath "package.json"
    if (-not $testFound -and (Test-Path $pkgJson)) {
        try {
            $pkg = Get-Content $pkgJson -Raw | ConvertFrom-Json
            if ($pkg.scripts.test -and $pkg.scripts.test -notmatch "no test specified") {
                $testFound = $true
                Write-Host "Обнаружен npm test. Запуск..." -ForegroundColor Gray
                & npm test --prefix $ProjectPath --silent 2>$null
                if ($LASTEXITCODE -ne 0) { $testPassed = $false }
            }
        } catch {}
    }

    if ($testFound) {
        if (-not $testPassed) {
            Write-Error "Верификация тестов провалена! Устраните ошибки перед сохранением чекпоинта."
            return
        } else {
            Write-Host "[OK] Все тесты успешно пройдены!" -ForegroundColor Green
        }
    } else {
        Write-Host "Тесты в проекте не обнаружены, проверка пропущена." -ForegroundColor Gray
    }
}
"""

# Normalize newlines
cp_text_norm = cp_text.replace("\r\n", "\n")
old_verify_norm = old_verify_block.replace("\r\n", "\n")

if old_verify_norm in cp_text_norm:
    cp_text_norm = cp_text_norm.replace(old_verify_norm, "")
    target_pos = "# 3. Создание бэкапа"
    if target_pos in cp_text_norm:
        cp_text_norm = cp_text_norm.replace(target_pos, new_verify_block + "\n" + target_pos)
        cp_path.write_text(cp_text_norm.replace("\n", "\r\n"), encoding="utf-8")
        print("Successfully updated checkpoint.ps1 (-Verify moved before backup creation).")
    else:
        print("Target '# 3. Создание бэкапа' not found in checkpoint.ps1!")
else:
    print("Old verify block not found in checkpoint.ps1!")

# --- 2. Fix clean-backups.ps1 ---
cb_path = scripts_dir / "clean-backups.ps1"
cb_text = cb_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_cb_logic = """$cutoffDate = (Get-Date).AddDays(-$MaxAgeDays)
$candidateFolders = $toDelete | Where-Object { $_.CreationTime -lt $cutoffDate -or $checkpoints.Count -gt ($KeepCount * 2) }

if ($candidateFolders.Count -eq 0) {
    # Если старых по дням нет, но превышение большое — удаляем самые старые сверх лимита
    $candidateFolders = $toDelete
}"""

new_cb_logic = """$cutoffDate = (Get-Date).AddDays(-$MaxAgeDays)
# Удаляем только те, что превышают лимит $KeepCount И при этом старше $MaxAgeDays, либо если превышен жесткий лимит 2x KeepCount
$candidateFolders = $toDelete | Where-Object { $_.CreationTime -lt $cutoffDate -or $checkpoints.Count -gt ($KeepCount * 2) }

if (-not $candidateFolders -or $candidateFolders.Count -eq 0) {
    Write-Host "Свежие чекпоинты защищены: нет чекпоинтов старше $MaxAgeDays дней (и общее число $($checkpoints.Count) <= жесткого лимита $($KeepCount * 2))." -ForegroundColor Green
    return
}"""

if old_cb_logic in cb_text:
    cb_text = cb_text.replace(old_cb_logic, new_cb_logic)
    cb_path.write_text(cb_text.replace("\n", "\r\n"), encoding="utf-8")
    print("Successfully updated clean-backups.ps1 (retention logic fixed).")
else:
    print("Old retention logic not found in clean-backups.ps1!")

# --- 3. Fix gen-env.ps1 ---
ge_path = scripts_dir / "gen-env.ps1"
ge_text = ge_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_patterns = """$patterns = @(
    'os\\.(?:environ\\.get|getenv)\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']',
    'os\\.environ\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'process\\.env\\.([A-Za-z0-9_]+)',
    'process\\.env\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'import\\.meta\\.env\\.([A-Za-z0-9_]+)',
    'getenv\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\)',
    '\\$_ENV\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'Environment\\.GetEnvironmentVariable\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']'
)"""

new_patterns = """$patterns = @(
    'os\\.(?:environ\\.get|getenv)\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']',
    'os\\.environ\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'process\\.env\\.([A-Za-z0-9_]+)',
    'process\\.env\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'import\\.meta\\.env\\.([A-Za-z0-9_]+)',
    'getenv\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\)',
    '\\$_ENV\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'Environment\\.GetEnvironmentVariable\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']',
    '(?m)^\\s*(?:export\\s+)?([A-Za-z_][A-Za-z0-9_]*)\\s*=',
    '\\$env:([A-Za-z0-9_]+)',
    '\\$\\{([A-Za-z0-9_]+)\\}'
)"""

if old_patterns in ge_text:
    ge_text = ge_text.replace(old_patterns, new_patterns)
    ge_path.write_text(ge_text.replace("\n", "\r\n"), encoding="utf-8")
    print("Successfully updated gen-env.ps1 (added support for .env, .sh, $env:).")
else:
    print("Old patterns not found in gen-env.ps1!")

# --- 4. Fix prepare-handoff.ps1 ---
ph_path = scripts_dir / "prepare-handoff.ps1"
ph_text = ph_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_handoff_prompt = """# Генерация готового промпта для нового диалога
$handoffPrompt = @"
Привет! Мы продолжаем работу над проектом '$projectName' в папке: $ProjectPath
Ветка Git: $branch | Последний коммит: $lastCommit
Задача на текущую сессию: $taskGoal

Пожалуйста, первым делом прочитай PROJECT_STATE.md для загрузки полной памяти проекта и подтверди готовность к задаче.
"@

# Сохранение в .agents/HANDOFF.md
$handoffFile = Join-Path $agentsDir "HANDOFF.md"
$handoffDoc = @"
# Контекст передачи проекта в новый диалог (Handoff)

- **Проект**: $projectName ($ProjectPath)
- **Дата формирования**: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
- **Ветка Git**: $branch
- **Последний коммит**: $lastCommit

---"""

new_handoff_prompt = """# Генерация готового промпта для нового диалога
$handoffPrompt = @"
Привет! Мы продолжаем работу над проектом '$projectName' в папке: $ProjectPath
Стек: $stackInfo | Ветка Git: $branch | Последний коммит: $lastCommit
Контекст изменений: $recentChanges
Задача на текущую сессию: $taskGoal

Пожалуйста, первым делом прочитай PROJECT_STATE.md для загрузки полной памяти проекта и подтверди готовность к задаче.
"@

# Сохранение в .agents/HANDOFF.md
$handoffFile = Join-Path $agentsDir "HANDOFF.md"
$handoffDoc = @"
# Контекст передачи проекта в новый диалог (Handoff)

- **Проект**: $projectName ($ProjectPath)
- **Дата формирования**: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
- **Стек**: $stackInfo
- **Ветка Git**: $branch
- **Последний коммит**: $lastCommit
- **Последние изменения**: $recentChanges

---"""

if old_handoff_prompt in ph_text:
    ph_text = ph_text.replace(old_handoff_prompt, new_handoff_prompt)
    ph_path.write_text(ph_text.replace("\n", "\r\n"), encoding="utf-8")
    print("Successfully updated prepare-handoff.ps1 (integrated stackInfo and recentChanges).")
else:
    print("Old handoff prompt not found in prepare-handoff.ps1!")
