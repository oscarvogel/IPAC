# Despliegue de producción

## Preparación

1. Instalar Docker Engine, Compose v2, Git y `curl` en el servidor.
2. Clonar el repositorio y crear `backend/.env` a partir de `.env.example`.
3. Configurar claves, hosts, orígenes CORS y credenciales PostgreSQL reales.
4. Mantener `IPAC_RUN_SEED=0`, salvo en una instalación nueva controlada.

## Despliegue y actualización

Desde el servidor:

```bash
bash scripts/deploy-production.sh main
```

Desde una estación Windows con acceso SSH:

```powershell
.\scripts\deploy-over-ssh.ps1 -Server ipac.ejemplo.com -User deploy -RemotePath /opt/ipac -Branch main
```

El procedimiento crea primero un dump PostgreSQL fuera del contenedor, actualiza sólo con `fast-forward`, reconstruye imágenes, ejecuta migraciones y verifica los healthchecks HTTP. Si falla, vuelve al commit anterior y reconstruye los servicios. El backup no se restaura automáticamente para evitar sobrescribir datos sin revisión humana.

## Verificación

```bash
docker compose ps
docker compose logs --tail=200 backend frontend db
curl --fail http://127.0.0.1:8005/api/health/
curl --fail http://127.0.0.1:8084/healthz
```

Los volúmenes `postgres_data` y `media_data` conservan datos y archivos al recrear contenedores. Los logs rotan a cinco archivos de 10 MB por servicio.

## Rollback manual

```bash
git checkout --detach COMMIT_ANTERIOR
docker compose build
docker compose up -d
```

Si una migración requiere restaurar datos, seguir `BACKUP_Y_RESTAURACION.md` y validar primero el dump en una base de prueba.
