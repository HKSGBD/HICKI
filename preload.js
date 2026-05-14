const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  onSignal: (callback) => ipcRenderer.on('signal', (event, data) => callback(data)),
  learn: (label) => ipcRenderer.send('learn', { label }),
  onChangePair: (pair) => ipcRenderer.send('change-pair', pair)
});