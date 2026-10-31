#!/usr/bin/env python3
"""
CMP - Cool Music Player
API bridge between Python backend and JavaScript frontend.
"""

import json
import os
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
import webview
from mutagen import File as MutagenFile
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wavpack import WavPack
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, APIC

# Optional imports
try:
    from mutagen.opus import Opus
except ImportError:
    Opus = None
from PIL import Image
import io
import base64


class CMPApi:
    """Python-JavaScript bridge API for pywebview."""
    
    def __init__(self, library_manager, audio_server):
        self.library = library_manager
        self.audio_server = audio_server
        self.window = None
        self._current_track_index = -1
        self._playback_state = {
            'playing': False,
            'position': 0,
            'duration': 0,
            'volume': 0.7,
            'speed': 1.0,
            'shuffle': False,
            'repeat': 0
        }
    
    def set_window(self, window):
        """Set the webview window reference for window controls."""
        self.window = window
    
    # Window controls
    def minimize_window(self):
        if self.window:
            self.window.minimize()
    
    def maximize_window(self):
        if self.window:
            if self.window.maximized:
                self.window.restore()
            else:
                self.window.maximize()
    
    def close_window(self):
        if self.window:
            self.window.destroy()
    
    # File/folder selection
    def select_files(self) -> dict:
        """Open file dialog to select audio files."""
        if not self.window:
            return {'paths': []}
        
        file_types = (
            'Audio Files (*.flac;*.mp3;*.wav;*.ogg;*.opus;*.m4a;*.aac;*.dsf;*.dff)',
            'All Files (*.*)'
        )
        
        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types
        )
        
        if result:
            return {'paths': list(result)}
        return {'paths': []}
    
    def select_folder(self) -> dict:
        """Open folder dialog to select a directory."""
        if not self.window:
            return {'path': None}
        
        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        
        if result:
            return {'path': result[0]}
        return {'path': None}
    
    # Library management
    def add_tracks(self, paths: List[str]) -> dict:
        """Add tracks to the library from file paths."""
        tracks = []
        for path_str in paths:
            path = Path(path_str)
            if path.is_file():
                track = self._extract_track_metadata(path)
                if track:
                    tracks.append(track)
            elif path.is_dir():
                # Recursively add all audio files in directory
                dir_tracks = self._scan_directory(path)
                tracks.extend(dir_tracks)
        
        if tracks:
            added = self.library.add_tracks(tracks)
            return {'tracks': added}
        return {'tracks': [] }
    
    def add_folder(self, path: str) -> dict:
        """Add a folder to the library index."""
        path_obj = Path(path)
        if path_obj.is_dir():
            self.library.add_directory(path_str)
            tracks = self._scan_directory(path_obj)
            if tracks:
                added = self.library.add_tracks(tracks)
                return {'tracks': added}
        return {'tracks': []}
    
    def _scan_directory(self, path: Path) -> List[dict]:
        """Scan a directory recursively for audio files."""
        audio_extensions = {'.flac', '.mp3', '.wav', '.ogg', '.opus', '.m4a', '.aac', '.dsf', '.dff'}
        tracks = []
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                track = self._extract_track_metadata(file_path)
                if track:
                    tracks.append(track)
        
        return tracks
    
    def _extract_track_metadata(self, path: Path) -> Optional[dict]:
        """Extract metadata from an audio file using mutagen."""
        try:
            audio = MutagenFile(str(path))
            if audio is None:
                return None
            
            # Basic info
            track = {
                'path': str(path),
                'title': 'Unknown Title',
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
                'year': '—',
                'duration': '00:00',
                'durationSec': 0,
                'formatTag': 'Unknown',
                'formatBadge': 'UNKNOWN',
                'bitrate': '—',
                'tier': '—',
                'sourceTag': 'LOCAL FILE',
                'cover': 'assets/placeholder-album.svg',
                'accentColor': '#a855f7',
                'accentSecondary': '#ec4899',
                'badgeColor': 'bg-purple-900/60 text-purple-200 border-purple-700/60',
                'ambientGradient': 'radial-gradient(circle at 65% 20%, rgba(139, 92, 246, 0.22) 0%, rgba(236, 72, 153, 0.10) 40%, rgba(19, 19, 22, 0) 70%)'
            }
            
            # Duration
            if hasattr(audio.info, 'length'):
                duration_sec = int(audio.info.length)
                track['durationSec'] = duration_sec
                track['duration'] = f"{duration_sec // 60:02d}:{duration_sec % 60:02d}"
            
            # Bitrate
            if hasattr(audio.info, 'bitrate'):
                bitrate = audio.info.bitrate
                if bitrate >= 1000:
                    track['bitrate'] = f"{bitrate // 1000} kbps"
                else:
                    track['bitrate'] = f"{bitrate} bps"
            
            # Format detection
            ext = path.suffix.lower()
            if isinstance(audio, FLAC):
                track['formatTag'] = f"FLAC {audio.info.bits_per_sample}-BIT / {audio.info.sample_rate // 1000}kHz"
                track['formatBadge'] = f"FLAC {audio.info.bits_per_sample}-BIT"
                track['tier'] = 'LOSSLESS STUDIO MASTER' if audio.info.bits_per_sample > 16 else 'CD QUALITY LOSSLESS'
                track['sourceTag'] = 'OFFLINE MASTER' if audio.info.bits_per_sample > 16 else 'RED BOOK CD'
                track['accentColor'] = '#8b5cf6'
                track['accentSecondary'] = '#3b82f6'
                track['badgeColor'] = 'bg-indigo-900/60 text-indigo-200 border-indigo-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(139, 92, 246, 0.24) 0%, rgba(59, 130, 246, 0.12) 40%, rgba(19, 19, 22, 0) 70%)'
            elif isinstance(audio, MP3):
                track['formatTag'] = f"MP3 {audio.info.bitrate // 1000} kbps / {audio.info.sample_rate // 1000}kHz"
                track['formatBadge'] = f"MP3 {audio.info.bitrate // 1000}K"
                track['tier'] = 'CBR LOSSY ARCHIVE' if audio.info.bitrate_mode == 0 else 'VBR LOSSY ARCHIVE'
                track['sourceTag'] = 'MPEG LAYER-3'
                track['accentColor'] = '#f59e0b'
                track['accentSecondary'] = '#ef4444'
                track['badgeColor'] = 'bg-amber-900/60 text-amber-200 border-amber-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(245, 158, 11, 0.18) 0%, rgba(239, 68, 68, 0.08) 40%, rgba(19, 19, 22, 0) 70%)'
            elif isinstance(audio, OggVorbis):
                track['formatTag'] = f"OGG Vorbis / {audio.info.sample_rate // 1000}kHz"
                track['formatBadge'] = 'OGG VORBIS'
                track['tier'] = 'LOSSY COMPRESSED'
                track['sourceTag'] = 'XIPH.ORG'
                track['accentColor'] = '#f97316'
                track['accentSecondary'] = '#fb923c'
                track['badgeColor'] = 'bg-orange-900/60 text-orange-200 border-orange-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(249, 115, 22, 0.18) 0%, rgba(251, 146, 60, 0.08) 40%, rgba(19, 19, 22, 0) 70%)'
            elif Opus and isinstance(audio, Opus):
                track['formatTag'] = f"Opus / {audio.info.sample_rate // 1000}kHz"
                track['formatBadge'] = 'OPUS'
                track['tier'] = 'LOSSY COMPRESSED'
                track['sourceTag'] = 'IETF RFC 6716'
                track['accentColor'] = '#eab308'
                track['accentSecondary'] = '#facc15'
                track['badgeColor'] = 'bg-yellow-900/60 text-yellow-200 border-yellow-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(234, 179, 8, 0.18) 0%, rgba(250, 204, 21, 0.08) 40%, rgba(19, 19, 22, 0) 70%)'
            elif isinstance(audio, MP4):
                track['formatTag'] = f"AAC / {audio.info.sample_rate // 1000}kHz"
                track['formatBadge'] = 'M4A/AAC'
                track['tier'] = 'LOSSY COMPRESSED'
                track['sourceTag'] = 'MPEG-4'
                track['accentColor'] = '#06b6d4'
                track['accentSecondary'] = '#0891b2'
                track['badgeColor'] = 'bg-cyan-900/60 text-cyan-200 border-cyan-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(6, 182, 212, 0.18) 0%, rgba(8, 145, 178, 0.08) 40%, rgba(19, 19, 22, 0) 70%)'
            elif isinstance(audio, WavPack):
                track['formatTag'] = f"WavPack {audio.info.bits_per_sample}-BIT / {audio.info.sample_rate // 1000}kHz"
                track['formatBadge'] = 'WAV PACK'
                track['tier'] = 'LOSSLESS COMPRESSED'
                track['sourceTag'] = 'WAVPACK'
                track['accentColor'] = '#a855f7'
                track['accentSecondary'] = '#ec4899'
                track['badgeColor'] = 'bg-purple-900/60 text-purple-200 border-purple-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(139, 92, 246, 0.22) 0%, rgba(236, 72, 153, 0.10) 40%, rgba(19, 19, 22, 0) 70%)'
            elif ext in ('.wav',):
                track['formatTag'] = f"WAV {audio.info.bits_per_sample}-BIT / {audio.info.sample_rate // 1000}kHz"
                track['formatBadge'] = 'WAV'
                track['tier'] = 'UNCOMPRESSED PCM'
                track['sourceTag'] = 'MICROSOFT/IBM'
                track['accentColor'] = '#ec4899'
                track['accentSecondary'] = '#f43f5e'
                track['badgeColor'] = 'bg-pink-900/60 text-pink-200 border-pink-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(236, 72, 153, 0.22) 0%, rgba(244, 63, 94, 0.10) 40%, rgba(19, 19, 22, 0) 70%)'
            elif ext in ('.dsf', '.dff'):
                track['formatTag'] = 'DSD 5.6MHz / 1-BIT'
                track['formatBadge'] = 'DSD 128'
                track['tier'] = 'DIRECT STREAM DIGITAL'
                track['sourceTag'] = 'DSD MASTER'
                track['accentColor'] = '#10b981'
                track['accentSecondary'] = '#06b6d4'
                track['badgeColor'] = 'bg-emerald-900/60 text-emerald-200 border-emerald-700/60'
                track['ambientGradient'] = 'radial-gradient(circle at 65% 20%, rgba(16, 185, 129, 0.20) 0%, rgba(6, 182, 212, 0.10) 40%, rgba(19, 19, 22, 0) 70%)'
            
            # Extract tags
            if audio.tags:
                tags = audio.tags
                
                # Title
                if 'TIT2' in tags:
                    track['title'] = str(tags['TIT2'])
                elif '\xa9nam' in tags:
                    track['title'] = str(tags['\xa9nam'][0])
                elif 'title' in tags:
                    track['title'] = str(tags['title'][0])
                
                # Artist
                if 'TPE1' in tags:
                    track['artist'] = str(tags['TPE1'])
                elif '\xa9ART' in tags:
                    track['artist'] = str(tags['\xa9ART'][0])
                elif 'artist' in tags:
                    track['artist'] = str(tags['artist'][0])
                
                # Album
                if 'TALB' in tags:
                    track['album'] = str(tags['TALB'])
                elif '\xa9alb' in tags:
                    track['album'] = str(tags['\xa9alb'][0])
                elif 'album' in tags:
                    track['album'] = str(tags['album'][0])
                
                # Year
                if 'TDRC' in tags:
                    track['year'] = str(tags['TDRC'])[:4]
                elif '\xa9day' in tags:
                    track['year'] = str(tags['\xa9day'][0])[:4]
                elif 'date' in tags:
                    track['year'] = str(tags['date'][0])[:4]
                
                # Cover art
                cover_data = self._extract_cover(audio, tags)
                if cover_data:
                    track['cover'] = cover_data
            
            return track
            
        except Exception as e:
            print(f"Error extracting metadata from {path}: {e}")
            return None
    
    def _extract_cover(self, audio, tags) -> Optional[str]:
        """Extract embedded cover art and return as base64 data URL."""
        try:
            cover_data = None
            
            if isinstance(audio, FLAC):
                for pic in audio.pictures:
                    if pic.type == 3:  # Front cover
                        cover_data = pic.data
                        break
                if not cover_data and audio.pictures:
                    cover_data = audio.pictures[0].data
                    
            elif isinstance(audio, MP3):
                if 'APIC:' in tags:
                    cover_data = tags['APIC:'].data
                else:
                    for key in tags.keys():
                        if key.startswith('APIC'):
                            cover_data = tags[key].data
                            break
                            
            elif isinstance(audio, MP4):
                if 'covr' in tags:
                    cover_data = tags['covr'][0]
                    
            elif isinstance(audio, OggVorbis) or (Opus and isinstance(audio, Opus)):
                if 'metadata_block_picture' in tags:
                    import base64
                    pic_data = base64.b64decode(tags['metadata_block_picture'][0])
                    # Parse FLAC picture block
                    # Simplified - just use first image
                    cover_data = pic_data
            
            if cover_data:
                # Convert to base64 data URL
                mime_type = 'image/jpeg'
                if cover_data.startswith(b'\x89PNG'):
                    mime_type = 'image/png'
                elif cover_data.startswith(b'GIF'):
                    mime_type = 'image/gif'
                elif cover_data.startswith(b'\xff\xd8'):
                    mime_type = 'image/jpeg'
                
                b64 = base64.b64encode(cover_data).decode('ascii')
                return f'data:{mime_type};base64,{b64}'
                
        except Exception as e:
            print(f"Error extracting cover: {e}")
        
        return None
    
    def get_audio_url(self, path: str) -> str:
        """Get the HTTP URL for streaming an audio file."""
        return self.audio_server.get_audio_url(path)
    
    def get_library(self) -> dict:
        """Get the full library data."""
        return {
            'tracks': self.library.get_all_tracks(),
            'directories': self.library.get_directories(),
            'playlists': self.library.get_playlists(),
            'favourites': self.library.get_favourites()
        }
    
    def get_directories(self) -> dict:
        """Get indexed directories."""
        return {'directories': self.library.get_directories()}
    
    def remove_directory(self, path: str) -> dict:
        """Remove a directory from the index."""
        self.library.remove_directory(path)
        return {'success': True}
    
    def get_library_stats(self) -> dict:
        """Get library statistics."""
        return {
            'trackCount': self.library.get_track_count(),
            'playlistCount': len(self.library.get_playlists()),
            'favouriteCount': len(self.library.get_favourites())
        }
    
    def create_playlist(self, name: str) -> dict:
        """Create a new playlist."""
        playlist = self.library.create_playlist(name)
        return {'playlist': playlist}
    
    def delete_playlist(self, playlist_id: str) -> dict:
        """Delete a playlist."""
        self.library.delete_playlist(playlist_id)
        return {'success': True}
    
    def add_to_playlist(self, playlist_id: str, track_paths: List[str]) -> dict:
        """Add tracks to a playlist."""
        self.library.add_to_playlist(playlist_id, track_paths)
        return {'success': True}
    
    def remove_from_playlist(self, playlist_id: str, track_path: str) -> dict:
        """Remove a track from a playlist."""
        self.library.remove_from_playlist(playlist_id, track_path)
        return {'success': True}
    
    def toggle_favourite(self, track_path: str) -> dict:
        """Toggle favourite status for a track."""
        is_fav = self.library.toggle_favourite(track_path)
        return {'isFavourite': is_fav}
    
    def get_playback_state(self) -> dict:
        """Get current playback state."""
        return self._playback_state
    
    def set_playback_state(self, state: dict) -> dict:
        """Update playback state from frontend."""
        self._playback_state.update(state)
        return {'success': True}
    
    def save_playback_state(self) -> dict:
        """Save playback state to persistence."""
        self.library.save_playback_state(self._playback_state)
        return {'success': True}
    
    def load_playback_state(self) -> dict:
        """Load playback state from persistence."""
        state = self.library.load_playback_state()
        self._playback_state.update(state)
        return state
    
    # Called from JS when track changes
    def on_track_change(self, index: int, track: dict) -> dict:
        """Notify backend of track change."""
        self._current_track_index = index
        self._playback_state['currentTrack'] = track
        return {'success': True}
    
    def on_playback_update(self, state: dict) -> dict:
        """Update playback state from frontend."""
        self._playback_state.update(state)
        return {'success': True}