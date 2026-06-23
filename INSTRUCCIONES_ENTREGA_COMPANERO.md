# Entrega completa de Afinia

Estos pasos sirven para que tu compañero pueda levantar la misma web con la base de datos exportada y las imagenes.

## 1. Preparar el proyecto

```powershell
git clone URL_DEL_REPOSITORIO
cd Afinia
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d
```

## 2. Crear la base de datos

```powershell
python manage.py migrate
python manage.py loaddata fixtures\afinia_entrega_db.json
```

## 3. Restaurar imagenes

```powershell
Expand-Archive -Path .\media_entrega_extra.zip -DestinationPath . -Force
Expand-Archive -Path .\demo_ai_profiles_women.zip -DestinationPath .\media\profiles\demo_ai -Force
Expand-Archive -Path .\demo_ai_profiles_men.zip -DestinationPath .\media\profiles\demo_ai -Force
Expand-Archive -Path .\demo_ai_profiles_variants_1.zip -DestinationPath .\media\profiles\demo_ai\variants -Force
Expand-Archive -Path .\demo_ai_profiles_variants_2.zip -DestinationPath .\media\profiles\demo_ai\variants -Force
Expand-Archive -Path .\demo_ai_profiles_variants_3.zip -DestinationPath .\media\profiles\demo_ai\variants -Force
```

## 4. Arrancar la web

```powershell
python manage.py runserver 0.0.0.0:8000
```

La web quedara disponible en `http://127.0.0.1:8000/`.

## Comprobacion rapida

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

El archivo `.env` no se sube a GitHub. Cada ordenador debe tener el suyo.
