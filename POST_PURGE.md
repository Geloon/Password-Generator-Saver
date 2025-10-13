## Instrucciones post-purga

Se reescribió el historial del repositorio para eliminar archivos sensibles (p. ej. `main.exe`) y se forzó el push al remoto. Sigue estas instrucciones si tienes un clone local:

Opciones recomendadas para sincronizar (elige una):

1) Clonar de nuevo (más simple y seguro):

```bash
git clone https://github.com/Geloon/Password-Generator-Saver.git
```

2) Reponer tu rama local para que coincida con el remoto (si tienes trabajo no publicado, guárdalo primero):

```bash
# Asegúrate de guardar cambios locales (stash o commit en una rama temporal)
git fetch origin
git checkout master
git reset --hard origin/master
```

Notas:
- Evita hacer `git pull` con merge automático mientras el historial sea reescrito; preferible `fetch` + `reset --hard`.
- Si tienes forks, deberán reclonarlos o reescribir sus propios forks.
