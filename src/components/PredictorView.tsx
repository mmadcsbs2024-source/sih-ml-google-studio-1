import React, { useState, useMemo } from 'react';
import { RiskAssessmentInput } from '../types';
import { calculateLandslideRisk } from '../utils/landslideML';
import { AlertTriangle, CloudRain, Mountain, Layers, ShieldCheck, Info, Sparkles, RefreshCw } from 'lucide-react';

const PRESET_LOCATIONS: { name: string; state: string; district: string; lat: number; lon: number; elevation: number; slope: number; desc: string }[] = [
  { name: 'Mawphlang Highway, East Khasi Hills', state: 'Meghalaya', district: 'East Khasi Hills', lat: 25.4510, lon: 91.7580, elevation: 1820, slope: 38, desc: 'High rainfall corridor along Shillong plateau scarp' },
  { name: 'National Highway 10, Gangtok Ridge', state: 'Sikkim', district: 'East Sikkim', lat: 27.3389, lon: 88.6065, elevation: 1650, slope: 42, desc: 'Steep phyllite and weathered schist corridor with high monsoon vulnerability' },
  { name: 'Lumding–Badarpur Hill Section', state: 'Assam', district: 'Dima Hasao', lat: 25.1834, lon: 93.0211, elevation: 620, slope: 31, desc: 'Barail range shale and sandstone debris slides' },
  { name: 'Aizawl West Valley Slope', state: 'Mizoram', district: 'Aizawl', lat: 23.7271, lon: 92.7176, elevation: 1132, slope: 35, desc: 'Tlangnuam formation turbidites and sandstone interbeds' },
  { name: 'Kohima–Mao Highway Corridor', state: 'Nagaland', district: 'Kohima', lat: 25.6751, lon: 94.1086, elevation: 1444, slope: 29, desc: 'Disang shale shear zone susceptible to deep rotational failure' },
  { name: 'Tamenglong Escarpment', state: 'Manipur', district: 'Tamenglong', lat: 24.9866, lon: 93.4984, elevation: 1260, slope: 36, desc: 'Heavy monsoon runoff and steep weathered colluvial slopes' },
  { name: 'Tawang Valley Approach', state: 'Arunachal Pradesh', district: 'Tawang', lat: 27.5861, lon: 91.8594, elevation: 3048, slope: 44, desc: 'High altitude glacial till and fragile Himalayan tectonic belt' }
];

export const PredictorView: React.FC = () => {
  const [formData, setFormData] = useState<RiskAssessmentInput>({
    state: 'Sikkim',
    district: 'East Sikkim',
    lat: 27.3389,
    lon: 88.6065,
    elevation: 1650,
    slope: 38,
    rainfall24h: 78,
    rainfall3day: 145,
    rainfall7day: 230,
    material: 'Debris',
    movementType: 'Slide',
    predictionDate: '2026-09-20',
    isExactDate: true
  });

  const [simulationScenario, setSimulationScenario] = useState<'custom' | 'dry' | 'moderate' | 'cloudburst'>('moderate');

  const handlePresetSelect = (preset: typeof PRESET_LOCATIONS[0]) => {
    setFormData(prev => ({
      ...prev,
      state: preset.state,
      district: preset.district,
      lat: preset.lat,
      lon: preset.lon,
      elevation: preset.elevation,
      slope: preset.slope
    }));
  };

  const applyScenario = (scenario: 'dry' | 'moderate' | 'cloudburst') => {
    setSimulationScenario(scenario);
    if (scenario === 'dry') {
      setFormData(prev => ({ ...prev, rainfall24h: 4, rainfall3day: 12, rainfall7day: 28 }));
    } else if (scenario === 'moderate') {
      setFormData(prev => ({ ...prev, rainfall24h: 55, rainfall3day: 110, rainfall7day: 175 }));
    } else if (scenario === 'cloudburst') {
      setFormData(prev => ({ ...prev, rainfall24h: 142, rainfall3day: 215, rainfall7day: 310 }));
    }
  };

  const result = useMemo(() => calculateLandslideRisk(formData), [formData]);

  const getRiskColors = (level: string) => {
    switch (level) {
      case 'VERY_HIGH':
        return {
          bg: 'bg-rose-950/40 border-rose-500/50',
          text: 'text-rose-400',
          badge: 'bg-rose-500 text-white',
          progress: 'bg-rose-500',
          ring: 'ring-rose-500/30'
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-950/40 border-orange-500/50',
          text: 'text-orange-400',
          badge: 'bg-orange-500 text-slate-950 font-bold',
          progress: 'bg-orange-500',
          ring: 'ring-orange-500/30'
        };
      case 'MODERATE':
        return {
          bg: 'bg-amber-950/40 border-amber-500/50',
          text: 'text-amber-400',
          badge: 'bg-amber-500 text-slate-950 font-bold',
          progress: 'bg-amber-400',
          ring: 'ring-amber-500/30'
        };
      default:
        return {
          bg: 'bg-emerald-950/40 border-emerald-500/50',
          text: 'text-emerald-400',
          badge: 'bg-emerald-500 text-white',
          progress: 'bg-emerald-500',
          ring: 'ring-emerald-500/30'
        };
    }
  };

  const colors = getRiskColors(result.riskLevel);

  return (
    <div className="space-y-6">
      {/* Top Banner with Scientific Context */}
      <div className="bg-slate-800/60 rounded-xl p-5 border border-slate-700/60 backdrop-blur">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-rose-400 uppercase tracking-wider mb-1">
              <Sparkles className="w-3.5 h-3.5" />
              <span>SIH26001 ML Inference Baseline: RandomForestClassifier</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Landslide Susceptibility & Early Warning Assessment
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-3xl">
              Evaluates landslide probability $P(\text{landslide}=1)$ from antecedent rainfall aggregations (Copernicus ERA5-Land), terrain slope, and elevation (Copernicus DEM GLO-30) following strict zero-temporal-leakage protocols.
            </p>
          </div>

          {/* Quick Scenario Toggles */}
          <div className="flex items-center space-x-2 shrink-0 bg-slate-900/80 p-1.5 rounded-lg border border-slate-700/80">
            <span className="text-xs text-slate-400 px-2 font-medium">Precipitation:</span>
            <button
              onClick={() => applyScenario('dry')}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-all ${
                simulationScenario === 'dry'
                  ? 'bg-slate-700 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Dry / Baseline
            </button>
            <button
              onClick={() => applyScenario('moderate')}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-all ${
                simulationScenario === 'moderate'
                  ? 'bg-amber-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Monsoon (55mm)
            </button>
            <button
              onClick={() => applyScenario('cloudburst')}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-all ${
                simulationScenario === 'cloudburst'
                  ? 'bg-rose-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Cloudburst (142mm)
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Parameter Inputs */}
        <div className="lg:col-span-7 space-y-6">
          {/* Preset NER Locations */}
          <div className="bg-slate-800/40 rounded-xl p-5 border border-slate-700/60">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center justify-between">
              <span>Select High-Vulnerability NER Location</span>
              <span className="text-xs text-slate-400 font-normal">7 Monitored Mountain Corridors</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {PRESET_LOCATIONS.map((preset) => {
                const isSelected = formData.state === preset.state && formData.district === preset.district;
                return (
                  <button
                    key={preset.name}
                    onClick={() => handlePresetSelect(preset)}
                    className={`text-left p-2.5 rounded-lg text-xs transition-all border ${
                      isSelected
                        ? 'bg-rose-500/15 border-rose-500/40 text-rose-200'
                        : 'bg-slate-900/60 border-slate-700/50 text-slate-300 hover:bg-slate-800 hover:border-slate-600'
                    }`}
                  >
                    <div className="font-semibold text-white truncate">{preset.name}</div>
                    <div className="text-slate-400 mt-0.5 flex items-center justify-between">
                      <span>{preset.state}</span>
                      <span className="font-mono">{preset.slope}° slope • {preset.elevation}m</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Environmental Factors Form */}
          <div className="bg-slate-800/40 rounded-xl p-5 border border-slate-700/60 space-y-5">
            <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-700/60 pb-2 flex items-center justify-between">
              <span className="flex items-center space-x-2">
                <CloudRain className="w-4 h-4 text-sky-400" />
                <span>Precipitation Predictors (ERA5-Land Hourly)</span>
              </span>
              <span className="text-xs text-slate-400 font-mono">Module 7 / 8 Specs</span>
            </h3>

            {/* 24h Rainfall */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">rainfall_24h (Immediate Flash Trigger)</span>
                <span className="font-mono text-sky-400 font-semibold">{formData.rainfall24h} mm</span>
              </div>
              <input
                id="input-rain-24h"
                type="range"
                min="0"
                max="250"
                step="1"
                value={formData.rainfall24h}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setFormData(prev => ({
                    ...prev,
                    rainfall24h: val,
                    rainfall3day: Math.max(prev.rainfall3day, val),
                    rainfall7day: Math.max(prev.rainfall7day, val)
                  }));
                  setSimulationScenario('custom');
                }}
                className="w-full accent-rose-500 cursor-pointer"
              />
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>0 mm (Dry)</span>
                <span>50 mm (Advisory)</span>
                <span>100 mm (Critical)</span>
                <span>250 mm (Extreme)</span>
              </div>
            </div>

            {/* 3-day Antecedent Rainfall */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">rainfall_3day (72-Hour Antecedent Saturation)</span>
                <span className="font-mono text-sky-400 font-semibold">{formData.rainfall3day} mm</span>
              </div>
              <input
                id="input-rain-3d"
                type="range"
                min="0"
                max="400"
                step="2"
                value={formData.rainfall3day}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setFormData(prev => ({
                    ...prev,
                    rainfall3day: val,
                    rainfall24h: Math.min(prev.rainfall24h, val),
                    rainfall7day: Math.max(prev.rainfall7day, val)
                  }));
                  setSimulationScenario('custom');
                }}
                className="w-full accent-sky-500 cursor-pointer"
              />
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Previous 72 Hours Cumulative Precipitation</span>
                <span>Max: 400 mm</span>
              </div>
            </div>

            {/* 7-day Cumulative Rainfall */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">rainfall_7day (168-Hour Phreatic Water Elevation)</span>
                <span className="font-mono text-sky-400 font-semibold">{formData.rainfall7day} mm</span>
              </div>
              <input
                id="input-rain-7d"
                type="range"
                min="0"
                max="600"
                step="5"
                value={formData.rainfall7day}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setFormData(prev => ({
                    ...prev,
                    rainfall7day: val,
                    rainfall3day: Math.min(prev.rainfall3day, val),
                    rainfall24h: Math.min(prev.rainfall24h, val)
                  }));
                  setSimulationScenario('custom');
                }}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            {/* Geotechnical Terrain Predictors */}
            <h3 className="text-sm font-semibold text-slate-200 border-t border-slate-700/60 pt-4 pb-1 flex items-center space-x-2">
              <Mountain className="w-4 h-4 text-emerald-400" />
              <span>Terrain Predictors (Copernicus DEM GLO-30)</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Slope */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">Slope Angle (°)</span>
                  <span className="font-mono text-emerald-400 font-semibold">{formData.slope}°</span>
                </div>
                <input
                  id="input-slope"
                  type="range"
                  min="0"
                  max="65"
                  step="1"
                  value={formData.slope}
                  onChange={(e) => setFormData(prev => ({ ...prev, slope: parseFloat(e.target.value) }))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <span className="text-[11px] text-slate-400 block">
                  {formData.slope < 20 ? 'Gentle slope' : formData.slope <= 45 ? '⚡ Critical failure zone (25°–45°)' : 'Cliff face'}
                </span>
              </div>

              {/* Elevation */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">Elevation (m)</span>
                  <span className="font-mono text-emerald-400 font-semibold">{formData.elevation} m</span>
                </div>
                <input
                  id="input-elevation"
                  type="range"
                  min="50"
                  max="4500"
                  step="25"
                  value={formData.elevation}
                  onChange={(e) => setFormData(prev => ({ ...prev, elevation: parseFloat(e.target.value) }))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[11px] text-slate-400 block">
                  Copernicus GLO-30 Digital Elevation
                </span>
              </div>
            </div>

            {/* Material & Movement */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Material Involved
                </label>
                <select
                  value={formData.material}
                  onChange={(e) => setFormData(prev => ({ ...prev, material: e.target.value }))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
                >
                  <option value="Debris">Debris / Colluvium (High risk)</option>
                  <option value="Earth">Earth / Weathered Soil</option>
                  <option value="Rock">Rock Mass / Discontinuous</option>
                  <option value="Mixed">Mixed Colluvium & Rock</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Movement Type
                </label>
                <select
                  value={formData.movementType}
                  onChange={(e) => setFormData(prev => ({ ...prev, movementType: e.target.value }))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
                >
                  <option value="Slide">Slide (Rotational / Translational)</option>
                  <option value="Fall">Fall (Rockfall)</option>
                  <option value="Flow">Debris Flow / Mudflow</option>
                  <option value="Topple">Topple</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Prediction Results & Explanation */}
        <div className="lg:col-span-5 space-y-6">
          {/* Main Risk Card */}
          <div className={`rounded-xl p-6 border ${colors.bg} backdrop-blur shadow-xl transition-all`}>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Inference Output
              </span>
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${colors.badge}`}>
                {result.riskLevel.replace('_', ' ')}
              </span>
            </div>

            {/* Probability Gauge & Score */}
            <div className="text-center py-4 border-y border-slate-700/60 my-2">
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                Landslide Probability P(Y=1)
              </div>
              <div className={`text-5xl font-black font-display tracking-tight my-1 ${colors.text}`}>
                {(result.probability * 100).toFixed(1)}%
              </div>
              <div className="text-sm font-semibold text-slate-200">
                {result.alertStatus}
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-950/80 rounded-full h-3 mt-4 overflow-hidden border border-slate-700/50 p-0.5">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${colors.progress}`}
                  style={{ width: `${result.riskScore}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1 px-1">
                <span>0% (Safe)</span>
                <span>25%</span>
                <span>50%</span>
                <span>75%</span>
                <span>100% (Imminent)</span>
              </div>
            </div>

            {/* Civil Defense Recommendation */}
            <div className="mt-4 p-3 rounded-lg bg-slate-900/80 border border-slate-700/60">
              <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>Operational Advisory</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {result.recommendation}
              </p>
            </div>

            {/* Scientific Violations check */}
            {result.scientificViolations.length > 0 && (
              <div className="mt-3 p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs space-y-1">
                <div className="font-semibold flex items-center space-x-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-rose-400" />
                  <span>Scientific Protocol Check:</span>
                </div>
                {result.scientificViolations.map((v, i) => (
                  <div key={i} className="text-[11px]">• {v}</div>
                ))}
              </div>
            )}
          </div>

          {/* Explainable Feature Attribution (Waterfall) */}
          <div className="bg-slate-800/40 rounded-xl p-5 border border-slate-700/60 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center justify-between">
              <span className="flex items-center space-x-1.5">
                <Layers className="w-4 h-4 text-purple-400" />
                <span>Feature Importance Attribution</span>
              </span>
              <span className="text-xs text-slate-400 font-mono">Ensemble Weights</span>
            </h3>

            <div className="space-y-3">
              {result.contributions.map((c) => (
                <div key={c.feature} className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-700/40 text-xs">
                  <div className="flex items-center justify-between font-medium">
                    <span className="text-slate-200">{c.feature}</span>
                    <span className="font-mono font-bold text-slate-100">{c.value}</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        c.impact === 'positive' ? 'bg-rose-500' : 'bg-slate-600'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, c.weight * 3))}%` }}
                    ></div>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1.5 leading-tight">
                    {c.explanation}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
