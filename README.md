# Afinia

Aplicacion web Django para una comunidad inclusiva orientada a amistad, citas, grupos, planes y chats.

## Requisitos

- Python 3.9 o superior
- Docker Desktop
- Git

## Arranque local

1. Clonar el repositorio:
   ```powershell
   git clone URL_DEL_REPOSITORIO
   cd "chat citas amigos"
   ```

2. Crear y activar entorno virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instalar dependencias:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Crear configuracion local:
   ```powershell
   Copy-Item .env.example .env
   ```

5. Levantar PostgreSQL y Redis:
   ```powershell
   docker compose up -d
   ```

6. Migrar la base de datos:
   ```powershell
   python manage.py migrate
   ```

7. Cargar datos demo:
   ```powershell
   python manage.py loaddata fixtures\demo_data.json
   ```

8. Regenerar fotos demo locales:
   ```powershell
   python manage.py fill_random_profiles
   ```

9. Crear administrador si hace falta:
   ```powershell
   python manage.py createsuperuser
   ```

10. Arrancar la web con soporte de chat en tiempo real:
    ```powershell
    daphne config.asgi:application
    ```

La web quedara en `http://127.0.0.1:8000/`.

## Notas

- El archivo `.env` no se sube a GitHub porque contiene configuracion local.
- La carpeta `media/` no se sube porque puede contener imagenes subidas por usuarios.
- Los datos demo estan en `fixtures/demo_data.json`.
- Si se quiere reiniciar la base de datos desde cero, se puede borrar el volumen de Docker y repetir migraciones/carga de datos.
