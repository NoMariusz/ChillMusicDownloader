# -*- mode: python ; coding: utf-8 -*-

from kivy_deps import sdl2, glew
import pathlib, os

actual_path = os.path.join(pathlib.Path().resolve(), "..")

block_cipher = None


a = Analysis([os.path.join(actual_path, 'app\\chill_music_downloader.py')],
             pathex=[os.path.join(actual_path, 'dev')],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Chill Music Downloader',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True , icon=os.path.join(actual_path, 'data\\graphics\\CMDownloader_logo.ico'))
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Chill Music Downloader')
