#!/usr/bin/env python3
"""
CMP - Cool Music Player
API bridge between Python backend and JavaScript frontend.
"""

import json
import os
import threading
import traceback
import weakref
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import webview
from webview import FileDialog
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

# Diagnostic log file path (project root)
_IMPORT_LOG_PATH = Path(__file__).resolve().parents[1] / 'import_debug.log'
_IMPORT_LOG_LOCK = threading.Lock()


class CMPApi:
    """Python-JavaScript bridge API for pywebview."""
    __slots__ = ('_library', '_audio_server', '_window_ref', '_current_track_index', '_playback_state')
    
    def __init__(self, library_manager, audio_server):
        self._library = library_manager
        self._audio_server = audio_server
        self._window_ref = None
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

    # ----- diagnostic logging -----
    def _ilog(self, msg: str):
        """Print to console and append to import_debug.log with timestamp."""
        ts = datetime.datetime.now().isoformat(timespec='seconds')
        line = f"{ts} {msg}"
        print(line)
        try:
            with _IMPORT_LOG_LOCK:
                with open(_IMPORT_LOG_PATH, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
        except Exception:
            # never let logging break the app
            pass

    def log(self, message: str):
        """Bridge for JavaScript: write a line to import_debug.log."""
        ts = datetime.datetime.now().isoformat(timespec='seconds')
        line = f"{ts} {message}"
        try:
            with _IMPORT_LOG_LOCK:
                with open(_IMPORT_LOG_PATH, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
        except Exception:
            pass
    
    def set_window(self, window):
        """Set the webview window reference for window controls."""
        self._window_ref = weakref.ref(window)
    
    def _get_window(self):
        if self._window_ref:
            return self._window_ref()
        return None
    
    # Window controls
    def minimize_window(self):
        w = self._get_window()
        if w:
            w.minimize()
    
    def maximize_window(self):
        w = self._get_window()
        if w:
            if w.maximized:
                w.restore()
            else:
                w.maximize()
    
    def close_window(self):
        w = self._get_window()
        if w:
            w.destroy()
    
    # File/folder selection
    def select_files(self) -> dict:
        """Open file dialog to select audio files."""
        self._ilog("[IMPORT] select_files: opening file picker")
        w = self._get_window()
        if not w:
            self._ilog("[IMPORT] select_files: no window")
            return {'paths': []}
        
        file_types = (
            'Audio Files (*.flac;*.mp3;*.wav;*.ogg;*.opus;*.m4a;*.aac;*.dsf;*.dff)',
            'All Files (*.*)'
        )
        
        result = w.create_file_dialog(
            FileDialog.OPEN,
            allow_multiple=True,
            file_types=file_types
        )
        
        paths = list(result) if result else []
        self._ilog(f"[IMPORT] select_files: picker returned {len(paths)} paths")
        for p in paths:
            self._ilog(f"[IMPORT]   {p}")
        return {'paths': paths}
    
    def select_folder(self) -> dict:
        """Open folder dialog to select a directory."""
        self._ilog("[IMPORT] select_folder: opening folder picker")
        w = self._get_window()
        if not w:
            self._ilog("[IMPORT] select_folder: no window")
            return {'path': None}
        
        result = w.create_file_dialog(FileDialog.FOLDER)
        
        path = result[0] if result else None
        self._ilog(f"[IMPORT] select_folder: picker returned {path}")
        return {'path': path}
    
    # Library management
    def add_tracks(self, paths: List[str]) -> dict:
        """Add tracks to the library from file paths."""
        self._ilog(f"[IMPORT] add_tracks called with {len(paths)} paths")
        for p in paths:
            self._ilog(f"[IMPORT]   input path: {p}")
        try:
            tracks = []
            for path_str in paths:
                path = Path(path_str)
                if path.is_file():
                    self._ilog(f"[IMPORT]   scanning file: {path}")
                    track = self._extract_track_metadata(path)
                    if track:
                        tracks.append(track)
                        self._ilog(f"[IMPORT]     extracted: {track['title']} - {track['artist']}")
                    else:
                        self._ilog(f"[IMPORT]     extraction failed for {path}")
                elif path.is_dir():
                    self._ilog(f"[IMPORT]   scanning directory: {path}")
                    dir_tracks = self._scan_directory(path)
                    self._ilog(f"[IMPORT]     found {len(dir_tracks)} tracks in directory")
                    tracks.extend(dir_tracks)
            
            self._ilog(f"[IMPORT] total tracks extracted: {len(tracks)}")
            if tracks:
                added = self._library.add_tracks(tracks)
                self._ilog(f"[IMPORT] library.add_tracks returned {len(added)} added")
                return {'tracks': added}
            self._ilog("[IMPORT] no tracks to add")
            return {'tracks': []}
        except Exception as e:
            self._ilog(f"[IMPORT] Error in add_tracks: {e}")
            traceback.print_exc()
            return {'tracks': []}
    
    def add_folder(self, path: str) -> dict:
        """Add a folder to the library index."""
        self._ilog(f"[IMPORT] add_folder called with path: {path}")
        try:
            if not path:
                self._ilog("[IMPORT] add_folder: empty path")
                return {'tracks': []}
            path_obj = Path(path)
            if path_obj.is_dir():
                self._ilog(f"[IMPORT] add_folder: adding directory {path_obj}")
                self._library.add_directory(str(path_obj))
                tracks = self._scan_directory(path_obj)
                self._ilog(f"[IMPORT] add_folder: scanned directory, found {len(tracks)} tracks")
                if tracks:
                    added = self._library.add_tracks(tracks)
                    self._ilog(f"[IMPORT] add_folder: library.add_tracks returned {len(added)} added")
                    return {'tracks': added}
            else:
                self._ilog(f"[IMPORT] add_folder: not a directory: {path_obj}")
            return {'tracks': []}
        except Exception as e:
            self._ilog(f"[IMPORT] Error in add_folder: {e}")
            traceback.print_exc()
            return {'tracks': []}
    
    def _scan_directory(self, path: Path) -> List[dict]:
        """Scan a directory recursively for audio files."""
        self._ilog(f"[IMPORT] _scan_directory scanning {path}")
        audio_extensions = {'.flac', '.mp3', '.wav', '.ogg', '.opus', '.m4a', '.aac', '.dsf', '.dff'}
        tracks = []
        count = 0
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                count += 1
                track = self._extract_track_metadata(file_path)
                if track:
                    tracks.append(track)
        self._ilog(f"[IMPORT] _scan_directory found {count} audio files, extracted {len(tracks)} tracks")
        return tracks
    
    def _extract_track_metadata(self, path: Path) -> Optional[dict]:
        """Extract metadata from an audio file using mutagen."""
        self._ilog(f"[IMPORT] _extract_track_metadata for {path}")
        try:
            audio = MutagenFile(str(path))
            if audio is None:
                self._ilog(f"[IMPORT]   MutagenFile returned None")
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
            
            # Determine container type for tag handling
            container_type = None
            if isinstance(audio, FLAC):
                container_type = 'flac'
            elif isinstance(audio, MP3):
                container_type = 'mp3'
            elif isinstance(audio, OggVorbis):
                container_type = 'ogg'
            elif Opus and isinstance(audio, Opus):
                container_type = 'opus'
            elif isinstance(audio, MP4):
                container_type = 'mp4'
            elif isinstance(audio, WavPack):
                container_type = 'wavpack'
            elif ext in ('.wav',):
                container_type = 'wav'
            elif ext in ('.dsf', '.dff'):
                container_type = 'dsd'

            # Extract tags in a format‑aware way
            if audio.tags:
                tags = audio.tags

                def get_tag(tag_dict, keys):
                    for k in keys:
                        if k in tag_dict:
                            val = tag_dict[k]
                            if isinstance(val, (list, tuple)):
                                return str(val[0])
                            return str(val)
                    return None

                if container_type in ('flac', 'ogg', 'opus'):
                    # VorbisComment – keys are uppercase
                    track['title'] = get_tag(tags, ['TITLE']) or track['title']
                    track['artist'] = get_tag(tags, ['ARTIST']) or track['artist']
                    track['album'] = get_tag(tags, ['ALBUM']) or track['album']
                    year_val = get_tag(tags, ['DATE', 'YEAR'])
                    if year_val:
                        track['year'] = year_val[:4]
                elif container_type == 'mp3':
                    # ID3 frames
                    track['title'] = get_tag(tags, ['TIT2']) or track['title']
                    track['artist'] = get_tag(tags, ['TPE1']) or track['artist']
                    track['album'] = get_tag(tags, ['TALB']) or track['album']
                    year_val = get_tag(tags, ['TDRC', 'TYER'])
                    if year_val:
                        track['year'] = year_val[:4]
                elif container_type == 'mp4':
                    # MP4 atoms
                    track['title'] = get_tag(tags, ['\xa9nam']) or track['title']
                    track['artist'] = get_tag(tags, ['\xa9ART']) or track['artist']
                    track['album'] = get_tag(tags, ['\xa9alb']) or track['album']
                    year_val = get_tag(tags, ['\xa9day'])
                    if year_val:
                        track['year'] = year_val[:4]
                elif container_type == 'wavpack':
                    # APE tags – usually Title, Artist, Album, Year
                    track['title'] = get_tag(tags, ['Title']) or track['title']
                    track['artist'] = get_tag(tags, ['Artist']) or track['artist']
                    track['album'] = get_tag(tags, ['Album']) or track['album']
                    year_val = get_tag(tags, ['Year'])
                    if year_val:
                        track['year'] = year_val[:4]
                # wav and dsd usually have no tags; keep defaults

                # Cover art (unchanged)
                cover_data = self._extract_cover(audio, tags)
                if cover_data:
                    track['cover'] = cover_data
            
            self._ilog(f"[IMPORT]   extracted metadata: {track['title']} - {track['artist']} ({track['duration']})")
            return track
            
        except Exception as e:
            self._ilog(f"[IMPORT] Error extracting metadata from {path}: {e}")
            traceback.print_exc()
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
        return self._audio_server.get_audio_url(path)
    
    def get_library(self) -> dict:
        """Get the full library data."""
        return {
            'tracks': self._library.get_all_tracks(),
            'directories': self._library.get_directories(),
            'playlists': self._library.get_playlists(),
            'favourites': self._library.get_favourites()
        }
    
    def get_directories(self) -> dict:
        """Get indexed directories."""
        return {'directories': self._library.get_directories()}
    
    def remove_directory(self, path: str) -> dict:
        """Remove a directory from the index."""
        self._library.remove_directory(path)
        return {'success': True}
    
    def get_library_stats(self) -> dict:
        """Get library statistics."""
        return {
            'trackCount': self._library.get_track_count(),
            'playlistCount': len(self._library.get_playlists()),
            'favouriteCount': len(self._library.get_favourites())
        }
    
    def create_playlist(self, name: str) -> dict:
        """Create a new playlist."""
        playlist = self._library.create_playlist(name)
        return {'playlist': playlist}
    
    def delete_playlist(self, playlist_id: str) -> dict:
        """Delete a playlist."""
        self._library.delete_playlist(playlist_id)
        return {'success': True}
    
    def add_to_playlist(self, playlist_id: str, track_paths: List[str]) -> dict:
        """Add tracks to a playlist."""
        self._library.add_to_playlist(playlist_id, track_paths)
        return {'success': True}
    
    def remove_from_playlist(self, playlist_id: str, track_path: str) -> dict:
        """Remove a track from a playlist."""
        self._library.remove_from_playlist(playlist_id, track_path)
        return {'success': True}
    
    def toggle_favourite(self, track_path: str) -> dict:
        """Toggle favourite status for a track."""
        is_fav = self._library.toggle_favourite(track_path)
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
        self._library.save_playback_state(self._playback_state)
        return {'success': True}
    
    def load_playback_state(self) -> dict:
        """Load playback state from persistence."""
        state = self._library.load_playback_state()
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