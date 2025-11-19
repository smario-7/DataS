import { create } from 'zustand'

type FlowState = {
  datasetId?: string
  target?: string
  problemType?: 'regresja' | 'klasyfikacja'
  modelId?: string
  openaiApiKey?: string | null
  showMainApp?: boolean
  setDatasetId: (v?: string) => void
  setTarget: (t?: string, p?: 'regresja' | 'klasyfikacja') => void
  setModelId: (m?: string) => void
  setOpenaiApiKey: (k?: string | null) => void
  setShowMainApp: (s: boolean) => void
}

export const useFlowStore = create<FlowState>((set) => ({
  datasetId: undefined,
  target: undefined,
  problemType: undefined,
  modelId: undefined,
  openaiApiKey: undefined,
  showMainApp: false,
  setDatasetId: (v) => set({ datasetId: v }),
  setTarget: (t, p) => set({ target: t, problemType: p }),
  setModelId: (m) => set({ modelId: m }),
  setOpenaiApiKey: (k) => set({ openaiApiKey: k }),
  setShowMainApp: (s) => set({ showMainApp: s }),
}))


