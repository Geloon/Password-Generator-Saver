Hola equipo,

Se reescribió el historial del repositorio para eliminar archivos sensibles (por ejemplo `main.exe`).

Acciones que debéis tomar en vuestro clone local:

1. Guardad cualquier trabajo local (commit en una rama, o `git stash`).
2. Reposiciona tu rama local a la versión remota:

```bash
git fetch origin
git checkout master
git reset --hard origin/master
```

3. Si tenéis forks públicos, considerad reclonar o reescribir vuestro fork.

Si necesitáis ayuda, responded a este mensaje y os guiaré.

Gracias.
