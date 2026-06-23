# Demos con fotos IA

Este paquete incluye `demo_ai_profiles.zip` con fotos ficticias generadas por IA para los usuarios demo.

Para cargarlo despues de actualizar el repositorio:

```powershell
Expand-Archive -Path .\demo_ai_profiles.zip -DestinationPath .\media\profiles -Force
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_profiles --reset --count 72
```

El comando borra usuarios demo/test anteriores y crea 72 usuarios demo nuevos con una sola foto principal.
