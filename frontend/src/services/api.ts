import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
export const api = axios.create({ baseURL: API_BASE })

export type PrepareRequest = { datasetId: string; params?: Record<string, any> }
export async function prepareData(req: PrepareRequest) {
  const { data } = await api.post('/v1/data/prepare', req)
  return data
}

export type TargetDetectRequest = { datasetId: string; userTarget?: string; llmSuggestion?: string; openaiApiKey?: string | null }
export async function detectTarget(req: TargetDetectRequest) {
  const { data } = await api.post('/v1/target/detect', req)
  return data
}

export type TrainRequest = { datasetId: string; target: string; problemType: string; params?: Record<string, any> }
export async function trainModel(req: TrainRequest) {
  const { data } = await api.post('/v1/model/train', req)
  return data
}

export async function jobStatus(jobId: string) {
  const { data } = await api.get(`/v1/jobs/${jobId}`)
  return data
}

export async function featureImportance(modelId: string) {
  const { data } = await api.get('/v1/charts/feature-importance', { params: { modelId } })
  return data
}

export async function uploadFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/v1/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

export async function getSchema(datasetId: string) {
  const { data } = await api.get(`/v1/data/${datasetId}/schema`)
  return data
}

export async function getSummary(datasetId: string) {
  const { data } = await api.get(`/v1/data/${datasetId}/summary`)
  return data
}

export type AIStep1Request = { datasetId: string; openaiApiKey: string }
export async function aiStep1(req: AIStep1Request) {
  const { data } = await api.post('/v1/ai/step1-business-domain', req)
  return data
}

export type AIStep2Request = { datasetId: string; businessDomain: string; openaiApiKey: string }
export async function aiStep2(req: AIStep2Request) {
  const { data } = await api.post('/v1/ai/step2-target-with-domain', req)
  return data
}

export type AIStep3Request = { datasetId: string; businessDomain: string; targetColumn: string; openaiApiKey: string }
export async function aiStep3(req: AIStep3Request) {
  const { data } = await api.post('/v1/ai/step3-column-correlations', req)
  return data
}

export type AIStep4Request = { datasetId: string; businessDomain: string; targetColumn: string; openaiApiKey: string }
export async function aiStep4(req: AIStep4Request) {
  const { data } = await api.post('/v1/ai/step4-cleaning-suggestions', req)
  return data
}

export type LLMReportRequest = { datasetId: string; modelId: string; businessDomain: string; targetColumn: string; aiSteps: Record<string, any>; openaiApiKey: string }
export async function generateLLMReport(req: LLMReportRequest) {
  const { data } = await api.post('/v1/report/llm', req)
  return data
}

export async function downloadReportPDF(reportId: string) {
  const response = await api.get(`/v1/report/${reportId}/pdf`, { responseType: 'blob' })
  return response.data
}

export async function downloadReportMarkdown(reportId: string) {
  const response = await api.get(`/v1/report/${reportId}/markdown`, { responseType: 'blob' })
  return response.data
}

export async function getReportCharts(reportId: string) {
  const { data } = await api.get(`/v1/report/${reportId}/charts`)
  return data
}

export async function getOpenAIStatus() {
  const { data } = await api.get('/v1/config/openai-status')
  return data
}


