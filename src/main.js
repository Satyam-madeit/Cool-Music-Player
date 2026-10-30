const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// Supported audio extensions
const AUDIO_EXTENSIONS = ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac'];

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 760,
    minWidth: 700,
    minHeight: 500,
    backgroundColor: '#0a0a0a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
      allowRunningInsecureContent: false
    }
  });

  win.loadFile(path.join(__dirname, 'renderer.html'));
  return win;
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// --- Secure IPC handlers ---

// Let the user pick a music folder (local only)
ipcMain.handle('select-music-folder', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory', 'createDirectory']
  });
  return result.canceled ? null : result.filePaths[0];
});

// Recursively scan a folder for audio files (local FS only, no network)
ipcMain.handle('scan-audio-files', async (event, folderPath) => {
  if (!folderPath || typeof folderPath !== 'string') {
    return { error: 'Invalid folder path' };
  }

  // Security: resolve and confirm the path exists on disk
  let resolved;
  try {
    resolved = path.resolve(folderPath);
    if (!fs.existsSync(resolved)) {
      return { error: 'Folder does not exist' };
    }
    const stat = fs.statSync(resolved);
    if (!stat.isDirectory()) {
      return { error: 'Path is not a folder' };
    }
  } catch (err) {
    return { error: 'Cannot access folder' };
  }

  const tracks = [];

  function walk(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (err) {
      return; // skip unreadable dirs
    }

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (AUDIO_EXTENSIONS.includes(ext)) {
          tracks.push({
            name: entry.name,
            path: fullPath,
            ext: ext
          });
        }
      }
    }
  }

  walk(resolved);
  return { tracks, count: tracks.length };
});

// Read a file as a base64 data URL so the renderer can play it via <audio>
// (keeps everything local — no network)
ipcMain.handle('read-audio-file', async (event, filePath) => {
  if (!filePath || typeof filePath !== 'string') return null;
  let resolved;
  try {
    resolved = path.resolve(filePath);
    if (!fs.existsSync(resolved)) return null;
    const stat = fs.statSync(resolved);
    if (!stat.isFile()) return null;
  } catch (err) {
    return null;
  }

  const ext = path.extname(resolved).toLowerCase();
  const mime = {
    '.mp3': 'audio/mpeg',
    '.flac': 'audio/flac',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
    '.ogg': 'audio/ogg',
    '.aac': 'audio/aac'
  }[ext] || 'application/octet-stream';

  const buffer = fs.readFileSync(resolved);
  const base64 = buffer.toString('base64');
  return `data:${mime};base64,${base64}`;
});
