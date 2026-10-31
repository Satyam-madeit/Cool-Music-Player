#!/usr/bin/env python3
"""
CMP - Cool Music Player
Library management with JSON persistence.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading


class LibraryManager:
    """Manages the music library with JSON persistence."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.library_file = data_dir / 'library.json'
        self.playlists_file = data_dir / 'playlists.json'
        self.settings_file = data_dir / 'settings.json'
        self.playback_file = data_dir / 'playback.json'
        
        self._lock = threading.RLock()
        
        # In-memory data
        self._tracks: List[Dict] = []
        self._directories: List[str] = []
        self._playlists: Dict[str, Dict] = {}
        self._favourites: set = set()
        self._settings: Dict = {}
        self._playback_state: Dict = {}
        
        # Track ID counter
        self._next_track_id = 1
    
    def load(self):
        """Load all data from JSON files."""
        with self._lock:
            self._load_tracks()
            self._load_directories()
            self._load_playlists()
            self._load_settings()
            self._load_playback_state()
    
    def save(self):
        """Save all data to JSON files."""
        with self._lock:
            self._save_tracks()
            self._save_directories()
            self._save_playlists()
            self._save_settings()
            self._save_playback_state()
    
    # Track management
    def _load_tracks(self):
        try:
            if self.library_file.exists():
                with open(self.library_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._tracks = data.get('tracks', [])
                    self._next_track_id = data.get('next_id', 1)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading library: {e}")
            self._tracks = []
            self._next_track_id = 1
    
    def _save_tracks(self):
        try:
            data = {
                'tracks': self._tracks,
                'next_id': self._next_track_id
            }
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving library: {e}")
    
    def add_tracks(self, tracks: List[Dict]) -> List[Dict]:
        """Add tracks to library, avoiding duplicates by path.
        Returns a list of track dicts for each input track (newly added or existing)."""
        with self._lock:
            result = []
            existing_by_path = {t['path']: t for t in self._tracks}
            any_new = False
            # Debug
            print(f"[LIB] add_tracks start: existing count={len(existing_by_path)} incoming={len(tracks)}")
            for track in tracks:
                path = track.get('path')
                print(f"[LIB] processing track path={path}")
                if path not in existing_by_path:
                    # New track
                    new_track = dict(track)  # copy to avoid mutating input
                    new_track['id'] = self._next_track_id
                    self._next_track_id += 1
                    self._tracks.append(new_track)
                    existing_by_path[path] = new_track
                    result.append(new_track)
                    any_new = True
                else:
                    # Existing track: return the stored track (with its ID)
                    result.append(existing_by_path[path])
            print(f"[LIB] add_tracks result count={len(result)} any_new={any_new}")
            if any_new:
                self._save_tracks()
            return result
    
    def get_all_tracks(self) -> List[Dict]:
        """Get all tracks in the library."""
        with self._lock:
            return [dict(t) for t in self._tracks]
    
    def get_track(self, path: str) -> Optional[Dict]:
        """Get a track by path."""
        with self._lock:
            for t in self._tracks:
                if t['path'] == path:
                    return dict(t)
        return None
    
    def get_track_by_id(self, track_id: int) -> Optional[Dict]:
        """Get a track by ID."""
        with self._lock:
            for t in self._tracks:
                if t['id'] == track_id:
                    return dict(t)
        return None
    
    def remove_track(self, path: str) -> bool:
        """Remove a track from the library."""
        with self._lock:
            for i, t in enumerate(self._tracks):
                if t['path'] == path:
                    self._tracks.pop(i)
                    self._favourites.discard(path)
                    # Remove from playlists
                    for pl in self._playlists.values():
                        if path in pl.get('tracks', []):
                            pl['tracks'].remove(path)
                    self._save_tracks()
                    self._save_playlists()
                    return True
        return False
    
    def get_track_count(self) -> int:
        """Get total track count."""
        with self._lock:
            return len(self._tracks)
    
    # Directory management
    def _load_directories(self):
        try:
            if self.library_file.exists():
                with open(self.library_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._directories = data.get('directories', [])
        except (json.JSONDecodeError, IOError):
            self._directories = []
    
    def _save_directories(self):
        # Directories are saved with tracks
        pass
    
    def add_directory(self, path: str):
        """Add a directory to the index."""
        with self._lock:
            normalized = str(Path(path).resolve())
            if normalized not in self._directories:
                self._directories.append(normalized)
                # Update library file with directories
                self._save_library_with_dirs()
    
    def remove_directory(self, path: str):
        """Remove a directory from the index."""
        with self._lock:
            normalized = str(Path(path).resolve())
            if normalized in self._directories:
                self._directories.remove(normalized)
                # Remove tracks from this directory
                self._tracks = [t for t in self._tracks if not t['path'].startswith(normalized)]
                self._favourites = {p for p in self._favourites if not p.startswith(normalized)}
                for pl in self._playlists.values():
                    pl['tracks'] = [p for p in pl.get('tracks', []) if not p.startswith(normalized)]
                self._save_tracks()
                self._save_playlists()
                self._save_library_with_dirs()
    
    def _save_library_with_dirs(self):
        """Save tracks and directories together."""
        try:
            data = {
                'tracks': self._tracks,
                'directories': self._directories,
                'next_id': self._next_track_id
            }
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving library: {e}")
    
    def get_directories(self) -> List[Dict]:
        """Get indexed directories with track counts."""
        with self._lock:
            result = []
            for d in self._directories:
                count = sum(1 for t in self._tracks if t['path'].startswith(d))
                result.append({
                    'path': d,
                    'name': Path(d).name,
                    'trackCount': count
                })
            return result
    
    # Playlist management
    def _load_playlists(self):
        try:
            if self.playlists_file.exists():
                with open(self.playlists_file, 'r', encoding='utf-8') as f:
                    self._playlists = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._playlists = {}
    
    def _save_playlists(self):
        try:
            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump(self._playlists, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving playlists: {e}")
    
    def create_playlist(self, name: str) -> Dict:
        """Create a new playlist."""
        with self._lock:
            playlist_id = f"pl_{len(self._playlists) + 1}_{int(__import__('time').time())}"
            playlist = {
                'id': playlist_id,
                'name': name,
                'tracks': [],
                'created': __import__('datetime').datetime.now().isoformat()
            }
            self._playlists[playlist_id] = playlist
            self._save_playlists()
            return playlist
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist."""
        with self._lock:
            if playlist_id in self._playlists:
                del self._playlists[playlist_id]
                self._save_playlists()
                return True
        return False
    
    def get_playlists(self) -> List[Dict]:
        """Get all playlists."""
        with self._lock:
            return [dict(p) for p in self._playlists.values()]
    
    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """Get a playlist by ID."""
        with self._lock:
            pl = self._playlists.get(playlist_id)
            return dict(pl) if pl else None
    
    def add_to_playlist(self, playlist_id: str, track_paths: List[str]):
        """Add tracks to a playlist."""
        with self._lock:
            if playlist_id in self._playlists:
                pl = self._playlists[playlist_id]
                existing = set(pl.get('tracks', []))
                for path in track_paths:
                    if path not in existing:
                        pl['tracks'].append(path)
                self._save_playlists()
    
    def remove_from_playlist(self, playlist_id: str, track_path: str):
        """Remove a track from a playlist."""
        with self._lock:
            if playlist_id in self._playlists:
                pl = self._playlists[playlist_id]
                if track_path in pl.get('tracks', []):
                    pl['tracks'].remove(track_path)
                    self._save_playlists()
    
    def reorder_playlist(self, playlist_id: str, from_index: int, to_index: int):
        """Reorder tracks in a playlist."""
        with self._lock:
            if playlist_id in self._playlists:
                pl = self._playlists[playlist_id]
                tracks = pl.get('tracks', [])
                if 0 <= from_index < len(tracks) and 0 <= to_index < len(tracks):
                    track = tracks.pop(from_index)
                    tracks.insert(to_index, track)
                    self._save_playlists()
    
    # Favourites management
    def toggle_favourite(self, track_path: str) -> bool:
        """Toggle favourite status for a track."""
        with self._lock:
            if track_path in self._favourites:
                self._favourites.remove(track_path)
                return False
            else:
                self._favourites.add(track_path)
                return True
    
    def get_favourites(self) -> List[str]:
        """Get list of favourite track paths."""
        with self._lock:
            return list(self._favourites)
    
    def is_favourite(self, track_path: str) -> bool:
        """Check if a track is a favourite."""
        with self._lock:
            return track_path in self._favourites
    
    # Settings management
    def _load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._settings = {}
    
    def _save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get a setting value."""
        with self._lock:
            return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        with self._lock:
            self._settings[key] = value
            self._save_settings()
    
    # Playback state persistence
    def _load_playback_state(self):
        try:
            if self.playback_file.exists():
                with open(self.playback_file, 'r', encoding='utf-8') as f:
                    self._playback_state = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._playback_state = {}
    
    def _save_playback_state(self):
        try:
            with open(self.playback_file, 'w', encoding='utf-8') as f:
                json.dump(self._playback_state, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving playback state: {e}")
    
    def save_playback_state(self, state: Dict):
        """Save playback state."""
        with self._lock:
            self._playback_state = state
            self._save_playback_state()
    
    def load_playback_state(self) -> Dict:
        """Load playback state."""
        with self._lock:
            return dict(self._playback_state)