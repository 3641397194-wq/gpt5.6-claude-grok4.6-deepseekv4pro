const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("node:path");
const fs = require("node:fs");
const { ACTIVATION_WORD, CONTROL_WORD, PROFILES, SEATS, CHANNELS, activate } = require("./lib/prompt-engine");

const COMMUNITY = {
  qq: [{ name: "交流群", value: "1057540028" }, { name: "专题群", value: "1077074552" }],
  telegram: [
    { name: "群", value: "@chachachacha99999", url: "https://t.me/chachachacha99999" },
    { name: "频道", value: "@chachachacha99999999", url: "https://t.me/chachachacha99999999" },
  ],
};

let splashWindow;
let mainWindow;

function createSplash() {
  splashWindow = new BrowserWindow({
    width: 920,
    height: 560,
    frame: false,
    resizable: false,
    show: false,
    backgroundColor: "#080b0f",
    webPreferences: { contextIsolation: true, sandbox: true },
  });
  splashWindow.loadFile(path.join(__dirname, "splash", "index.html"));
  splashWindow.once("ready-to-show", () => splashWindow.show());
}

function createMain() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1080,
    minHeight: 700,
    frame: false,
    show: false,
    backgroundColor: "#0b0f14",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
}

ipcMain.handle("coldbrew:meta", () => ({
  activation: ACTIVATION_WORD,
  control: CONTROL_WORD,
  profiles: PROFILES,
  seats: SEATS,
  channels: CHANNELS,
  community: COMMUNITY,
  version: "2.0.0",
}));

ipcMain.handle("coldbrew:activate", (_event, payload = {}) => activate({
  word: payload.word,
  profile: payload.profile,
  channel: payload.channel,
  prompt: payload.prompt,
}));

ipcMain.handle("coldbrew:inspect", () => ({
  isolated: true,
  mode: "explicit-input-only",
  filesRead: 0,
  localConfig: "未读取",
  clipboard: "未读取",
  environment: "未读取",
  history: "未读取",
}));

ipcMain.handle("coldbrew:open-docs", async () => {
  const packagedDocs = path.join(process.resourcesPath, "public", "docs", "index.html");
  const localDocs = path.resolve(__dirname, "..", "..", "docs", "index.html");
  const target = app.isPackaged && fs.existsSync(packagedDocs) ? packagedDocs : localDocs;
  if (fs.existsSync(target)) {
    await shell.openPath(target);
    return target;
  }
  await shell.openExternal("https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro");
  return "https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro";
});

ipcMain.handle("coldbrew:open-external", async (_event, value) => {
  const url = String(value || "").trim();
  if (!/^https:\/\/(t\.me|github\.com)(\/|$)/i.test(url)) throw new Error("只允许打开品牌社群或仓库链接");
  await shell.openExternal(url);
  return url;
});

ipcMain.handle("window:minimize", () => mainWindow?.minimize());
ipcMain.handle("window:maximize", () => {
  if (!mainWindow) return false;
  if (mainWindow.isMaximized()) mainWindow.unmaximize(); else mainWindow.maximize();
  return mainWindow.isMaximized();
});
ipcMain.handle("window:close", () => mainWindow?.close());

app.whenReady().then(() => {
  createSplash();
  createMain();
  setTimeout(() => {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    if (mainWindow && !mainWindow.isDestroyed()) { mainWindow.show(); mainWindow.focus(); }
  }, 1800);
});

app.on("window-all-closed", () => app.quit());
