import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ge_path = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts\gen-env.ps1")
ge_text = ge_path.read_text(encoding="utf-8").replace("\r\n", "\n")

target_patterns = """$patterns = @(
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

clean_patterns = """$codePatterns = @(
    'os\\.(?:environ\\.get|getenv)\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']',
    'os\\.environ\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'process\\.env\\.([A-Za-z0-9_]+)',
    'process\\.env\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'import\\.meta\\.env\\.([A-Za-z0-9_]+)',
    'getenv\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\)',
    '\\$_ENV\\s*\\[\\s*["'']([A-Za-z0-9_]+)["'']\\s*\\]',
    'Environment\\.GetEnvironmentVariable\\s*\\(\\s*["'']([A-Za-z0-9_]+)["'']',
    '\\$env:([A-Za-z0-9_]+)'
)
$envFilePatterns = @(
    '(?m)^\\s*(?:export\\s+)?([A-Za-z_][A-Za-z0-9_]*)\\s*=',
    '\\$\\{([A-Za-z0-9_]+)\\}'
)"""

old_loop = """        foreach ($p in $patterns) {
            $matches = [regex]::Matches($content, $p)
            foreach ($m in $matches) {
                if ($m.Groups.Count -gt 1) {
                    $varName = $m.Groups[1].Value.Trim()
                    if ($varName.Length -gt 1 -and $systemVars -notcontains $varName.ToUpper()) {
                        [void]$detectedVars.Add($varName)
                    }
                }
            }
        }"""

new_loop = """        $activePatterns = [System.Collections.Generic.List[string]]::new()
        $activePatterns.AddRange($codePatterns)
        $isEnvOrShell = ($f.Extension -match "^\\.(env|sh|bash)$" -or $f.Name -like "*.env*")
        if ($isEnvOrShell) {
            $activePatterns.AddRange($envFilePatterns)
        }

        foreach ($p in $activePatterns) {
            $matches = [regex]::Matches($content, $p)
            foreach ($m in $matches) {
                if ($m.Groups.Count -gt 1) {
                    $varName = $m.Groups[1].Value.Trim()
                    if ($varName.Length -gt 1 -and $systemVars -notcontains $varName.ToUpper()) {
                        [void]$detectedVars.Add($varName)
                    }
                }
            }
        }"""

if target_patterns in ge_text:
    ge_text = ge_text.replace(target_patterns, clean_patterns)
    ge_text = ge_text.replace(old_loop, new_loop)
    ge_path.write_text(ge_text.replace("\n", "\r\n"), encoding="utf-8")
    print("Refined gen-env.ps1 patterns!")
else:
    print("target_patterns not found in gen-env.ps1")
