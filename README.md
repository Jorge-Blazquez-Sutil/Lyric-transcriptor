# Lyric Transcriptor

**Aplicación web para descargar audio de URLs, separar vocales y transcribir letras automáticamente.**

## Descripción General

Lyric Transcriptor es una herramienta que automatiza el proceso de transcripción de audio desde diversas plataformas. Descarga canciones desde URLs (SoundCloud, YouTube, etc.), separa las vocales usando modelos de deep learning (Demucs), y transcribe el texto mediante OpenAI Whisper.

La aplicación está diseñada para procesar lotes de URLs desde archivos Excel o CSV, generando un archivo ZIP con las transcripciones y archivos de audio separados.

---

## Características Principales

- ✅ Descarga de audio desde múltiples plataformas (SoundCloud, YouTube, etc.)
- ✅ Separación automática de vocales e instrumentales (Demucs - modelo htdemucs)
- ✅ Transcripción de letras con modelo Whisper (OpenAI)
- ✅ Interfaz web intuitiva (Flask)
- ✅ Procesamiento en lote de múltiples URLs
- ✅ Exportación de resultados en ZIP
- ✅ Empaquetado como ejecutable Windows (.exe)

---

## Instalación

### Requisitos Previos

- **Python 3.12+**
- **Git** (opcional, para clonar)
- **Espacio en disco**: ~5-10 GB (modelos de Whisper y Demucs)

### Opción 1: Ejecutable Windows (Recomendado para usuarios finales)

1. Descarga `LyricTranscriptor.exe` desde la carpeta `dist/`
2. Ejecuta el archivo
3. Abre tu navegador en `http://localhost:5000`

**Nota**: La primera ejecución puede tardar unos minutos mientras descarga modelos.

### Opción 2: Desde el código fuente

1. Clona o descarga el repositorio:
   ```bash
   git clone <url-repo>
   cd Lyric-transcriptor
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta la aplicación:
   ```bash
   python app.py
   ```

5. Abre tu navegador en `http://localhost:5000`

---

## Uso

### Interfaz Web

1. **Cargar archivo**: Selecciona un archivo Excel (.xlsx) o CSV (.csv) con URLs de audio
   - El archivo debe contener una columna llamada `URL`
   - Opcionalmente, puede incluir una columna `PLATAFORMA` (p.ej., "SoundCloud", "YouTube")

2. **Procesar**: Haz clic en "Transcribir"
   - La aplicación muestra progreso en tiempo real
   - Logs detallados del proceso

3. **Descargar**: Una vez completo, descarga el ZIP con:
   - Archivos `.txt` con transcripciones
   - Carpetas con audio separado (voces e instrumentales)

### Ejemplo de archivo CSV/Excel

| URL | PLATAFORMA |
|-----|-----------|
| https://soundcloud.com/artist/song-123 | SoundCloud |
| https://www.youtube.com/watch?v=abc123 | YouTube |

---

## Módulos y Funcionalidades

### 1. **app.py** (Servidor Flask)

**Rol**: Núcleo de la aplicación web

**Funciones principales**:
- `Flask` - Servidor HTTP en puerto 5000
- `process_file()` - Procesa archivo Excel/CSV en segundo plano (hilo)
- `/upload` - Endpoint para cargar archivos
- `/progress/<job_id>` - SSE (Server-Sent Events) para actualizar progreso en tiempo real
- `/download/<filename>` - Descarga ZIP de resultados

**Características especiales**:
- Ruta base adaptativa: usa `sys._MEIPASS` cuando está empaquetado, directorio local en modo desarrollo
- Logging a `app.log` para diagnóstico
- Manejo de rutas absolutas para ffmpeg y Demucs en entornos empaquetados

---

### 2. **downloader.py** (Descarga de Audio)

**Rol**: Descarga audio desde URLs

**Funciones principales**:
- `download_audio_from_url(url, output_dir, platform=None)` - Descarga audio
  - Usa `yt-dlp` internamente
  - Soporta múltiples plataformas (SoundCloud, YouTube, Spotify, etc.)
  - Convierte a MP3 automáticamente
  - Retorna ruta al archivo descargado o `None` si falla

**Parámetros**:
- `url` (str): URL de la canción
- `output_dir` (str): Carpeta donde guardar
- `platform` (str, opcional): Plataforma explícita para optimizar descarga

---

### 3. **audio_separator.py** (Separación de Vocales)

**Rol**: Aísla voces e instrumentales usando Demucs

**Funciones principales**:
- `separate_audio(audio_path, output_base_dir="separated_audio")` - Separa pistas
  - Usa modelo `htdemucs` (Hybrid Transformer Demucs)
  - Guarda voces, batería, bajo, otros en carpetas separadas
  - Retorna ruta al archivo de voces (vocals.mp3)

**Estructura de salida**:
```
output_base_dir/
  htdemucs/
    song_name/
      vocals.mp3        ← Voces aisladas
      drums.mp3
      bass.mp3
      other.mp3
```

**Tecnología**: 
- Demucs v4 (facebook/demucs)
- Modelo: htdemucs (rápido y buena calidad)
- Salida: MP3 (evita problemas con TorchCodec)

---

### 4. **transcriber.py** (Transcripción de Audio)

**Rol**: Convierte audio a texto usando OpenAI Whisper

**Funciones principales**:
- `get_model(model_size)` - Carga modelo Whisper en caché
  - Tamaños disponibles: 'tiny', 'base', 'small', 'medium', 'large'
  - Evita recargar modelos para múltiples archivos
  
- `transcribe_audio(audio_path, model_size='large', use_separation=True)` - Transcribe audio
  - Usa audio separado (voces) si disponible
  - Retorna texto transcrito o mensaje de error

**Modelos disponibles**:
| Modelo | Tamaño | Precisión | Velocidad |
|--------|--------|-----------|-----------|
| tiny | 39 MB | Baja | Muy rápida |
| base | 140 MB | Media | Rápida |
| small | 466 MB | Buena | Media |
| medium | 1.5 GB | Muy buena | Media |
| large | 2.9 GB | Excelente | Lenta |

**Nota**: El modelo se descarga automáticamente en `~/.cache/whisper/` la primera vez.

---

### 5. **batch_transcribe.py** (Transcripción por Lotes - Opcional)

**Rol**: Procesa múltiples archivos sin interfaz web

**Uso desde línea de comandos**:
```bash
python batch_transcribe.py <archivo.csv> [--model large]
```

**Parámetros**:
- Archivo con URLs
- `--model`: Tamaño de modelo Whisper (default: 'large')

---

### 6. **soundcloud_downloader.py** (Plugin SoundCloud)

**Rol**: Optimizador específico para SoundCloud

**Funciones principales**:
- Manejo especial de URLs de SoundCloud
- Fallback a yt-dlp si falla descarga directa

---

### 7. **archive_downloader.py** (Plugin Descarga de Archivos)

**Rol**: Descarga desde archivos ZIP/TAR

**Funciones principales**:
- Extrae y procesa audio de archivos comprimidos

---

## Archivos de Configuración

### requirements.txt

Dependencias principales:

```
Flask==3.1.2                    # Servidor web
openai-whisper==20250625        # Transcripción (OpenAI)
demucs==4.0.1                   # Separación de audio
yt-dlp==2026.2.4                # Descarga de videos
torch==2.1.0                    # Motor de deep learning (Whisper/Demucs)
torchaudio==2.1.0               # Procesamiento de audio para Torch
pandas==2.3.3                   # Lectura de CSV/Excel
librosa==0.10.0                 # Análisis de audio (opcional)
soundfile==0.12.1               # I/O de audio WAV/FLAC (opcional)
ffmpeg                          # Conversión de audio (binario, incluido en .exe)
```

### Estructura de Carpetas

```
Lyric-transcriptor/
├── app.py                      # Servidor Flask
├── downloader.py               # Descarga de audio
├── audio_separator.py          # Separación con Demucs
├── transcriber.py              # Transcripción con Whisper
├── batch_transcribe.py         # Procesamiento por lotes
├── soundcloud_downloader.py    # Plugin SoundCloud
├── archive_downloader.py       # Plugin descarga de archivos
├── requirements.txt            # Dependencias Python
├── build_exe.ps1               # Script para empaquetar .exe
├── README.md                   # Este archivo
├── README_BUILD.md             # Instrucciones de compilación
├── static/                     # Assets web (CSS, fondo, etc.)
│   └── style.css
├── templates/                  # Plantillas HTML
│   └── index.html
├── uploads/                    # Archivos subidos temporalmente
├── results/                    # Resultados procesados
├── ffmpeg/                     # Binarios ffmpeg incluidos en .exe
└── venv/                       # Entorno virtual Python
```

---

## Configuración Avanzada

### Variables de Entorno

```bash
# Tamaño de modelo Whisper (default: large)
set WHISPER_MODEL=medium

# Directorio de caché para Whisper
set XDG_CACHE_HOME=C:\custom\cache

# Directorio de caché para Demucs
set DEMUCS_ROOT=C:\custom\.demucs
```

### Cambiar Puerto

En `app.py`, línea final:
```python
app.run(host='0.0.0.0', port=8080, ...)  # Cambiar 5000 → 8080
```

### Modelo de Whisper Personalizado

En `app.py`, dentro de `process_file()`:
```python
transcript_text = transcribe_audio(transcription_source, model_size='medium')
```

---

## Troubleshooting

### Error: "mel_filters.npz not found"
**Solución**: Whisper assets no se empaquetaron correctamente. Reconstruye el .exe:
```bash
.\build_exe.ps1
```

### Error: "demucs command not found"
**Solución**: ffmpeg o demucs no están en PATH. En máquinas remotas:
1. Instala demucs: `pip install demucs`
2. Instala ffmpeg: Descárgalo desde https://ffmpeg.org

### La aplicación es lenta la primera vez
**Esperado**: Whisper descarga modelos (~2.9 GB para 'large') la primera ejecución. Subsecuentes son rápidas.

### Caracteres extraños en transcripciones
**Solución**: Asegúrate que el audio es MP3/WAV válido. Prueba con modelo 'medium' si 'large' falla.

---

## Rendimiento

| Tarea | Tiempo Aprox. | Requisitos |
|-------|---------------|-----------|
| Descarga (SoundCloud 3 min) | 30 segundos | Internet |
| Separación (3 minutos) | 20-40 segundos | GPU recomendada |
| Transcripción (modelo large) | 2-5 minutos | CPU/GPU |
| **Total por canción** | **3-7 minutos** | - |

**Nota**: Tiempos dependen de duración del audio y hardware.

---

## Compilación a .exe

Ver [README_BUILD.md](README_BUILD.md) para instrucciones detalladas.

**Resumen rápido**:
```bash
.\build_exe.ps1  # Descarga ffmpeg, assets de Whisper, y compila
```

Resultado: `dist\LyricTranscriptor.exe`

---

## Licencias

- **Whisper**: OpenAI (MIT License)
- **Demucs**: Facebook Research (CC0)
- **Flask**: BSD 3-Clause
- **yt-dlp**: Unlicense (público)

---

## Soporte y Problemas

1. Revisa `app.log` en la carpeta raíz para logs detallados
2. Ejecuta desde terminal para ver mensajes de error en tiempo real
3. Prueba con modelos más pequeños (medium/small) si hay problemas de memoria

---

## Cambios Recientes

### v1.0.0 (Actual)
- ✅ Separación de vocales con Demucs
- ✅ Transcripción con Whisper
- ✅ Interfaz web Flask
- ✅ Procesamiento en lote
- ✅ Empaquetado a .exe
- ✅ Logging detallado

---

**Última actualización**: Febrero 2026
