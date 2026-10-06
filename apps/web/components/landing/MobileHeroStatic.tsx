'use client';

import React from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  Terminal,
  ChevronDown,
  ShieldCheck,
  Lock,
} from 'lucide-react';

export default function MobileHeroStatic() {
  return (
    <div className="relative w-full min-h-[85vh] bg-black text-white flex flex-col justify-between pt-28 pb-12 px-4 sm:px-6 md:px-8 overflow-hidden select-none">
      {/* Ambient Radial Gradient Lights */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-2xl h-80 bg-gradient-to-b from-sky-400/20 via-cyan-500/10 to-transparent blur-3xl pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-0 w-72 h-72 bg-indigo-500/10 blur-3xl pointer-events-none -z-10" />

      {/* Main Content Area */}
      <div className="w-full max-w-4xl mx-auto flex flex-col items-center text-center my-auto">
        {/* Status Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[11px] font-mono font-bold uppercase tracking-widest bg-sky-400/10 text-sky-400 border border-sky-400/30 mb-6 backdrop-blur-md shadow-lg shadow-sky-950/20">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>MIGRATION CONTROL PLANE • ACTIVE</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold text-white tracking-tight leading-[1.1] uppercase font-sans">
          Autonomous Database <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-sky-400 via-cyan-300 to-indigo-400 bg-clip-text text-transparent">
            Schema Migration Platform
          </span>
        </h1>

        {/* Sub-headline */}
        <p className="mt-4 sm:mt-6 text-xs sm:text-sm md:text-base text-zinc-400 max-w-xl mx-auto font-mono leading-relaxed">
          Intelligent AST schema translation and zero-OOM chunked streaming ETL across PostgreSQL, MySQL, and MongoDB powered by local Docker agents.
        </p>

        {/* Primary CTA Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5 sm:gap-4 w-full max-w-md mx-auto">
          <Link
            href="/register"
            className="w-full sm:w-auto px-6 py-3.5 bg-sky-400 hover:bg-sky-300 text-black text-xs font-mono font-bold uppercase tracking-wider transition-all duration-200 shadow-xl shadow-sky-950/60 flex items-center justify-center gap-2 group"
          >
            <span>Launch Migration</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <a
            href="#overview"
            className="w-full sm:w-auto px-6 py-3.5 bg-zinc-900/90 hover:bg-zinc-800 text-zinc-200 text-xs font-mono font-bold uppercase tracking-wider border border-zinc-800 hover:border-zinc-700 transition-colors flex items-center justify-center gap-2"
          >
            <Terminal className="w-4 h-4 text-sky-400" />
            <span>Explore Architecture</span>
          </a>
        </div>

        {/* UK GDPR & Air-Gapped Trust Badges */}
        <div className="mt-7 flex flex-wrap items-center justify-center gap-2.5 text-[11px] font-mono">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900/80 border border-sky-400/30 text-sky-300">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
            <span>UK GDPR Compliant</span>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900/80 border border-zinc-800 text-zinc-400">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Air-Gapped Local Execution</span>
          </div>
        </div>
      </div>

      {/* Bottom Scroll Prompt */}
      <div className="mt-8 flex flex-col items-center gap-1 text-zinc-500 hover:text-sky-400 transition-colors">
        <a
          href="#overview"
          aria-label="Scroll to platform details"
          className="flex flex-col items-center gap-1 text-[11px] font-mono uppercase tracking-widest"
        >
          <span>Scroll to explore</span>
          <ChevronDown className="w-4 h-4 text-sky-400 animate-bounce" />
        </a>
      </div>
    </div>
  );
}
