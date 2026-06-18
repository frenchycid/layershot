import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('layershot', {
  windowControl: (action: string) => ipcRenderer.invoke('window:control', action),
  listMoodboards: () => ipcRenderer.invoke('fs:list-moodboards'),
  listOutputs: () => ipcRenderer.invoke('fs:list-outputs'),
  pickFolder: () => ipcRenderer.invoke('fs:pick-folder'),
  health: () => ipcRenderer.invoke('health:check'),
  runPipeline: (args: any) => ipcRenderer.invoke('pipeline:run', args),
  stopPipeline: () => ipcRenderer.invoke('pipeline:stop'),
  onLog: (cb: (chunk: string) => void) => {
    const h = (_e: any, chunk: string) => cb(chunk)
    ipcRenderer.on('pipeline:log', h)
    return () => ipcRenderer.removeListener('pipeline:log', h)
  },
  onDone: (cb: (r: { code: number }) => void) => {
    const h = (_e: any, r: any) => cb(r)
    ipcRenderer.on('pipeline:done', h)
    return () => ipcRenderer.removeListener('pipeline:done', h)
  },
})

declare global {
  interface Window {
    layershot: {
      windowControl: (a: string) => Promise<void>
      listMoodboards: () => Promise<{ name: string; path: string; count: number }[]>
      listOutputs: () => Promise<{ path: string; rel: string; mtime: number }[]>
      pickFolder: () => Promise<string | null>
      health: () => Promise<{ project: boolean; moodboards: boolean; outputs: boolean }>
      runPipeline: (args: any) => Promise<{ ok: boolean; pid?: number; error?: string }>
      stopPipeline: () => Promise<{ ok: boolean }>
      onLog: (cb: (chunk: string) => void) => () => void
      onDone: (cb: (r: { code: number }) => void) => () => void
    }
  }
}
