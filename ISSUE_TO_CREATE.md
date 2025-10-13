Title: Repository history rewritten to remove sensitive files

Body:
Hola equipo,

He reescribido el historial del repositorio para eliminar archivos sensibles (por ejemplo `main.exe`). El cambio ya se empujó al remoto y hay una etiqueta `purge-20251013` que marca el punto.

Pasos que debéis tomar en vuestro clone local:

1. Guardad cualquier trabajo local (commit en una rama, o `git stash`).
2. Reposiciona tu rama local a la versión remota:

```bash
git fetch origin
git checkout master
git reset --hard origin/master
```

3. Si tenéis forks, considerad reclonarlos o reescribir vuestro fork.

Si necesitáis ayuda, responded a este mensaje y os guiaré.

Gracias.
