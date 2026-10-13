# Despliegue y migración (Fase 10)

## Preparación
1. Backup local: `python scripts/backup_db.py superchampion.db`
2. Backup Turso: `turso db shell <db> .dump > backup_$(date +%F).sql`
3. Ejecutar tests: `venv/bin/python -m unittest discover -s tests -t .` (usan una BD temporal, nunca la de producción).

## Migración
- `inicializar_db()` crea anios, campeonatos, copas, campeonato_permisos y siembra año/campeonato/copa/torneo por defecto.
- BD antigua (sin `copa_id`): ejecutar `backend/database/migration_torneo_hierarchy.py` y `migration_add_campeonatos.py`.

## Checklist de validación post-despliegue
- [ ] La app abre y muestra Año/Campeonato/Copa/Torneo
- [ ] Crear/editar/eliminar en cada nivel
- [ ] Jornada con Lugar y Horario
- [ ] Permisos por campeonato (modal "Permisos")
- [ ] Datos previos visibles tras migrar

## Rollback
Restaurar el archivo `.backup_*` (local) o ejecutar el `.dump` SQL en una BD nueva de Turso y actualizar `TURSO_URL`.
