#!/usr/bin/env python3
"""
CMP - Cool Music Player
HTTP audio server with Range request support for streaming.
"""

import http.server
import socketserver
import threading
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
import mimetypes


class AudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with Range support for audio files."""
    
    def __init__(self, *args, library_manager=None, **kwargs):
        self.library_manager = library_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests with Range support."""
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        
        # Audio file serving endpoint
        if path.startswith('/audio/'):
            self.serve_audio(path[7:])  # Remove '/audio/' prefix
            return
        
        # Health check
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            return
        
        # Default 404
        self.send_error(404)
    
    def serve_audio(self, file_path: str):
        """Serve audio file with Range request support."""
        # Resolve the path
        try:
            # The file_path should be an absolute path or we look it up
            abs_path = Path(file_path).resolve()
            
            # Security: ensure file exists and is readable
            if not abs_path.exists() or not abs_path.is_file():
                self.send_error(404, "File not found")
                return
            
            # Check if it's in our library (optional security)
            # For now, allow any readable audio file
            
            file_size = abs_path.stat().st_size
            mime_type, _ = mimetypes.guess_type(str(abs_path))
            if not mime_type:
                mime_type = 'audio/mpeg'
            
            # Parse Range header
            range_header = self.headers.get('Range')
            
            if range_header:
                # Parse range: "bytes=start-end"
                try:
                    range_str = range_header.replace('bytes=', '')
                    start_str, end_str = range_str.split('-')
                    start = int(start_str) if start_str else 0
                    end = int(end_str) if end_str else file_size - 1
                    
                    # Clamp values
                    start = max(0, min(start, file_size - 1))
                    end = max(start, min(end, file_size - 1))
                    content_length = end - start + 1
                    
                    self.send_response(206)  # Partial Content
                    self.send_header('Content-Type', mime_type)
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Content-Length', str(content_length))
                    self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                    self.send_header('Cache-Control', 'public, max-age=3600')
                    self.end_headers()
                    
                    # Send file chunk
                    with open(abs_path, 'rb') as f:
                        f.seek(start)
                        remaining = content_length
                        chunk_size = 8192
                        while remaining > 0:
                            read_size = min(chunk_size, remaining)
                            data = f.read(read_size)
                            if not data:
                                break
                            self.wfile.write(data)
                            remaining -= len(data)
                    
                except (ValueError, IndexError):
                    # Invalid range, serve full file
                    self.serve_full_file(abs_path, file_size, mime_type)
            else:
                # No range header, serve full file
                self.serve_full_file(abs_path, file_size, mime_type)
                
        except Exception as e:
            print(f"Error serving audio: {e}")
            self.send_error(500, str(e))
    
    def serve_full_file(self, abs_path: Path, file_size: int, mime_type: str):
        """Serve the full audio file."""
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(file_size))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        
        with open(abs_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
    
    def log_message(self, format, *args):
        """Suppress default log messages."""
        pass


class AudioServer:
    """HTTP server for serving audio files with Range support."""
    
    def __init__(self, library_manager, port=0):
        self.library_manager = library_manager
        self.port = port
        self.server = None
        self.thread = None
        self._port = None
    
    def start(self):
        """Start the HTTP server in a background thread."""
        # Find an available port
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            self._port = s.getsockname()[1]
        
        handler = lambda *args, **kwargs: AudioRequestHandler(
            *args, library_manager=self.library_manager, **kwargs
        )
        
        self.server = socketserver.TCPServer(('', self._port), handler)
        self.server.allow_reuse_address = True
        
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        print(f"Audio server started on http://localhost:{self._port}")
    
    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
    
    def get_audio_url(self, file_path: str) -> str:
        """Get the HTTP URL for an audio file."""
        if self._port:
            # URL encode the path
            import urllib.parse
            encoded = urllib.parse.quote(file_path, safe='')
            return f'http://localhost:{self._port}/audio/{encoded}'
        return ''
    
    @property
    def base_url(self) -> str:
        """Get the base URL of the server."""
        if self._port:
            return f'http://localhost:{self._port}'
        return ''