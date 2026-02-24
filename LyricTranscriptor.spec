# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[('C:\\Users\\AlumnoB2\\Documents\\Becario\\Scripts\\Lyric transcriptor\\Lyric-transcriptor\\ffmpeg\\bin\\ffmpeg.exe', 'ffmpeg\\\\bin'), ('C:\\Users\\AlumnoB2\\Documents\\Becario\\Scripts\\Lyric transcriptor\\Lyric-transcriptor\\ffmpeg\\bin\\ffprobe.exe', 'ffmpeg\\\\bin')],
    datas=[('templates', 'templates'), ('static', 'static'), ('uploads', 'uploads'), ('results', 'results'), ('ffmpeg', 'ffmpeg'), ('whisper_assets', 'whisper/assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LyricTranscriptor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
