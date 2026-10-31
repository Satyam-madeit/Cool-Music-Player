#!/usr/bin/env python3
"""
CMP - Cool Music Player
Main entry point for the application.
"""

import sys
import os
import json
import threading
import webview
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.api import CMPApi
from backend.library import LibraryManager
from backend.audio_server import AudioServer


def get_app_data_dir():
    """Get the application data directory for persistence."""
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    else:
        base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    return Path(base) / 'CMP'


def _rotate_import_log():
    """Clear import_debug.log at start of a new session."""
    log_path = Path(__file__).resolve().parent / 'import_debug.log'
    try:
        log_path.write_text('', encoding='utf-8')
    except Exception:
        pass


def main():
    # Rotate diagnostic log for this session
    _rotate_import_log()
    
    # Setup app data directory
    app_data_dir = get_app_data_dir()
    app_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize library manager
    library_manager = LibraryManager(app_data_dir)
    library_manager.load()
    
    # Start audio HTTP server in background
    audio_server = AudioServer(library_manager)
    audio_server.start()
    
    # Write the audio server port to a file for diagnostic scripts
    try:
        port_file = Path(__file__).resolve().parent / 'audio_port.txt'
        port_file.write_text(str(audio_server._port))
    except Exception:
        pass
    
    # Create API bridge
    api = CMPApi(library_manager, audio_server)
    
    # Get frontend directory
    frontend_dir = Path(__file__).parent / 'frontend'
    index_html = frontend_dir / 'index.html'
    
    # Create webview window
    window = webview.create_window(
        'CMP - Cool Music Player',
        str(index_html),
        width=1280,
        height=800,
        min_size=(900, 600),
        frameless=False,
        easy_drag=False,
        js_api=api,
        text_select=False
    )
    
    # Set window reference in API for window controls
    api.set_window(window)
    
    # Start the application
    webview.start(debug=False, http_server=True)
    
    # Cleanup
    audio_server.stop()
    library_manager.save()


if __name__ == '__main__':
    main()