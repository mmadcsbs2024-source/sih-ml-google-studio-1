import React, { useState, useMemo } from 'react';
import spatialData from '../data/nerSpatialData.json';
import { LandslideRecord } from '../types';
import { MapPin, Filter, Eye, Layers, CheckCircle2, XCircle, Info, ExternalLink } from 'lucide-react';

interface SpatialMapProps {
  onSelectEventForPredictor?: (event: {
    state: string;
    district: string;
    lat: number;
    lon: number;
    material: string;
    movement: string;
  }) => void;
}

export const SpatialMap: React.FC<SpatialMapProps> = ({ onSelectEventForPredictor }) => {
  const [selectedState, setSelectedState] = useState<string>('ALL');
  const [showBackgroundPoints, setShowBackgroundPoints] = useState<boolean>(true);
  const [showPositivePoints, setShowPositivePoints] = useState<boolean>(true);
  const [exactDateOnly, setExactDateOnly] = useState<boolean>(false);
  const [selectedEvent, setSelectedEvent] = useState<LandslideRecord | null>(null);

  // Map coordinate boundaries for NER
  const minLon = 88.0;
  const maxLon = 97.5;
  const minLat = 21.9;
  const maxLat = 29.5;

  const width = 800;
  const height = 550;

  // Projection: geographic (lon, lat) to SVG (x, y)
  const project = (lon: number, lat: number): [number, number] => {
    const x = ((lon - minLon) / (maxLon - minLon)) * (width - 60) + 30;
    const y = ((maxLat - lat) / (maxLat - minLat)) * (height - 60) + 30;
    return [x, y];
  };

  // Convert polygon coordinates to SVG path string
  const boundaryPath = useMemo(() => {
    const coords = spatialData.nerPolygon;
    if (!coords || !Array.isArray(coords)) return '';

    const paths: string[] = [];

    // Helper to traverse multi-polygons
    const processRing = (ring: number[][]) => {
      if (!Array.isArray(ring) || ring.length === 0) return '';
      return ring
        .map((pt, i) => {
          if (!Array.isArray(pt) || pt.length < 2) return '';
          const [x, y] = project(pt[0], pt[1]);
          return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .filter(Boolean)
        .join(' ') + ' Z';
    };

    const traverse = (item: any) => {
      if (Array.isArray(item) && item.length > 0 && typeof item[0][0] === 'number') {
        paths.push(processRing(item));
      } else if (Array.isArray(item)) {
        item.forEach(traverse);
      }
    };

    traverse(coords);
    return paths.join(' ');
  }, []);

  // Filter positive events
  const filteredEvents = useMemo(() => {
    return (spatialData.sampleEvents as LandslideRecord[]).filter((ev) => {
      if (selectedState !== 'ALL' && ev.state !== selectedState) return false;
      if (exactDateOnly && ev.dateStatus !== 'exact_date') return false;
      return true;
    });
  }, [selectedState, exactDateOnly]);

  // Filter background points (landslide = 0)
  const filteredBackground = useMemo(() => {
    return spatialData.sampleBackground;
  }, []);

  const statesList = ['ALL', 'Assam', 'Arunachal Pradesh', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura'];

  return (
    <div className="space-y-6">
      {/* Header controls */}
      <div className="bg-slate-800/60 rounded-xl p-5 border border-slate-700/60 backdrop-blur">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-rose-400 uppercase tracking-wider mb-1">
              <Layers className="w-3.5 h-3.5" />
              <span>GIS Spatial Boundary & Sampling Distribution</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              North Eastern Region (NER) Landslide Map
            </h2>
            <p className="text-sm text-slate-300 mt-1">
              Displays authoritative 8-state NER boundary polygon and validated historical landslide scars (y=1) alongside negative background sample points (y=0).
            </p>
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-rose-500"
              >
                {statesList.map(s => (
                  <option key={s} value={s}>{s === 'ALL' ? 'All 8 NER States' : s}</option>
                ))}
              </select>
            </div>

            <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-700">
              <input
                type="checkbox"
                checked={showPositivePoints}
                onChange={(e) => setShowPositivePoints(e.target.checked)}
                className="rounded accent-rose-500"
              />
              <span className="flex items-center space-x-1">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block"></span>
                <span>Positive (y=1)</span>
              </span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-700">
              <input
                type="checkbox"
                checked={showBackgroundPoints}
                onChange={(e) => setShowBackgroundPoints(e.target.checked)}
                className="rounded accent-sky-500"
              />
              <span className="flex items-center space-x-1">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400 inline-block"></span>
                <span>Background (y=0)</span>
              </span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-700">
              <input
                type="checkbox"
                checked={exactDateOnly}
                onChange={(e) => setExactDateOnly(e.target.checked)}
                className="rounded accent-amber-500"
              />
              <span>Exact Dates Only</span>
            </label>
          </div>
        </div>
      </div>

      {/* Map Canvas and Info Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Map Display */}
        <div className="lg:col-span-8 bg-slate-950 rounded-xl border border-slate-800 p-4 relative overflow-hidden flex flex-col items-center justify-center min-h-[500px]">
          {/* Coordinates Legend */}
          <div className="absolute top-4 left-4 z-10 bg-slate-900/80 backdrop-blur px-3 py-2 rounded-lg border border-slate-800 text-[11px] text-slate-300 space-y-1">
            <div className="font-semibold text-white flex items-center space-x-1">
              <MapPin className="w-3.5 h-3.5 text-rose-500" />
              <span>NER Bounding Envelope</span>
            </div>
            <div>Lon: 88.0°E — 97.4°E</div>
            <div>Lat: 21.9°N — 29.5°N</div>
            <div className="text-slate-400 pt-1 border-t border-slate-800 text-[10px]">
              Showing {filteredEvents.length} events • {filteredBackground.length} background
            </div>
          </div>

          {/* SVG Map */}
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-auto max-h-[600px] select-none"
          >
            {/* Background Grid Lines */}
            <g stroke="#1e293b" strokeWidth="0.5" strokeDasharray="3,3">
              {[89, 91, 93, 95, 97].map(lon => {
                const [x1] = project(lon, minLat);
                const [x2] = project(lon, maxLat);
                return <line key={lon} x1={x1} y1="0" x2={x2} y2={height} />;
              })}
              {[23, 25, 27, 29].map(lat => {
                const [, y1] = project(minLon, lat);
                const [, y2] = project(maxLon, lat);
                return <line key={lat} x1="0" y1={y1} x2={width} y2={y2} />;
              })}
            </g>

            {/* Authoritative NER Boundary Polygon */}
            {boundaryPath && (
              <path
                d={boundaryPath}
                fill="#0f172a"
                stroke="#38bdf8"
                strokeWidth="1.5"
                strokeOpacity="0.8"
                className="transition-colors hover:fill-slate-900"
              />
            )}

            {/* Negative Background Sample Points (landslide = 0) */}
            {showBackgroundPoints &&
              filteredBackground.map((bg, idx) => {
                const [x, y] = project(bg.lon, bg.lat);
                return (
                  <circle
                    key={`bg-${idx}`}
                    cx={x}
                    cy={y}
                    r={2}
                    fill="#38bdf8"
                    fillOpacity={0.4}
                    stroke="#0284c7"
                    strokeWidth={0.5}
                  />
                );
              })}

            {/* Positive Landslide Event Points (landslide = 1) */}
            {showPositivePoints &&
              filteredEvents.map((ev) => {
                const [x, y] = project(ev.lon, ev.lat);
                const isSelected = selectedEvent?.id === ev.id;
                return (
                  <circle
                    key={`ev-${ev.id}`}
                    cx={x}
                    cy={y}
                    r={isSelected ? 6 : 3}
                    fill={isSelected ? '#f43f5e' : '#e11d48'}
                    fillOpacity={isSelected ? 1 : 0.75}
                    stroke={isSelected ? '#ffffff' : '#9f1239'}
                    strokeWidth={isSelected ? 2 : 0.8}
                    className="cursor-pointer hover:scale-150 transition-all"
                    onClick={() => setSelectedEvent(ev)}
                  />
                );
              })}

            {/* State Label Landmarks */}
            <text x={project(92.9, 26.2)[0]} y={project(92.9, 26.2)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Assam</text>
            <text x={project(94.2, 28.1)[0]} y={project(94.2, 28.1)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Arunachal Pradesh</text>
            <text x={project(91.6, 25.5)[0]} y={project(91.6, 25.5)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Meghalaya</text>
            <text x={project(94.0, 24.8)[0]} y={project(94.0, 24.8)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Manipur</text>
            <text x={project(92.8, 23.3)[0]} y={project(92.8, 23.3)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Mizoram</text>
            <text x={project(94.4, 26.1)[0]} y={project(94.4, 26.1)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Nagaland</text>
            <text x={project(88.5, 27.5)[0]} y={project(88.5, 27.5)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Sikkim</text>
            <text x={project(91.7, 23.8)[0]} y={project(91.7, 23.8)[1]} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">Tripura</text>
          </svg>
        </div>

        {/* Event Detail Inspector */}
        <div className="lg:col-span-4 space-y-4">
          {selectedEvent ? (
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/70 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center space-x-1.5">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>Historical Landslide Record</span>
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Sl.No {selectedEvent.id}
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-white leading-snug">
                  {selectedEvent.name || 'Unnamed Slide Occurrence'}
                </h3>
                <div className="text-xs text-slate-300 mt-1">
                  {selectedEvent.district}, {selectedEvent.state}
                </div>
                {selectedEvent.location && (
                  <div className="text-xs text-slate-400 mt-0.5">
                    Location: {selectedEvent.location}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 py-2 border-y border-slate-700/60 text-xs">
                <div>
                  <span className="text-slate-400 block text-[11px]">Slide No:</span>
                  <span className="font-mono text-slate-200 truncate block">{selectedEvent.slideNo}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Coordinates:</span>
                  <span className="font-mono text-slate-200 block">{selectedEvent.lat.toFixed(4)}°N, {selectedEvent.lon.toFixed(4)}°E</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Material Involved:</span>
                  <span className="text-slate-200">{selectedEvent.material || 'Debris'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Movement Type:</span>
                  <span className="text-slate-200">{selectedEvent.movement || 'Slide'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Date Status:</span>
                  <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    selectedEvent.dateStatus === 'exact_date' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-slate-800 text-slate-300'
                  }`}>
                    {selectedEvent.dateStatus}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Recorded Date:</span>
                  <span className="font-mono text-slate-200">{selectedEvent.date || 'Unspecified'}</span>
                </div>
              </div>

              {/* Historical Description */}
              {selectedEvent.history && (
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-700/50">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    GSI History Narrative:
                  </span>
                  <p className="text-xs text-slate-300 italic leading-relaxed">
                    "{selectedEvent.history}"
                  </p>
                </div>
              )}

              {/* Action Button */}
              {onSelectEventForPredictor && (
                <button
                  onClick={() => onSelectEventForPredictor({
                    state: selectedEvent.state,
                    district: selectedEvent.district,
                    lat: selectedEvent.lat,
                    lon: selectedEvent.lon,
                    material: selectedEvent.material,
                    movement: selectedEvent.movement
                  })}
                  className="w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs transition-colors shadow-lg shadow-rose-900/40"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Simulate Risk for This Location</span>
                </button>
              )}
            </div>
          ) : (
            <div className="bg-slate-800/30 rounded-xl p-8 border border-slate-700/50 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
                <MapPin className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-white">Click Any Event on the Map</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Select any red landslide scar (y=1) to inspect its GSI metadata, historical notes, material composition, and test in the ML Early Warning Predictor.
              </p>
            </div>
          )}

          {/* Map Statistics Widget */}
          <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50 text-xs space-y-2">
            <div className="font-semibold text-slate-200">Module 6 Sampling Verification</div>
            <div className="flex justify-between text-slate-300">
              <span>Total NER Positive Scars:</span>
              <span className="font-mono text-rose-400 font-bold">{spatialData.totalRawNER}</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>NER Background Non-Events:</span>
              <span className="font-mono text-sky-400 font-bold">{spatialData.totalRawBackground}</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Boundary Envelope:</span>
              <span className="text-emerald-400 font-semibold">Strict GeoJSON Boundary</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
