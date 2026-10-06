'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useCookieConsent } from '@/hooks/useCookieConsent';
import { Shield, Settings2, Check, X, ChevronDown, ChevronUp } from 'lucide-react';

export const CookieConsentBanner: React.FC = () => {
  const {
    preferences,
    hasDecided,
    isSettingsOpen,
    acceptAll,
    rejectOptional,
    savePreferences,
    openSettings,
    closeSettings,
  } = useCookieConsent();

  const [expanded, setExpanded] = useState<boolean>(false);
  const [customVisuals3D, setCustomVisuals3D] = useState<boolean>(preferences.visuals_3d);
  const [customAnalytics, setCustomAnalytics] = useState<boolean>(preferences.analytics);

  // Sync state when preferences change
  React.useEffect(() => {
    setCustomVisuals3D(preferences.visuals_3d);
    setCustomAnalytics(preferences.analytics);
  }, [preferences]);

  // Don't render anything if user already decided and modal is not opened
  if (hasDecided && !isSettingsOpen) {
    return null;
  }

  const handleSaveCustom = () => {
    savePreferences({
      necessary: true,
      visuals_3d: customVisuals3D,
      analytics: customAnalytics,
    });
  };

  return (
    <aside
      role="region"
      aria-label="Cookie consent banner"
      className="fixed bottom-0 inset-x-0 z-50 p-4 sm:p-6 pointer-events-none"
    >
      <div className="max-w-4xl mx-auto pointer-events-auto bg-zinc-950/95 border border-zinc-800 backdrop-blur-xl rounded-2xl shadow-2xl p-5 sm:p-6 text-zinc-200 animate-in fade-in slide-in-from-bottom-5 duration-300">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-3 border-b border-zinc-800/80">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-semibold text-white tracking-tight">
                Privacy & Cookie Preferences
              </h2>
              <p className="text-xs text-zinc-400">
                UK GDPR & PECR Compliant Data Protection
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end md:self-auto">
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-zinc-400 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-800 hover:bg-zinc-900 transition-colors"
            >
              <Settings2 className="w-3.5 h-3.5 text-zinc-400" />
              <span>{expanded ? 'Hide Categories' : 'Customize'}</span>
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            {isSettingsOpen && (
              <button
                onClick={closeSettings}
                className="p-1.5 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-900 transition-colors"
                title="Close settings"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <p className="text-xs sm:text-sm text-zinc-300 mt-3 leading-relaxed">
          We use strictly necessary cookies to keep you signed in securely and store your session tokens in HTTP-only cookies.
          With your consent, we also load interactive 3D WebGL visualizations (Spline) and non-invasive telemetry to improve your migration workflow.
          Read our{' '}
          <Link href="/privacy" className="text-cyan-400 hover:underline underline-offset-2">
            Privacy Policy
          </Link>{' '}
          and{' '}
          <Link href="/terms" className="text-cyan-400 hover:underline underline-offset-2">
            Terms of Service
          </Link>{' '}
          for full details.
        </p>

        {/* Detailed Category Settings (Accordion) */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-zinc-800/80 space-y-3 animate-in fade-in duration-200">
            {/* Strictly Necessary */}
            <div className="flex items-start justify-between p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <div className="pr-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-white">Strictly Necessary</span>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
                    Always Active
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Required for user authentication, CSRF security, HTTP-only JWT cookies, and core API communication.
                </p>
              </div>
              <input
                type="checkbox"
                checked={true}
                disabled
                className="mt-1 w-4 h-4 accent-cyan-500 cursor-not-allowed opacity-70"
              />
            </div>

            {/* Interactive 3D Visuals (Spline) */}
            <div className="flex items-start justify-between p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <div className="pr-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-white">Interactive 3D Visualizations</span>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
                    Optional
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Loads external WebGL 3D models via Spline CDN to render interactive graphics on the landing page.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer mt-1">
                <input
                  type="checkbox"
                  checked={customVisuals3D}
                  onChange={(e) => setCustomVisuals3D(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>

            {/* Analytics & Diagnostics */}
            <div className="flex items-start justify-between p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <div className="pr-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-white">Performance & Anonymous Telemetry</span>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
                    Optional
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Aggregated, non-personal metrics on UI responsiveness and error rates to help us maintain system reliability.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer mt-1">
                <input
                  type="checkbox"
                  checked={customAnalytics}
                  onChange={(e) => setCustomAnalytics(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-4 pt-3 flex flex-wrap items-center justify-end gap-2.5">
          {expanded ? (
            <button
              onClick={handleSaveCustom}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-cyan-500 hover:bg-cyan-400 text-zinc-950 transition-all shadow-md shadow-cyan-500/20 flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              Save My Choices
            </button>
          ) : (
            <>
              <button
                onClick={rejectOptional}
                className="px-3.5 py-2 text-xs font-medium rounded-xl border border-zinc-700/80 hover:bg-zinc-900 text-zinc-300 hover:text-white transition-all"
              >
                Reject Optional
              </button>
              <button
                onClick={acceptAll}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-cyan-500 hover:bg-cyan-400 text-zinc-950 transition-all shadow-md shadow-cyan-500/20"
              >
                Accept All
              </button>
            </>
          )}
        </div>
      </div>
    </aside>
  );
};
