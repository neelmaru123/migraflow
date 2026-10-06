'use client';

import { useState, useEffect, useCallback } from 'react';

export interface CookiePreferences {
  necessary: boolean;
  visuals_3d: boolean;
  analytics: boolean;
  decidedAt?: string;
}

const STORAGE_KEY = 'migraflow_cookie_consent';
const EVENT_NAME = 'migraflow-cookie-consent-updated';
const OPEN_MODAL_EVENT = 'migraflow-open-cookie-settings';

const DEFAULT_PREFERENCES: CookiePreferences = {
  necessary: true,
  visuals_3d: false,
  analytics: false,
};

export function useCookieConsent() {
  const [preferences, setPreferences] = useState<CookiePreferences>(DEFAULT_PREFERENCES);
  const [hasDecided, setHasDecided] = useState<boolean>(true); // default true to avoid flash on server render
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Load from localStorage on client mount
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const readFromStorage = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          setPreferences({
            necessary: true,
            visuals_3d: !!parsed.visuals_3d,
            analytics: !!parsed.analytics,
            decidedAt: parsed.decidedAt,
          });
          setHasDecided(true);
        } else {
          setHasDecided(false);
        }
      } catch {
        setHasDecided(false);
      }
    };

    readFromStorage();

    const handleUpdate = () => readFromStorage();
    const handleOpenModal = () => setIsSettingsOpen(true);

    window.addEventListener(EVENT_NAME, handleUpdate);
    window.addEventListener(OPEN_MODAL_EVENT, handleOpenModal);

    return () => {
      window.removeEventListener(EVENT_NAME, handleUpdate);
      window.removeEventListener(OPEN_MODAL_EVENT, handleOpenModal);
    };
  }, []);

  const savePreferences = useCallback((newPrefs: Partial<CookiePreferences>) => {
    if (typeof window === 'undefined') return;

    const finalPrefs: CookiePreferences = {
      necessary: true,
      visuals_3d: !!newPrefs.visuals_3d,
      analytics: !!newPrefs.analytics,
      decidedAt: new Date().toISOString(),
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(finalPrefs));
    setPreferences(finalPrefs);
    setHasDecided(true);
    setIsSettingsOpen(false);

    window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: finalPrefs }));
  }, []);

  const acceptAll = useCallback(() => {
    savePreferences({
      necessary: true,
      visuals_3d: true,
      analytics: true,
    });
  }, [savePreferences]);

  const rejectOptional = useCallback(() => {
    savePreferences({
      necessary: true,
      visuals_3d: false,
      analytics: false,
    });
  }, [savePreferences]);

  const openSettings = useCallback(() => {
    setIsSettingsOpen(true);
  }, []);

  const closeSettings = useCallback(() => {
    setIsSettingsOpen(false);
  }, []);

  return {
    preferences,
    hasDecided,
    isSettingsOpen,
    acceptAll,
    rejectOptional,
    savePreferences,
    openSettings,
    closeSettings,
  };
}

export function triggerOpenCookieSettings() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(OPEN_MODAL_EVENT));
  }
}
