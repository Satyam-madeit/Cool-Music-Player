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

# Ensure correct MIME types for audio extensions
mimetypes.add_type('audio/flac', '.flac')
mimetypes.add_type('audio/ogg', '.ogg')
mimetypes.add_type('audio/opus', '.opus')
mimetypes.add_type('audio/x-wav', '.wav')
mimetypes.add_type('audio/mp4', '.m4a')
mimetypes.add_type('audio/aac', '.aac')
mimetypes.add_type('audio/x-wavpack', '.wv')
mimetypes.add_type('audio/dsf', '.dsf')
mimetypes.add_type('audio/dff', '.dff')


class AudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with Range support for audio files."""
    
    def __init__(self, *args, library_manager=None, **kwargs):
        self.library_manager = library_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests with Range support."""
        parsed = urlparse(self.path)
        raw_path = self.path
        path = unquote(parsed.path)
        print(f"[AUDIO] HTTP GET raw_path={raw_path} decoded_path={path}")
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
        print(f"[AUDIO] serve_audio request for: {file_path}")
        print(f"[AUDIO] HTTP method={self.command} raw_path={self.path}")
        # Resolve the path
        try:
            # The file_path should be an absolute path or we look it up
            abs_path = Path(file_path).resolve()
            print(f"[AUDIO] resolved absolute path: {abs_path}")
            
            # Security: ensure file exists and is readable
            if not abs_path.exists() or not abs_path.is_file():
                print(f"[AUDIO] file not found: {abs_path}")
                self._safe_send_error(404, "File not found")
                return
            
            # Check if it's in our library (optional security)
            # For now, allow any readable audio file
            
            file_size = abs_path.stat().st_size
            mime_type, _ = mimetypes.guess_type(str(abs_path))
            if not mime_type:
                mime_type = 'audio/mpeg'
            print(f"[AUDIO] file size: {file_size}, mime: {mime_type}")
            
            # Parse Range header
            range_header = self.headers.get('Range')
            print(f"[AUDIO] Range header: {range_header}")
            
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
                    print(f"[AUDIO] serving range {start}-{end}/{file_size} ({content_length} bytes)")
                    
                    self.send_response(206)  # Partial Content
                    self.send_header('Content-Type', mime_type)
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Content-Length', str(content_length))
                    self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                    self.send_header('Cache-Control', 'public, max-age=3600')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    print(f"[AUDIO] Response headers sent: 206 Partial Content, Content-Type={mime_type}, Content-Length={content_length}, Content-Range=bytes {start}-{end}/{file_size}, Access-Control-Allow-Origin=*")
                    
                    # Send file chunk
                    sent = 0
                    with open(abs_path, 'rb') as f:
                        f.seek(start)
                        remaining = content_length
                        chunk_size = 8192
                        while remaining > 0:
                            read_size = min(chunk_size, remaining)
                            data = f.read(read_size)
                            if not data:
                                break
                            try:
                                self.wfile.write(data)
                            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                                # Client disconnected; stop sending
                                print("[AUDIO] client disconnected during streaming")
                                return
                            sent += len(data)
                            remaining -= len(data)
                    print(f"[AUDIO] range stream finished, bytes sent={sent}")
                    
                except (ValueError, IndexError):
                    # Invalid range, serve full file
                    print("[AUDIO] invalid range, serving full file")
                    self.serve_full_file(abs_path, file_size, mime_type)
            else:
                # No range header, serve full file
                print("[AUDIO] no range header, serving full file")
                self.serve_full_file(abs_path, file_size, mime_type)
                
        except Exception as e:
            print(f"[AUDIO] Error serving audio: {e}")
            self._safe_send_error(500, str(e))

    def _safe_send_error(self, code, message=None):
        """Send an error response, ignoring client disconnects."""
        try:
            self.send_error(code, message)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Client already gone; nothing to do
            pass
    
    def serve_full_file(self, abs_path: Path, file_size: int, mime_type: str):
        """Serve the full audio file."""
        print(f"[AUDIO] serve_full_file called for {abs_path} size={file_size}")
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(file_size))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        print(f"[AUDIO] Response headers sent: 200 OK, Content-Type={mime_type}, Content-Length={file_size}, Accept-Ranges=bytes, Access-Control-Allow-Origin=*")
        
        sent = 0
        with open(abs_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    # Client disconnected; stop sending
                    print("[AUDIO] client disconnected during streaming")
                    return
                sent += len(chunk)
        print(f"[AUDIO] full stream finished, bytes sent={sent}")
    
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