'use client';

import React, { useState } from 'react';
import { Database, Cpu, Zap, CheckCircle2, Server, Layers } from 'lucide-react';

export default function DatabaseFlowDiagram() {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('ai-engine');

  return (
    <section id="overview" className="py-20 bg-black relative border-t border-zinc-900 rounded-none overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="max-w-3xl mb-12">
          <div className="text-xs font-mono text-sky-400 font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
            <Zap className="w-3.5 h-3.5" />
            <span>Interactive Data Architecture</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight mb-3">
            Multi-Source Database Migration Topology
          </h2>
          <p className="text-zinc-400 text-sm leading-relaxed">
            Visualizing real-time schema translation and zero-OOM chunked record streaming from two independent source databases into one unified target data warehouse.
          </p>
        </div>

        {/* Frameless Dark Topology Layout */}
        <div className="relative min-h-[440px] flex flex-col justify-between py-2">
          {/* Status Header Bar */}
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4 mb-8 text-xs font-mono">
            <span className="text-zinc-300 uppercase tracking-wider flex items-center gap-2 font-bold">
              <Layers className="w-4 h-4 text-sky-400" />
              Live Architecture Diagram
            </span>
            <span className="text-sky-400 font-semibold flex items-center gap-2 bg-zinc-900 px-3 py-1 border border-zinc-800">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              STREAM ACTIVE
            </span>
          </div>

          {/* Floating Diagram Nodes Layout */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 items-center relative my-auto">
            {/* SVG Connecting Lines (Desktop) */}
            <div className="hidden md:block absolute inset-0 pointer-events-none z-0">
              <svg className="w-full h-full" overflow="visible">
                <line
                  x1="28%"
                  y1="25%"
                  x2="50%"
                  y2="50%"
                  stroke="rgba(56,189,248,0.3)"
                  strokeWidth="2"
                  strokeDasharray="5 5"
                />
                <line
                  x1="28%"
                  y1="75%"
                  x2="50%"
                  y2="50%"
                  stroke="rgba(56,189,248,0.3)"
                  strokeWidth="2"
                  strokeDasharray="5 5"
                />
                <line
                  x1="50%"
                  y1="50%"
                  x2="72%"
                  y2="50%"
                  stroke="rgba(56,189,248,0.4)"
                  strokeWidth="2"
                  strokeDasharray="6 4"
                />
              </svg>
            </div>

            {/* Column 1: Source Databases */}
            <div className="space-y-5 relative z-10">
              {/* Node: Source DB 1 */}
              <button
                onClick={() => setSelectedNodeId('source-1')}
                className={`w-full p-5 text-left rounded-none border transition-all duration-200 ${
                  selectedNodeId === 'source-1'
                    ? 'bg-zinc-900 border-sky-400 text-white shadow-lg'
                    : 'bg-zinc-950/80 border-zinc-800 hover:border-zinc-700 text-zinc-300'
                }`}
              >
                <div className="flex items-center gap-3 mb-1.5">
                  <Database className="w-5 h-5 text-sky-400 shrink-0" />
                  <span className="font-bold text-xs uppercase tracking-tight">
                    PostgreSQL DB 1
                  </span>
                </div>
                <div className="text-[11px] font-mono text-zinc-400">750,000 Records</div>
              </button>

              {/* Node: Source DB 2 */}
              <button
                onClick={() => setSelectedNodeId('source-2')}
                className={`w-full p-5 text-left rounded-none border transition-all duration-200 ${
                  selectedNodeId === 'source-2'
                    ? 'bg-zinc-900 border-sky-400 text-white shadow-lg'
                    : 'bg-zinc-950/80 border-zinc-800 hover:border-zinc-700 text-zinc-300'
                }`}
              >
                <div className="flex items-center gap-3 mb-1.5">
                  <Server className="w-5 h-5 text-sky-400 shrink-0" />
                  <span className="font-bold text-xs uppercase tracking-tight">
                    MySQL DB 2
                  </span>
                </div>
                <div className="text-[11px] font-mono text-zinc-400">500,000 Records</div>
              </button>
            </div>

            {/* Column 2: Migraflow AI Engine Node */}
            <div className="relative z-10">
              <button
                onClick={() => setSelectedNodeId('ai-engine')}
                className={`w-full p-6 text-center rounded-none border transition-all duration-200 ${
                  selectedNodeId === 'ai-engine'
                    ? 'bg-zinc-900 border-sky-400 shadow-xl'
                    : 'bg-zinc-950/90 border-zinc-800 hover:border-zinc-700'
                }`}
              >
                <div className="w-10 h-10 mx-auto mb-2.5 rounded-none bg-sky-400/10 border border-sky-400/30 flex items-center justify-center text-sky-400">
                  <Cpu className="w-5 h-5" />
                </div>
                <div className="font-bold text-xs text-white uppercase tracking-wider mb-1">
                  Migraflow AI Engine
                </div>
                <div className="text-[11px] font-mono text-sky-400 font-medium">
                  Zero-OOM Streaming
                </div>
              </button>
            </div>

            {/* Column 3: Target Database Warehouse */}
            <div className="relative z-10">
              <button
                onClick={() => setSelectedNodeId('target-db')}
                className={`w-full p-5 text-left rounded-none border transition-all duration-200 ${
                  selectedNodeId === 'target-db'
                    ? 'bg-zinc-900 border-emerald-400 text-white shadow-lg'
                    : 'bg-zinc-950/80 border-zinc-800 hover:border-zinc-700 text-zinc-300'
                }`}
              >
                <div className="flex items-center gap-3 mb-1.5">
                  <Database className="w-5 h-5 text-emerald-400 shrink-0" />
                  <span className="font-bold text-xs uppercase tracking-tight">
                    Target Warehouse
                  </span>
                </div>
                <div className="text-[11px] font-mono text-emerald-400 font-semibold">
                  1.25M / 1.25M Synced
                </div>
              </button>
            </div>
          </div>

          {/* Bottom Real-time Telemetry Bar */}
          <div className="mt-8 pt-4 border-t border-zinc-800/80 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-zinc-400">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="font-bold text-zinc-300">Zero OOM Crashes</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
