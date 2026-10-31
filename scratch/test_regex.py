import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# In regex, to match either quote, we don't even need ["']. We can use ["'] using double-quoted string in PS:
# or in regex: ["\'] or ['"]
# If in PowerShell we use double quotes: "os\.(?:environ\.get|getenv)\s*\(\s*[`"']([A-Za-z0-9_]+)[`"']"
# OR in PowerShell single quotes: '["' + "'" + ']'
# Even simpler: in regex, quotes in Python/JS are either ' or " or `
# We can match: 'os\.(?:environ\.get|getenv)\s*\(\s*["' + "']([A-Za-z0-9_]+)"
# Or even better in PowerShell:
# 'os\.(?:environ\.get|getenv)\s*\(\s*["\x27]([A-Za-z0-9_]+)["\x27]'
# In regex, \x27 IS the single quote character '!
# \x22 IS the double quote character "!
# So ["\x27] in regex matches either double quote or single quote!
# And it contains ZERO single quotes in PowerShell!
print(r"Regex with \x27: 'os\.(?:environ\.get|getenv)\s*\(\s*[" r"\x27]([A-Za-z0-9_]+)[" r"\x27]'")
