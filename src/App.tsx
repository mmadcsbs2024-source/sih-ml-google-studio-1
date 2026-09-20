import React, { useState } from 'react';
import { Header } from './components/Header';
import { PredictorView } from './components/PredictorView';
import { SpatialMap } from './components/SpatialMap';
import { ModulesExplorer } from './components/ModulesExplorer';
import { DataBrowser } from './components/DataBrowser';
import { CopernicusPipeline } from './components/CopernicusPipeline';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Shield, Sparkles, CheckCircle } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'predictor' | 'map' | 'modules' | 'data' | 'copernicus'>('predictor');

  const handleSelectEventForPredictor = (event: {
    state: string;
    district: string;
    lat: number;
    lon: number;
    material: string;
    movement: string;
  }) => {
    setActiveTab('predictor');
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <ErrorBoundary>
          {activeTab === 'predictor' && <PredictorView />}
          {activeTab === 'map' && <SpatialMap onSelectEventForPredictor={handleSelectEventForPredictor} />}
          {activeTab === 'modules' && <ModulesExplorer />}
          {activeTab === 'data' && <DataBrowser />}
          {activeTab === 'copernicus' && <CopernicusPipeline />}
        </ErrorBoundary>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-6 text-xs text-slate-400 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-rose-500" />
            <span className="font-semibold text-slate-300">
              SIH26001 • AI-Based Early Warning & Landslide Risk Monitoring System
            </span>
          </div>
          <div className="flex items-center space-x-4 text-[11px] text-slate-400">
            <span>North Eastern Region of India</span>
            <span>•</span>
            <span>Copernicus ERA5-Land & DEM GLO-30</span>
            <span>•</span>
            <span className="text-emerald-400 font-medium">Zero Temporal Leakage</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
