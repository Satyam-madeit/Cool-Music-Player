// Preload script — secure bridge between main process and renderer.
// Only the exposed functions are available to the renderer. No raw Node access.
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainApi('musicPlayerApi', {
  selectMusicFolder: () => ipcRenderer.invoke('select-music-folder'),
  scanAudioFiles: (folderPath) => ipcRenderer.invoke('scan-audio-files', folderPath),
  readAudioFile: (filePath) => ipcRenderer.invoke('read-audio-file', filePath)
});
