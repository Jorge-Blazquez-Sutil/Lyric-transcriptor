# Empaquetar la aplicación en un .exe (Windows)

Requisitos:
- Tener Python 3 instalado y accesible vía `py`.
- Espacio suficiente en disco para la carpeta `dist`.

Pasos rápidos (PowerShell):

1. Abrir PowerShell en la raíz del proyecto:

```
cd "C:\Users\AlumnoB2\Documents\Becario\Scripts\Lyric transcriptor\Lyric-transcriptor"
```

2. Ejecutar el script de build:

```
.\build_exe.ps1
```

Nota: el script intentará descargar automáticamente una build estática de `ffmpeg`
si no encuentra una carpeta `ffmpeg` en el proyecto. El binario `ffmpeg.exe` y
`ffprobe.exe` serán incluidos en el bundle para evitar errores en equipos destino.

Qué hace el script:
- Crea o activa el `venv` en `./venv`.
- Actualiza `pip` y instala `pyinstaller` dentro del `venv`.
- Ejecuta `pyinstaller --onefile` empaquetando `app.py`.
- Incluye las carpetas `templates`, `static`, `uploads`, `results` y `ffmpeg` en el ejecutable.

Resultado:
- El ejecutable estará en `dist\LyricTranscriptor.exe`.

Notas y ajustes:
- Si tu aplicación necesita otros archivos o carpetas, añade más `--add-data "ruta;dest"` en `build_exe.ps1`.
- Para compilar desde CMD usa `pyinstaller` directamente con las mismas opciones (recuerda usar `;` como separador en Windows).
- El tamaño del ejecutable puede ser grande; considera usar `--onedir` si prefieres una carpeta en lugar de un solo exe.
