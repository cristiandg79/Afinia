# Demos con fotos IA

Este paquete incluye varios ZIP `demo_ai_profiles_*.zip` con fotos ficticias generadas por IA para los usuarios demo.

Para cargarlo despues de actualizar el repositorio:

```powershell
Expand-Archive -Path .\demo_ai_profiles_women.zip -DestinationPath .\media\profiles\demo_ai -Force
Expand-Archive -Path .\demo_ai_profiles_men.zip -DestinationPath .\media\profiles\demo_ai -Force
Expand-Archive -Path .\demo_ai_profiles_variants_1.zip -DestinationPath .\media\profiles\demo_ai\variants -Force
Expand-Archive -Path .\demo_ai_profiles_variants_2.zip -DestinationPath .\media\profiles\demo_ai\variants -Force
Expand-Archive -Path .\demo_ai_profiles_variants_3.zip -DestinationPath .\media\profiles\demo_ai\variants -Force
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_profiles --reset --count 72
```

El comando borra usuarios demo/test anteriores y crea 72 usuarios demo nuevos con foto principal y fotos secundarias coherentes.
Las fotos secundarias son variantes de la misma imagen principal, para mantener los mismos rasgos.
