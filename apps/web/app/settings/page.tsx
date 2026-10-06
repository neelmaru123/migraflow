import React from 'react';
import { AccountSettingsView } from '@/components/settings/AccountSettingsView';

export const metadata = {
  title: 'Account Settings — Migraflow',
  description: 'Manage account profile, credentials, and data export.',
};

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-black text-slate-100 flex flex-col justify-between selection:bg-cyan-500/20 selection:text-cyan-400 font-sans">
      {/* Background Ambient Glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-cyan-500/10 via-sky-500/5 to-transparent blur-3xl pointer-events-none -z-10" />

      <main className="flex-1">
        <AccountSettingsView />
      </main>
    </div>
  );
}
