import { useState, useCallback, useEffect } from 'react';
import type {
  AnalysisResponse,
  SampleImage,
  HealthResponse,
  AppStatus,
  DatasetSummary,
} from '../types';
import { analyzeImage, analyzeSample, fetchSamples, fetchHealth, fetchHistory, fetchDatasetSummary } from '../api/client';

export interface UseAnalysisReturn {
  status: AppStatus;
  result: AnalysisResponse | null;
  error: string | null;
  samples: SampleImage[];
  health: HealthResponse | null;
  history: AnalysisResponse[];
  datasetSummary: DatasetSummary | null;
  uploadAndAnalyze: (file: File) => Promise<void>;
  analyzeFromSample: (sampleId: string) => Promise<void>;
  reset: () => void;
  refreshHistory: () => Promise<void>;
}

export function useAnalysis(): UseAnalysisReturn {
  const [status, setStatus] = useState<AppStatus>('idle');
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [samples, setSamples] = useState<SampleImage[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [history, setHistory] = useState<AnalysisResponse[]>([]);
  const [datasetSummary, setDatasetSummary] = useState<DatasetSummary | null>(null);

  const refreshHistory = useCallback(async () => {
    try {
      const res = await fetchHistory();
      setHistory(res.history || []);
    } catch (err) {
      // fail silently
    }
  }, []);

  // Polling for backend health
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    let isBackendOnline = false;

    const checkBackend = async () => {
      try {
        const res = await fetchHealth();
        setHealth(res);
        
        // If the backend just came online, fetch the rest of the initial data
        if (!isBackendOnline) {
          isBackendOnline = true;
          fetchSamples().then((res) => setSamples(res.samples)).catch(() => {});
          fetchDatasetSummary().then(setDatasetSummary).catch(() => {});
          refreshHistory();
        }
      } catch (err) {
        setHealth(null);
        isBackendOnline = false;
      }
    };

    checkBackend(); // Initial check
    interval = setInterval(checkBackend, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, [refreshHistory]);

  const uploadAndAnalyze = useCallback(async (file: File) => {
    setStatus('uploading');
    setError(null);
    try {
      setStatus('analyzing');
      const data = await analyzeImage(file);
      setResult(data);
      setStatus('complete');
      refreshHistory();
    } catch (err: any) {
      const message =
        err?.response?.data?.detail || err?.message || 'Analysis failed. Please try again.';
      setError(message);
      setStatus('error');
    }
  }, []);

  const analyzeFromSample = useCallback(async (sampleId: string) => {
    setStatus('analyzing');
    setError(null);
    try {
      const data = await analyzeSample(sampleId);
      setResult(data);
      setStatus('complete');
      refreshHistory();
    } catch (err: any) {
      const message =
        err?.response?.data?.detail || err?.message || 'Analysis failed. Please try again.';
      setError(message);
      setStatus('error');
    }
  }, []);

  const reset = useCallback(() => {
    setStatus('idle');
    setResult(null);
    setError(null);
  }, []);

  return {
    status,
    result,
    error,
    samples,
    health,
    history,
    datasetSummary,
    uploadAndAnalyze,
    analyzeFromSample,
    reset,
    refreshHistory,
  };
}
