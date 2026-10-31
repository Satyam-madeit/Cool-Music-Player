#!/usr/bin/env python3
"""
CMP - Cool Music Player
PyInstaller build script.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    project_root = Path(__file__).parent
    frontend_dir = project_root / 'frontend'
    backend_dir = project_root / 'backend'
    assets_dir = project_root / 'assets'
    
    # Clean previous builds
    for dir_name in ['build', 'dist']:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    # PyInstaller arguments
    args = [
        'pyinstaller',
        '--name=CMP',
        '--onefile',
        '--windowed',  # No console window
        '--icon=assets/app-icon.ico',
        f'--add-data={frontend_dir}{os.pathsep}frontend',
        f'--add-data={backend_dir}{os.pathsep}backend',
        f'--add-data={assets_dir}{os.pathsep}assets',
        '--hidden-import=mutagen',
        '--hidden-import=mutagen.flac',
        '--hidden-import=mutagen.mp3',
        '--hidden-import=mutagen.wavpack',
        '--hidden-import=mutagen.oggvorbis',
        '--hidden-import=mutagen.opus',
        '--hidden-import=mutagen.mp4',
        '--hidden-import=mutagen.id3',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=webview',
        '--hidden-import=webview.platforms.edgechromium',
        '--collect-all=webview',
        '--collect-all=mutagen',
        '--collect-all=PIL',
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        'main.py'
    ]
    
    print("Building CMP with PyInstaller...")
    print(f"Command: {' '.join(args)}")
    
    result = subprocess.run(args, cwd=project_root)
    
    if result.returncode == 0:
        print("\nBuild successful!")
        print(f"Executable: {project_root / 'dist' / 'CMP.exe'}")
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()