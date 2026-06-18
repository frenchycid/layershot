import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import { spawn, ChildProcess } from 'node:child_process'
import * as path from 'node:path'
import * as fs from 'node:fs'

const PROJECT_ROOT = path.resolve(__dirname, '..', '..')
let win: BrowserWindow | null = null
let pipelineProc: ChildProcess | null = null

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    frame: false,
    titleBarStyle: 'hidden',
    backgroundColor: '#000000',
    vibrancy: 'under-window',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  const devUrl = process.env.VITE_DEV_SERVER_URL
  if (devUrl) {
    win.loadURL(devUrl)
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

/* ── Window controls ── */
ipcMain.handle('window:control', (_e, action: string) => {
  if (!win) return
  if (action === 'minimize') win.minimize()
  else if (action === 'maximize') win.isMaximized() ? win.unmaximize() : win.maximize()
  else if (action === 'close') win.close()
})

/* ── Filesystem helpers ── */
ipcMain.handle('fs:list-moodboards', () => {
  const moodDir = path.join(PROJECT_ROOT, 'data', 'moodboards')
  if (!fs.existsSync(moodDir)) return []
  return fs
    .readdirSync(moodDir, { withFileTypes: true })
    .filter(d => d.isDirectory() && !d.name.startsWith('_') && !d.name.startsWith('.'))
    .map(d => ({
      name: d.name,
      path: path.join(moodDir, d.name),
      count: fs.readdirSync(path.join(moodDir, d.name))
        .filter(f => /\.(jpe?g|png|webp)$/i.test(f)).length,
    }))
})

ipcMain.handle('fs:list-outputs', () => {
  const outDir = path.join(PROJECT_ROOT, 'data', 'outputs')
  if (!fs.existsSync(outDir)) return []
  const walk = (dir: string, base = ''): any[] => {
    const out: any[] = []
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name)
      const rel = base ? `${base}/${entry.name}` : entry.name
      if (entry.isFile() && /\.(png|jpe?g)$/i.test(entry.name)) {
        out.push({ path: full, rel, mtime: fs.statSync(full).mtimeMs })
      }
    }
    return out
  }
  return walk(outDir).sort((a, b) => b.mtime - a.mtime).slice(0, 60)
})

ipcMain.handle('fs:pick-folder', async () => {
  const res = await dialog.showOpenDialog({ properties: ['openDirectory'] })
  if (res.canceled || !res.filePaths.length) return null
  return res.filePaths[0]
})

/* ── Python pipeline ── */
ipcMain.handle('pipeline:run', (_e, args: {
  moodboard: string
  products: string[]
  session: string
  renderMode: string
  backend: string
}) => {
  if (pipelineProc) {
    return { ok: false, error: 'Pipeline already running' }
  }
  const py = process.env.LAYERSHOT_PY || 'python3'
  const cliArgs = [
    'main.py',
    '--backend', args.backend,
    'run',
    '--moodboard', args.moodboard,
    '--products', ...args.products,
    '--session', args.session,
    '--render-mode', args.renderMode,
  ]
  pipelineProc = spawn(py, cliArgs, { cwd: PROJECT_ROOT })

  pipelineProc.stdout?.on('data', (d) => win?.webContents.send('pipeline:log', d.toString()))
  pipelineProc.stderr?.on('data', (d) => win?.webContents.send('pipeline:log', d.toString()))
  pipelineProc.on('close', (code) => {
    win?.webContents.send('pipeline:done', { code })
    pipelineProc = null
  })

  return { ok: true, pid: pipelineProc.pid }
})

ipcMain.handle('pipeline:stop', () => {
  if (pipelineProc) {
    pipelineProc.kill('SIGTERM')
    pipelineProc = null
    return { ok: true }
  }
  return { ok: false }
})

/* ── Health probes ── */
ipcMain.handle('health:check', async () => {
  // Best-effort check: is the config valid, does python3 exist, do moodboards exist
  const moodDir = path.join(PROJECT_ROOT, 'data', 'moodboards')
  return {
    project: fs.existsSync(path.join(PROJECT_ROOT, 'main.py')),
    moodboards: fs.existsSync(moodDir),
    outputs: fs.existsSync(path.join(PROJECT_ROOT, 'data', 'outputs')),
  }
})
