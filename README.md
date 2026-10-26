# AECODE — Entregable 2

Aplicación web de análisis modal espectral con Streamlit. Permite modificar parámetros, importar masas y formas modales desde CSV, visualizar seis gráficos y exportar resultados a CSV, Excel y PDF.

## Ejecutar en Windows

Abre la carpeta del proyecto en VS Code. Desde su terminal PowerShell ejecuta:

```powershell
& E:\aecode_env\Scripts\python.exe -m streamlit run app.py --server.port 8510
```

Abre `http://localhost:8510`. El comando utiliza el entorno corto de AECODE configurado en Windows. Si aún no existe, créalo una sola vez y añade las dependencias:

```powershell
py -3.14 -m venv E:\aecode_env
& E:\aecode_env\Scripts\python.exe -m pip install -r requirements.txt
```

Evita ejecutar `app.py` con «Run Python File» de VS Code: la interfaz se inicia mediante `streamlit run`.

## Archivos incluidos

`app.py` inicia la aplicación. `motor_web.py`, `core/` y `funciones/` contienen los cálculos; `ui/` y `visualizaciones.py`, la interfaz y los gráficos. `exportacion.py` genera los informes. `datos/caso_original.csv` permite probar la importación. El informe y la infografía están incluidos.

El programa usa períodos y formas modales ingresados. No calcula un modelo estructural completo a partir de rigideces y apoyos.

## Publicación

Sube los archivos del proyecto (sin entornos virtuales) a GitHub. En Streamlit Community Cloud selecciona el repositorio y `app.py`. Comprueba la URL pública antes de entregar.
