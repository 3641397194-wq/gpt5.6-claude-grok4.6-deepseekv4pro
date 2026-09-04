const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("coldbrew", {
  meta: () => ipcRenderer.invoke("coldbrew:meta"),
  activate: (payload) => ipcRenderer.invoke("coldbrew:activate", payload),
  inspect: () => ipcRenderer.invoke("coldbrew:inspect"),
  gemini: (verb, payload) => ipcRenderer.invoke("coldbrew:gemini", verb, payload),
  openDocs: () => ipcRenderer.invoke("coldbrew:open-docs"),
  openExternal: (url) => ipcRenderer.invoke("coldbrew:open-external", url),
  minimize: () => ipcRenderer.invoke("window:minimize"),
  maximize: () => ipcRenderer.invoke("window:maximize"),
  close: () => ipcRenderer.invoke("window:close"),
});
