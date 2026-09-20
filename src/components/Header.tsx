import React from 'react';
import { ShieldAlert, Compass, Database, FileCheck2, CloudRain, Activity } from 'lucide-react';

interface HeaderProps {
  activeTab: 'predictor' | 'map' | 'modules' | 'data' | 'copernicus';
  onTabChange: (tab: 'predictor' | 'map' | 'modules' | 'data' | 'copernicus') => void;
  systemStatus?: string;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-500 flex items-center justify-center shadow-lg shadow-rose-900/30 text-white">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  SIH26001
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  NER India Baseline
                </span>
              </div>
              <h1 className="text-base sm:text-lg font-bold text-white tracking-tight leading-tight">
                Landslide Early Warning & Risk Monitoring
              </h1>
            </div>
          </div>

          {/* Navigation tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              id="nav-predictor-btn"
              onClick={() => onTabChange('predictor')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'predictor'
                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Risk Predictor</span>
            </button>

            <button
              id="nav-map-btn"
              onClick={() => onTabChange('map')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'map'
                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Compass className="w-4 h-4" />
              <span>GIS Spatial Map</span>
            </button>

            <button
              id="nav-modules-btn"
              onClick={() => onTabChange('modules')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'modules'
                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <FileCheck2 className="w-4 h-4" />
              <span>Modules 1–8 Audit</span>
            </button>

            <button
              id="nav-data-btn"
              onClick={() => onTabChange('data')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'data'
                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Database className="w-4 h-4" />
              <span>Historical Events</span>
            </button>

            <button
              id="nav-copernicus-btn"
              onClick={() => onTabChange('copernicus')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'copernicus'
                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <CloudRain className="w-4 h-4" />
              <span>ERA5 & DEM Sources</span>
            </button>
          </nav>

          {/* Quick status pill */}
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
              RF Model Active
            </span>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="md:hidden flex items-center justify-between overflow-x-auto py-2 border-t border-slate-800/80 space-x-1">
          <button
            onClick={() => onTabChange('predictor')}
            className={`px-3 py-1.5 rounded-md text-xs whitespace-nowrap font-medium ${
              activeTab === 'predictor' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400'
            }`}
          >
            Predictor
          </button>
          <button
            onClick={() => onTabChange('map')}
            className={`px-3 py-1.5 rounded-md text-xs whitespace-nowrap font-medium ${
              activeTab === 'map' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400'
            }`}
          >
            Spatial Map
          </button>
          <button
            onClick={() => onTabChange('modules')}
            className={`px-3 py-1.5 rounded-md text-xs whitespace-nowrap font-medium ${
              activeTab === 'modules' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400'
            }`}
          >
            Modules 1–8
          </button>
          <button
            onClick={() => onTabChange('data')}
            className={`px-3 py-1.5 rounded-md text-xs whitespace-nowrap font-medium ${
              activeTab === 'data' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400'
            }`}
          >
            Events Catalog
          </button>
          <button
            onClick={() => onTabChange('copernicus')}
            className={`px-3 py-1.5 rounded-md text-xs whitespace-nowrap font-medium ${
              activeTab === 'copernicus' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400'
            }`}
          >
            ERA5 & DEM
          </button>
        </div>
      </div>
    </header>
  );
};
