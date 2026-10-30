// ============================================
// COOL MUSIC PLAYER — RENDERER LOGIC
// Human-made, English only, local & secure.
// ============================================

const api = window.musicPlayerApi;

// Startup check: make sure the secure bridge is available
if (!api || typeof api.selectMusicFolder !== 'function') {
  alert('⚠ Secure music bridge not available.\n\nThe app may not have loaded correctly.\nPlease close and reopen Cool Music Player.');
}

// DOM elements
const btnPick = document.getElementById('btn-pick-folder');
const folderInfo = document.getElementById('folder-info');
const folderPathEl = document.getElementById('folder-path');
const countChip = document.getElementById('count-chip');
const trackCountEl = document.getElementById('track-count');
const searchInput = document.getElementById('search');
const tracklistEl = document.getElementById('tracklist');
const emptyState = document.getElementById('empty-state');

const nowTitle = document.getElementById('now-title');
const nowArtist = document.getElementById('now-artist');
const nowExt = document.getElementById('now-ext');

const btnPlay = document.getElementById('btn-play');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const btnShuffle = document.getElementById('btn-shuffle');
const btnRepeat = document.getElementById('btn-repeat');

const progress = document.getElementById('progress');
const timeCurrent = document.getElementById('time-current');
const timeDuration = document.getElementById('time-duration');
const volumeInput = document.getElementById('volume');

// Audio element
const audio = new Audio();
audio.preload = 'metadata';

// State
let tracks = [];            // all scanned tracks
let filteredTracks = [];    // after search filter
let currentIndex = -1;      // index into filteredTracks
let isPlaying = false;
let isShuffle = false;
let isRepeat = false;
let isUserSeeking = false;

// format seconds -> m:ss
function formatTime(sec) {
  if (!Number.isFinite(sec) || sec < 0) return '0:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

// Escape HTML to prevent injection
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Render the track list
function renderTracks() {
  tracklistEl.innerHTML = '';

  if (filteredTracks.length === 0) {
    emptyState.style.display = 'flex';
    return;
  }
  emptyState.style.display = 'none';

  filteredTracks.forEach((track, idx) => {
    const btn = document.createElement('button');
    btn.className = 'track' + (idx === currentIndex ? ' active' : '');
    btn.innerHTML = `<span class="emoji">🎧</span><span class="name">${escapeHtml(track.name)}</span>`;
    btn.title = track.name;
    btn.addEventListener('click', () => loadAndPlay(idx));
    tracklistEl.appendChild(btn);
  });
}

// Update now-playing UI
function updateNowPlaying() {
  const t = currentTrack();
  if (!t) {
    nowTitle.textContent = 'Select a track';
    nowArtist.textContent = '—';
    nowExt.textContent = '';
    return;
  }
  const name = t.name;
  const dot = name.lastIndexOf('.');
  const displayName = dot > 0 ? name.slice(0, dot) : name;
  const ext = dot > 0 ? name.slice(dot + 1).toUpperCase() : '';

  nowTitle.textContent = displayName;
  nowArtist.textContent = 'Local File';
  nowExt.textContent = ext;
}

function currentTrack() {
  return filteredTracks[currentIndex];
}

// Highlight active row in list
function refreshActiveRow() {
  const buttons = tracklistEl.querySelectorAll('.track');
  buttons.forEach((btn, idx) => {
    btn.classList.toggle('active', idx === currentIndex);
  });
}

// Load a track (fetch base64 from main process) and play
async function loadAndPlay(index) {
  if (index < 0 || index >= filteredTracks.length) return;
  currentIndex = index;
  const track = filteredTracks[index];
  updateNowPlaying();
  refreshActiveRow();
  scrollTrackIntoView(index);

  try {
    const dataUrl = await api.readAudioFile(track.path);
    if (!dataUrl) {
      nowTitle.textContent = '⚠ Could not load file';
      return;
    }
    audio.src = dataUrl;
    audio.volume = parseFloat(volumeInput.value);
    await audio.play();
    isPlaying = true;
    btnPlay.textContent = '⏸';
    btnPlay.classList.add('playing');
  } catch (err) {
    console.error(err);
    nowTitle.textContent = '⚠ Playback error';
  }
}

function togglePlay() {
  if (!currentTrack()) return;
  if (isPlaying) {
    audio.pause();
    isPlaying = false;
    btnPlay.textContent = '▶';
    btnPlay.classList.remove('playing');
  } else {
    audio.play().catch(() => {});
    isPlaying = true;
    btnPlay.textContent = '⏸';
    btnPlay.classList.add('playing');
  }
}

function playPrevious() {
  if (filteredTracks.length === 0) return;
  if (isShuffle) {
    currentIndex = Math.floor(Math.random() * filteredTracks.length);
  } else {
    currentIndex = (currentIndex - 1 + filteredTracks.length) % filteredTracks.length;
  }
  loadAndPlay(currentIndex);
}

function playNext() {
  if (filteredTracks.length === 0) return;
  if (isShuffle) {
    currentIndex = Math.floor(Math.random() * filteredTracks.length);
  } else {
    currentIndex = (currentIndex + 1) % filteredTracks.length;
  }
  loadAndPlay(currentIndex);
}

function scrollTrackIntoView(idx) {
  const btns = tracklistEl.querySelectorAll('.track');
  const el = btns[idx];
  if (el) el.scrollIntoView({ block: 'nearest' });
}

// ----- Event wiring -----

btnPick.addEventListener('click', async () => {
  try {
    const folder = await api.selectMusicFolder();
    if (!folder) return; // user cancelled

    folderPathEl.textContent = folder;
    folderInfo.style.display = 'flex';
    countChip.style.display = 'inline-flex';

    const result = await api.scanAudioFiles(folder);
    if (result.error) {
      alert('⚠ ' + result.error);
      nowTitle.textContent = '⚠ ' + result.error;
      return;
    }
    tracks = result.tracks;
    trackCountEl.textContent = tracks.length;
    applySearch();
  } catch (err) {
    console.error(err);
    alert('⚠ Failed to pick folder: ' + (err && err.message ? err.message : err));
  }
});

searchInput.addEventListener('input', applySearch);

function applySearch() {
  const q = searchInput.value.toLowerCase().trim();
  filteredTracks = tracks.filter(t => t.name.toLowerCase().includes(q));
  // keep current index valid if possible
  if (currentIndex >= filteredTracks.length) currentIndex = filteredTracks.length - 1;
  if (currentIndex < 0 && filteredTracks.length > 0) currentIndex = 0;
  renderTracks();
  if (currentIndex >= 0) {
    updateNowPlaying();
    refreshActiveRow();
  }
}

btnPlay.addEventListener('click', togglePlay);
btnPrev.addEventListener('click', playPrevious);
btnNext.addEventListener('click', playNext);

btnShuffle.addEventListener('click', () => {
  isShuffle = !isShuffle;
  btnShuffle.classList.toggle('active', isShuffle);
});
btnRepeat.addEventListener('click', () => {
  isRepeat = !isRepeat;
  btnRepeat.classList.toggle('active', isRepeat);
});

// Progress bar
audio.addEventListener('loadedmetadata', () => {
  timeDuration.textContent = formatTime(audio.duration);
});
audio.addEventListener('timeupdate', () => {
  if (isUserSeeking) return;
  const pct = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
  progress.value = pct;
  timeCurrent.textContent = formatTime(audio.currentTime);
});
audio.addEventListener('ended', () => {
  if (isRepeat) {
    audio.currentTime = 0;
    audio.play();
  } else {
    playNext();
  }
});

progress.addEventListener('mousedown', () => { isUserSeeking = true; });
progress.addEventListener('mouseup', () => {
  isUserSeeking = false;
  if (audio.duration) {
    audio.currentTime = (progress.value / 100) * audio.duration;
  }
});
progress.addEventListener('change', () => {
  if (audio.duration) {
    audio.currentTime = (progress.value / 100) * audio.duration;
  }
});

volumeInput.addEventListener('input', () => {
  audio.volume = parseFloat(volumeInput.value);
});

// Keyboard shortcuts
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
  if (e.code === 'ArrowLeft') playPrevious();
  if (e.code === 'ArrowRight') playNext();
});
