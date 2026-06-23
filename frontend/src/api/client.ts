import axios from 'axios';
import type { AnalysisResponse, SamplesResponse, HealthResponse, DatasetSummary, HistoryResponse } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 120_000, // YOLO inference can take time on first run
});

/** Upload an image and run full analysis pipeline */
export async function analyzeImage(file: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<AnalysisResponse>('/api/analyze', formData);
  return data;
}

/** Analyze a sample image by its ID */
export async function analyzeSample(sampleId: string): Promise<AnalysisResponse> {
  const { data } = await api.post<AnalysisResponse>(`/api/analyze-sample/${sampleId}`);
  return data;
}

/** Fetch list of available sample images */
export async function fetchSamples(): Promise<SamplesResponse> {
  const { data } = await api.get<SamplesResponse>('/api/samples');
  return data;
}

/** Health check */
export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/api/health');
  return data;
}

/** Fetch dataset summary analytics */
export async function fetchDatasetSummary(): Promise<DatasetSummary> {
  const { data } = await api.get<DatasetSummary>('/api/dataset/summary');
  return data;
}

/** Fetch analysis history */
export async function fetchHistory(limit = 20): Promise<HistoryResponse> {
  const { data } = await api.get<HistoryResponse>(`/api/history?limit=${limit}`);
  return data;
}

/** Get the URL for exporting a report */
export function getExportUrl(analysisId: string): string {
  return `${api.defaults.baseURL || ''}/api/export/${analysisId}`;
}
