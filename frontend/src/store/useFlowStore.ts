import { create } from 'zustand'

export type Strategy = 'auto_ai' | 'heuristics' | 'manual'

export type MLSettings = {
  sample_n: number
  random_state: number
  top_n_features: number
  permutation_repeats: number
  test_size: number
}

export type AISteps = {
  step1?: string
  step2?: string
  step3?: any
  step4?: any
}

type FlowState = {
  datasetId?: string
  target?: string
  problemType?: 'regresja' | 'klasyfikacja'
  modelId?: string
  openaiApiKey?: string | null
  openaiApiKeySource?: 'env' | 'manual' | null
  showMainApp?: boolean
  
  // Ustawienia ML
  mlSettings: MLSettings
  strategy: Strategy
  manualColumnChoice?: string
  
  // Analiza AI
  aiSteps: AISteps
  analysisResult?: any
  lastAnalysisParams?: any
  trainingParams?: any
  
  // Wyniki ML
  mlResults?: any
  
  // Raport LLM
  llmReport?: string
  llmCharts?: Record<string, string>
  llmPdf?: Blob | string
  
  // Przygotowanie danych
  prepDone: boolean
  
  // Setters
  setDatasetId: (v?: string) => void
  setTarget: (t?: string, p?: 'regresja' | 'klasyfikacja') => void
  setModelId: (m?: string) => void
  setOpenaiApiKey: (k?: string | null) => void
  setOpenaiApiKeySource: (s?: 'env' | 'manual' | null) => void
  setShowMainApp: (s: boolean) => void
  setMLSettings: (s: Partial<MLSettings>) => void
  setStrategy: (s: Strategy) => void
  setManualColumnChoice: (c?: string) => void
  setAISteps: (steps: Partial<AISteps>) => void
  setAnalysisResult: (r?: any) => void
  setLastAnalysisParams: (p?: any) => void
  setTrainingParams: (p?: any) => void
  setMLResults: (r?: any) => void
  setLLMReport: (r?: string) => void
  setLLMCharts: (c?: Record<string, string>) => void
  setLLMPdf: (p?: Blob | string) => void
  setPrepDone: (d: boolean) => void
}

export const useFlowStore = create<FlowState>((set) => ({
  datasetId: undefined,
  target: undefined,
  problemType: undefined,
  modelId: undefined,
  openaiApiKey: undefined,
  openaiApiKeySource: undefined,
  showMainApp: false,
  
  // Ustawienia ML - domyślne wartości
  mlSettings: {
    sample_n: 0,
    random_state: 42,
    top_n_features: 20,
    permutation_repeats: 5,
    test_size: 0.2,
  },
  strategy: 'auto_ai',
  manualColumnChoice: undefined,
  
  // Analiza AI
  aiSteps: {},
  analysisResult: undefined,
  lastAnalysisParams: undefined,
  trainingParams: undefined,
  
  // Wyniki ML
  mlResults: undefined,
  
  // Raport LLM
  llmReport: undefined,
  llmCharts: undefined,
  llmPdf: undefined,
  
  // Przygotowanie danych
  prepDone: false,
  
  // Setters
  setDatasetId: (v) => set({ datasetId: v }),
  setTarget: (t, p) => set({ target: t, problemType: p }),
  setModelId: (m) => set({ modelId: m }),
  setOpenaiApiKey: (k) => set({ openaiApiKey: k }),
  setOpenaiApiKeySource: (s) => set({ openaiApiKeySource: s }),
  setShowMainApp: (s) => set({ showMainApp: s }),
  setMLSettings: (s) => set((state) => ({ mlSettings: { ...state.mlSettings, ...s } })),
  setStrategy: (s) => set({ strategy: s }),
  setManualColumnChoice: (c) => set({ manualColumnChoice: c }),
  setAISteps: (steps) => set((state) => ({ aiSteps: { ...state.aiSteps, ...steps } })),
  setAnalysisResult: (r) => set({ analysisResult: r }),
  setLastAnalysisParams: (p) => set({ lastAnalysisParams: p }),
  setTrainingParams: (p) => set({ trainingParams: p }),
  setMLResults: (r) => set({ mlResults: r }),
  setLLMReport: (r) => set({ llmReport: r }),
  setLLMCharts: (c) => set({ llmCharts: c }),
  setLLMPdf: (p) => set({ llmPdf: p }),
  setPrepDone: (d) => set({ prepDone: d }),
}))


