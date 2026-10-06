'use client';

import React, { useState, useEffect } from 'react';
import Script from 'next/script';
import { useCookieConsent, triggerOpenCookieSettings } from '@/hooks/useCookieConsent';
import { Sparkles, Eye } from 'lucide-react';

interface SplineHeroBackgroundProps {
  sceneUrl?: string;
  interactive?: boolean;
}

const DEFAULT_SPLINE_URL = 'https://prod.spline.design/E6eFCzHp4BkxYnO7/scene.splinecode';

export default function SplineHeroBackground({
  sceneUrl,
  interactive = false,
}: SplineHeroBackgroundProps) {
  const [hasError, setHasError] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const { preferences, savePreferences } = useCookieConsent();

  const activeUrl =
    sceneUrl && sceneUrl !== 'undefined' ? sceneUrl : DEFAULT_SPLINE_URL;

  const isIframeUrl = activeUrl.includes('my.spline.design');
  const is3DEnabled = preferences.visuals_3d;

  // Viewport detection: Only activate 3D on full laptop and desktop screens (>= 1280px)
  useEffect(() => {
    const checkDesktop = () => {
      setIsDesktop(typeof window !== 'undefined' && window.innerWidth >= 1280);
    };
    checkDesktop();
    window.addEventListener('resize', checkDesktop);
    return () => window.removeEventListener('resize', checkDesktop);
  }, []);

  // Intercept spline-viewer async fetch errors & unhandled rejections
  useEffect(() => {
    const handleGlobalError = (event: ErrorEvent) => {
      if (
        event.message?.includes('Failed to fetch') ||
        event.filename?.includes('spline-viewer')
      ) {
        setHasError(true);
      }
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reasonStr = String(event.reason?.message || event.reason || '');
      if (reasonStr.includes('Failed to fetch') || reasonStr.includes('spline')) {
        event.preventDefault(); // Intercepts error overlay in Next.js dev mode
        setHasError(true);
      }
    };

    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleGlobalError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  return (
    <div className="relative w-full h-screen overflow-hidden select-none bg-black">
      {/* UK GDPR / PECR: Only load external Spline script and iframe if user has given consent AND on desktop */}
      {isDesktop && is3DEnabled && !isIframeUrl && (
        <Script
          src="https://unpkg.com/@splinetool/viewer@1.12.98/build/spline-viewer.js"
          type="module"
          strategy="afterInteractive"
          onError={() => setHasError(true)}
        />
      )}

      {isDesktop && is3DEnabled && !hasError ? (
        <div className={`w-full h-full ${interactive ? 'pointer-events-auto' : 'pointer-events-none'}`}>
          {isIframeUrl ? (
            <iframe
              src={activeUrl}
              className="w-full h-full border-0"
              style={{ pointerEvents: interactive ? 'auto' : 'none' }}
              title="Spline 3D Auth Scene"
            />
          ) : (
            React.createElement('spline-viewer', {
              url: activeUrl,
              'loading-anim-type': 'spinner',
              style: {
                width: '100%',
                height: '100%',
                pointerEvents: interactive ? 'auto' : 'none',
              },
            })
          )}
        </div>
      ) : !isDesktop ? (
        <div className="w-full h-full bg-black" />
      ) : (
        /* High-performance, Privacy-compliant Dark Gradient Mesh Fallback */
        <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center bg-black relative">
          {/* Subtle Ambient Radial Gradients */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(6,182,212,0.08),transparent_60%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(14,165,233,0.05),transparent_50%)]" />
          
          <div className="relative z-10 flex flex-col items-center">
            <div className="w-16 h-16 rounded-2xl bg-zinc-900/90 border border-zinc-800 flex items-center justify-center text-cyan-400 font-mono font-bold text-xl mb-4 shadow-xl shadow-cyan-950/20">
              <Sparkles className="w-7 h-7 text-cyan-400 animate-pulse" />
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight mb-2">
              Autonomous Database Schema Migration Platform
            </h3>
            <p className="text-xs font-mono text-zinc-400 max-w-sm mb-6 leading-relaxed">
              High-Performance Database Schema Discovery & Streaming Data Migration
            </p>

            {!is3DEnabled && (
              <div className="flex flex-col items-center gap-2">
                <button
                  onClick={() => savePreferences({ visuals_3d: true })}
                  className="px-4 py-2 text-xs font-medium rounded-xl bg-zinc-900/90 hover:bg-zinc-800 border border-zinc-700/80 text-zinc-300 hover:text-white flex items-center gap-2 transition-all shadow-sm"
                >
                  <Eye className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Enable Interactive 3D Visuals</span>
                </button>
                <button
                  onClick={triggerOpenCookieSettings}
                  className="text-[11px] text-zinc-500 hover:text-zinc-400 underline underline-offset-2"
                >
                  Cookie Preferences
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
