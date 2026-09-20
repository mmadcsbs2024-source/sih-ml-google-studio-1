import React, { useState } from 'react';
import { MODULES_AUDIT_DATA } from '../data/modulesData';
import { CheckCircle2, ShieldCheck, AlertCircle, FileCode, ArrowRight, BookOpen } from 'lucide-react';

export const ModulesExplorer: React.FC = () => {
  const [selectedModuleNum, setSelectedModuleNum] = useState<number>(1);
  const activeModule = MODULES_AUDIT_DATA.find(m => m.moduleNumber === selectedModuleNum) || MODULES_AUDIT_DATA[0];

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="bg-slate-800/60 rounded-xl p-5 border border-slate-700/60 backdrop-blur">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Project Audit Lifecycle & Scientific Verification</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              SIH26001 Modules 1–8 Verification Matrix
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-3xl">
              Inspect verified analytical findings, data cleaning decisions, conservative date parsing, boundary sampling, and environmental contracts across all project modules.
            </p>
          </div>

          <div className="flex items-center space-x-2 bg-emerald-950/60 border border-emerald-800/60 px-3 py-2 rounded-lg text-emerald-300 text-xs font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Modules 1–7 Verified PASS • Module 8 Operational in Web</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Module Selection Rail */}
        <div className="lg:col-span-4 space-y-2">
          {MODULES_AUDIT_DATA.map((mod) => {
            const isSelected = mod.moduleNumber === selectedModuleNum;
            return (
              <button
                key={mod.moduleNumber}
                onClick={() => setSelectedModuleNum(mod.moduleNumber)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                  isSelected
                    ? 'bg-rose-500/15 border-rose-500/40 shadow-lg'
                    : 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/70'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Module {mod.moduleNumber}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                    PASS
                  </span>
                </div>
                <div className="text-sm font-semibold text-white mt-1">
                  {mod.name}
                </div>
                <div className="text-xs text-slate-400 font-mono mt-1 truncate">
                  {mod.implementationFile}
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Module Detail Panel */}
        <div className="lg:col-span-8 space-y-5">
          <div className="bg-slate-800/40 rounded-xl p-6 border border-slate-700/60 space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-700 pb-4 gap-2">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-rose-400">
                  Module {activeModule.moduleNumber} Specification
                </span>
                <h3 className="text-xl font-bold text-white mt-0.5">
                  {activeModule.name}
                </h3>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-300 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-700">
                <FileCode className="w-3.5 h-3.5 text-sky-400" />
                <span>{activeModule.implementationFile}</span>
              </div>
            </div>

            {/* Findings Table */}
            <div>
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Verified Statistical Findings
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(activeModule.findings).map(([key, val]) => (
                  <div
                    key={key}
                    className="bg-slate-900/60 border border-slate-700/50 p-3 rounded-lg flex items-center justify-between text-xs"
                  >
                    <span className="text-slate-400 font-medium">{key}</span>
                    <span className="font-mono font-bold text-white text-sm">
                      {typeof val === 'number' ? val.toLocaleString() : val}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Scientific Principles */}
            <div>
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-rose-400" />
                <span>Core Scientific Principles & Invariants</span>
              </h4>
              <div className="space-y-2">
                {activeModule.scientificPrinciples.map((principle, idx) => (
                  <div
                    key={idx}
                    className="flex items-start space-x-2.5 p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-xs text-slate-300"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{principle}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Implementation Notes & Outputs */}
            <div className="pt-2 border-t border-slate-700/60 flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs text-slate-400 gap-2">
              <div>
                <span className="text-slate-500 font-medium">Primary Outputs: </span>
                <span className="font-mono text-slate-300">{activeModule.primaryOutputs.join(', ')}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-900/70 border border-slate-800 text-xs text-slate-300">
              <span className="text-slate-400 font-semibold uppercase tracking-wider block mb-1">
                Engineering Assessment:
              </span>
              <p className="leading-relaxed">{activeModule.notes}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
