# Política de Seguridad

## Manejo de credenciales y archivos sensibles

Este proyecto utiliza credenciales de la API de Telegram y sesiones activas de usuario. Por seguridad, **nunca** incluyas en commits, pull requests ni issues:

- El archivo `.env` o cualquier variante `.env.*` con secretos reales (usa `.env.example` como plantilla).
- Archivos de sesión de Telethon (`*.session`, `*.session-journal`), ya que otorgan acceso directo a tu cuenta de Telegram.
- Claves de API de proveedores de IA (`TOGETHER_API_KEY` u otros tokens).
- Listas personales de canales privados o logs de descargas (`logs/`).

Si alguna credencial o archivo `.session` se expone accidentalmente:

1. Revoca la sesión activa desde **Telegram → Ajustes → Dispositivos** y regenera tu `API_HASH` en [my.telegram.org](https://my.telegram.org) si corresponde.
2. Rota cualquier API key comprometida (por ejemplo, en Together AI).
3. Elimina el archivo del historial de Git antes de volver a publicar.

## Reporte de vulnerabilidades

Si encuentras una vulnerabilidad de seguridad en este repositorio:

- **No** abras un issue público con los detalles del fallo o pruebas de concepto explotables.
- Repórtala de forma privada mediante **GitHub Security Advisories** (pestaña *Security → Advisories → Report a vulnerability*) o contactando directamente al mantenedor del repositorio.
- Incluye una descripción clara del problema, los pasos para reproducirlo y el posible impacto.
