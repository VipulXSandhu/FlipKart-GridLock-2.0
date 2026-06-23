import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { LeftPanel } from './components/layout/LeftPanel';
import { MainSection } from './components/layout/MainSection';
import { RightPanel } from './components/layout/RightPanel';
import { BottomSection } from './components/layout/BottomSection';
import { DatasetDashboard } from './components/analytics/DatasetDashboard';
import { ErrorMessage } from './components/common/ErrorMessage';
import { useAnalysis } from './hooks/useAnalysis';

const App: React.FC = () => {
  const {
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
  } = useAnalysis();

  const isProcessing = status === 'uploading' || status === 'analyzing';
  const [activeTab, setActiveTab] = useState<'live' | 'analytics'>('live');

  return (
    <div className="min-h-screen flex flex-col animate-fade-in">
      {/* Header */}
      <Header 
        health={health} 
        result={result} 
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Error banner */}
      {error && (
        <div className="px-4 pt-3 animate-fade-in">
          <ErrorMessage message={error} onRetry={reset} />
        </div>
      )}

      {/* Main content area */}
      {activeTab === 'live' ? (
        <>
          <div className="flex-1 flex overflow-hidden animate-fade-in">
            {/* Left — Upload & Samples */}
            <LeftPanel
              samples={samples}
              onFileSelect={uploadAndAnalyze}
              onSampleSelect={analyzeFromSample}
              disabled={isProcessing}
            />

            {/* Center — Image Viewer */}
            <MainSection status={status} result={result} />

            {/* Right — Metrics */}
            <RightPanel result={result} />
          </div>

          {/* Bottom — Charts */}
          <BottomSection result={result} history={history} />
        </>
      ) : (
        <div className="animate-fade-in">
          <DatasetDashboard summary={datasetSummary} />
        </div>
      )}
    </div>
  );
};

export default App;
