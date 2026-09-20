import React, { useState, useMemo } from 'react';
import spatialData from '../data/nerSpatialData.json';
import { LandslideRecord } from '../types';
import { Search, Filter, Download, ArrowUpDown, ChevronLeft, ChevronRight, FileText, MapPin } from 'lucide-react';

export const DataBrowser: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedState, setSelectedState] = useState('ALL');
  const [selectedMaterial, setSelectedMaterial] = useState('ALL');
  const [selectedDateStatus, setSelectedDateStatus] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedRecordId, setExpandedRecordId] = useState<string | null>(null);

  const pageSize = 15;

  const records = spatialData.sampleEvents as LandslideRecord[];

  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      if (selectedState !== 'ALL' && r.state !== selectedState) return false;
      if (selectedMaterial !== 'ALL' && r.material !== selectedMaterial) return false;
      if (selectedDateStatus !== 'ALL' && r.dateStatus !== selectedDateStatus) return false;

      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchName = (r.name || '').toLowerCase().includes(query);
        const matchDistrict = (r.district || '').toLowerCase().includes(query);
        const matchSlideNo = (r.slideNo || '').toLowerCase().includes(query);
        const matchLoc = (r.location || '').toLowerCase().includes(query);
        const matchHist = (r.history || '').toLowerCase().includes(query);
        return matchName || matchDistrict || matchSlideNo || matchLoc || matchHist;
      }
      return true;
    });
  }, [records, selectedState, selectedMaterial, selectedDateStatus, searchTerm]);

  const totalPages = Math.ceil(filteredRecords.length / pageSize) || 1;
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, currentPage]);

  const states = ['ALL', 'Assam', 'Arunachal Pradesh', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura'];
  const materials = ['ALL', 'Debris', 'Earth', 'Rock'];

  const exportCSV = () => {
    const headers = ['SlNo', 'SlideNo', 'State', 'District', 'Name', 'Location', 'Latitude', 'Longitude', 'Material', 'Movement', 'Date', 'DateStatus', 'History'];
    const rows = filteredRecords.map(r => [
      r.id,
      `"${(r.slideNo || '').replace(/"/g, '""')}"`,
      `"${r.state}"`,
      `"${r.district}"`,
      `"${(r.name || '').replace(/"/g, '""')}"`,
      `"${(r.location || '').replace(/"/g, '""')}"`,
      r.lat,
      r.lon,
      `"${r.material || ''}"`,
      `"${r.movement || ''}"`,
      `"${r.date || ''}"`,
      `"${r.dateStatus || ''}"`,
      `"${(r.history || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `sih26001_landslide_events_${selectedState.toLowerCase()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Search and Filters Bar */}
      <div className="bg-slate-800/60 rounded-xl p-5 border border-slate-700/60 backdrop-blur space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Historical Landslide Events Dataset
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified GSI observations across 8 North Eastern Region states with complete audit provenance.
            </p>
          </div>

          <button
            onClick={exportCSV}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-100 text-xs font-medium transition-colors shrink-0 shadow border border-slate-600"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Filtered CSV ({filteredRecords.length})</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Keyword Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search slide name, highway, notes..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />
          </div>

          {/* State Filter */}
          <div>
            <select
              value={selectedState}
              onChange={(e) => {
                setSelectedState(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
            >
              {states.map(s => (
                <option key={s} value={s}>{s === 'ALL' ? 'All 8 NER States' : s}</option>
              ))}
            </select>
          </div>

          {/* Material Filter */}
          <div>
            <select
              value={selectedMaterial}
              onChange={(e) => {
                setSelectedMaterial(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
            >
              {materials.map(m => (
                <option key={m} value={m}>{m === 'ALL' ? 'All Materials' : m}</option>
              ))}
            </select>
          </div>

          {/* Date Status Filter */}
          <div>
            <select
              value={selectedDateStatus}
              onChange={(e) => {
                setSelectedDateStatus(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
            >
              <option value="ALL">All Date Precision Types</option>
              <option value="exact_date">Exact Dates Only (Module 3 verified)</option>
              <option value="year_only">Year Only (e.g. 2019)</option>
              <option value="month_only">Month Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table of Records */}
      <div className="bg-slate-800/40 rounded-xl border border-slate-700/60 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-slate-700 text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Slide No / ID</th>
                <th className="py-3 px-4">State & District</th>
                <th className="py-3 px-4">Slide Name / Highway</th>
                <th className="py-3 px-4">Coordinates</th>
                <th className="py-3 px-4">Material</th>
                <th className="py-3 px-4">Event Date</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {paginatedRecords.length > 0 ? (
                paginatedRecords.map((r) => {
                  const isExpanded = expandedRecordId === r.id;
                  return (
                    <React.Fragment key={r.id}>
                      <tr className={`hover:bg-slate-800/50 transition-colors ${isExpanded ? 'bg-slate-800/60' : ''}`}>
                        <td className="py-3 px-4 font-mono text-slate-200">
                          <span className="font-bold text-rose-400 mr-2">#{r.id}</span>
                          <span className="text-[11px] text-slate-400">{r.slideNo}</span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-white">{r.state}</div>
                          <div className="text-[11px] text-slate-400">{r.district}</div>
                        </td>
                        <td className="py-3 px-4 max-w-xs">
                          <div className="font-medium text-slate-100 truncate">{r.name || 'Unnamed Slide'}</div>
                          {r.location && <div className="text-[11px] text-slate-400 truncate">{r.location}</div>}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                          {r.lat.toFixed(4)}°N, {r.lon.toFixed(4)}°E
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-[11px]">
                            {r.material || 'Debris'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-mono text-slate-200">{r.date || 'Historical'}</div>
                          <div className={`text-[10px] ${r.dateStatus === 'exact_date' ? 'text-emerald-400' : 'text-slate-400'}`}>
                            {r.dateStatus}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setExpandedRecordId(isExpanded ? null : r.id)}
                            className="text-xs text-rose-400 hover:text-rose-300 font-medium"
                          >
                            {isExpanded ? 'Hide' : 'Inspect'}
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-slate-900/90 border-y border-slate-700/80">
                          <td colSpan={7} className="p-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                              <div>
                                <span className="font-semibold text-slate-400 block mb-1">
                                  Geotechnical Attributes:
                                </span>
                                <div className="space-y-1 text-slate-300">
                                  <div><strong className="text-slate-400">Material:</strong> {r.material}</div>
                                  <div><strong className="text-slate-400">Movement Type:</strong> {r.movement}</div>
                                  <div><strong className="text-slate-400">Candidate Quality:</strong> {r.quality}</div>
                                </div>
                              </div>
                              <div>
                                <span className="font-semibold text-slate-400 block mb-1">
                                  GSI Historical Incident Narrative:
                                </span>
                                <p className="italic text-slate-300 bg-slate-950 p-2.5 rounded border border-slate-800">
                                  "{r.history || 'No textual narrative provided in historical catalog.'}"
                                </p>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No matching landslide records found for the current query and filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-900/80 border-t border-slate-700 text-xs text-slate-400">
          <div>
            Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filteredRecords.length)} of {filteredRecords.length} records
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-slate-300">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-white"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
