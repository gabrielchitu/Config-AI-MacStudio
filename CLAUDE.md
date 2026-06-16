# CLAUDE.md — Config-AI-MacStudio

## Token Optimization

Folosește `rtk` prefix pentru toate comenzile Bash (git, grep, find, ls etc.) — salvează ~60-90% tokens per comandă.

```bash
rtk git status
rtk git diff
rtk grep -r "pattern" .
rtk find . -name "*.json"
rtk ls -la
```

`python3` — RTK nu rescrie automat. Comprimă output cu pipe:
```bash
rtk proxy python3 script.py 2>&1 | rtk log
```

`rtk log` — grupează errors/warnings cu count, elimină duplicatele.

Meta comenzi RTK:
```bash
rtk gain              # Token savings analytics
rtk gain --history    # Istoric comenzi + savings
rtk discover          # Oportunități ratate din history
```

## Caveman Mode

Activ automat la fiecare sesiune (hook). Comunicare comprimată, fără filler, fără articole/pleasantries.
Dezactivare: `stop caveman` sau `normal mode`.
Nivele: `/caveman lite|full|ultra`
