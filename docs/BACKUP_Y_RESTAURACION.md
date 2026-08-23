# Backup y restauración de PostgreSQL

Los respaldos se guardan fuera del volumen de PostgreSQL, en `backups/` del host, y no se versionan.

## Crear un backup

```powershell
.\scripts\backup-postgres.ps1
```

El script usa `pg_dump` en formato custom, verifica que el archivo no esté vacío y elimina respaldos con más de 14 días. La retención puede cambiarse con `-RetentionDays`.

Antes de un despliegue o migración sensible ejecutar el script y copiar el `.dump` a almacenamiento externo cifrado.

## Restaurar

Primero validar la restauración en una instancia de prueba:

```powershell
.\scripts\restore-postgres.ps1 -Backup .\backups\ipac-AAAAMMDD-HHMMSS.dump
```

La restauración limpia los objetos existentes, carga el respaldo y ejecuta `manage.py check`. Después verificar login, cantidad de alumnos, últimos pagos y cierres de caja antes de considerar válido el restore.

## Política mínima

- Backup diario y antes de cada despliegue con migraciones.
- Retención local de 14 días.
- Copia externa cifrada de al menos un backup semanal durante 3 meses.
- Prueba de restauración mensual en un entorno aislado.
