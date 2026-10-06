'use client';

import React from 'react';
import Link from 'next/link';
import { triggerOpenCookieSettings } from '@/hooks/useCookieConsent';
import { ShieldCheck } from 'lucide-react';

export default function Footer() {
  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault();
    const element = document.getElementById(targetId);
    if (element) {
      const navbarHeight = 80;
      const elementPosition = element.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({
        top: elementPosition - navbarHeight,
        behavior: 'smooth',
      });
    }
  };

  return (
    <footer className="bg-black border-t border-zinc-900 pt-14 pb-10 text-zinc-400 text-xs font-sans rounded-none relative overflow-hidden">
      {/* Specular Ambient Glow */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[250px] bg-sky-400/[0.04] rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Main Footer Top Section */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-8 mb-12">
          {/* Brand Info */}
          <div className="flex flex-col items-center md:items-start text-center md:text-left gap-2.5">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-none bg-sky-950/80 border border-sky-400/60 flex items-center justify-center text-sky-400 font-extrabold text-xs shadow-md shadow-sky-950/40 group-hover:border-sky-300 transition-colors">
                M
              </div>
              <span className="font-bold text-base text-white uppercase tracking-tight">
                Migra<span className="text-sky-400">flow</span>
              </span>
            </Link>
            <p className="text-xs font-mono text-zinc-500 max-w-xs leading-relaxed">
              Enterprise AST database schema translation & streaming migration. 100% UK GDPR compliant with zero customer records stored offsite.
            </p>
          </div>

          {/* Section Navigation Links */}
          <nav className="flex flex-wrap items-center justify-center gap-6 sm:gap-8 font-mono text-xs uppercase tracking-wider text-zinc-400">
            <a
              href="#overview"
              onClick={(e) => handleNavClick(e, 'overview')}
              className="hover:text-sky-400 transition-colors"
            >
              Architecture
            </a>
            <a
              href="#features"
              onClick={(e) => handleNavClick(e, 'features')}
              className="hover:text-sky-400 transition-colors"
            >
              Capabilities
            </a>
            <a
              href="#workflow"
              onClick={(e) => handleNavClick(e, 'workflow')}
              className="hover:text-sky-400 transition-colors"
            >
              Workflow
            </a>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3 w-full sm:w-auto justify-center">
            <Link
              href="/login"
              className="px-4 py-2 bg-zinc-950 hover:bg-zinc-900 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 text-xs font-mono font-semibold uppercase tracking-wider transition-colors rounded-none"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 bg-sky-400 hover:bg-sky-300 text-black text-xs font-mono font-bold uppercase tracking-wider transition-colors shadow-lg shadow-sky-950/40 rounded-none"
            >
              Register
            </Link>
          </div>
        </div>

        {/* Decorative Watermark: Visible only on larger screens to avoid mobile clutter */}
        <div className="hidden md:flex w-full my-10 items-center justify-center overflow-hidden pointer-events-none select-none opacity-40 hover:opacity-70 transition-opacity duration-500">
          <div className="flex items-center justify-center gap-6 w-full">
            <div className="w-24 h-24 border border-sky-400/40 flex items-center justify-center text-transparent text-5xl font-black font-mono shrink-0">
              <span className="[-webkit-text-stroke:1px_rgba(56,189,248,0.6)]">M</span>
            </div>
            <h2 className="text-[10vw] font-black uppercase tracking-tighter leading-none text-transparent [-webkit-text-stroke:1px_rgba(56,189,248,0.4)] whitespace-nowrap">
              Migraflow
            </h2>
          </div>
        </div>

        {/* Bottom Status & Legal Bar */}
        <div className="pt-8 border-t border-zinc-900 flex flex-col md:flex-row items-center justify-between gap-6 text-xs font-mono text-zinc-500">
          {/* Status & Compliance Badges */}
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/40 border border-emerald-800/40 text-emerald-400 text-[11px]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
              </span>
              <span className="tracking-wide">All systems operational</span>
            </div>

            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-sky-950/40 border border-sky-800/40 text-sky-400 text-[11px]">
              <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
              <span className="tracking-wide">UK GDPR Compliant</span>
            </div>
          </div>

          {/* Legal Links & Cookie Preferences */}
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-zinc-400">
            <Link href="/privacy" className="hover:text-sky-400 transition-colors">
              Privacy policy
            </Link>
            <span className="text-zinc-700 hidden sm:inline">•</span>
            <Link href="/terms" className="hover:text-sky-400 transition-colors">
              Terms of service
            </Link>
            <span className="text-zinc-700 hidden sm:inline">•</span>
            <button
              onClick={triggerOpenCookieSettings}
              className="hover:text-sky-400 transition-colors cursor-pointer text-center"
            >
              Cookie settings
            </button>
          </div>

          {/* Copyright */}
          <div className="text-zinc-500 text-center md:text-right text-[11px]">
            &copy; {new Date().getFullYear()} Migraflow. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
}
