import React from 'react';
import Link from 'next/link';
import { FileText, ArrowLeft, CheckCircle2, ShieldCheck, Scale, AlertTriangle } from 'lucide-react';

export const metadata = {
  title: 'Terms of Service — Migraflow',
  description: 'Terms of Service and Customer Agreement for Migraflow Platform.',
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-black text-zinc-200 font-sans selection:bg-cyan-500/20 selection:text-cyan-400">
      {/* Header Bar */}
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-xs font-mono text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Migraflow</span>
          </Link>
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-white uppercase tracking-tight">
              Migra<span className="text-cyan-400">flow</span>
            </span>
            <span className="text-[10px] font-mono uppercase bg-zinc-800 text-zinc-300 border border-zinc-700 px-2 py-0.5 rounded-full">
              Legal Terms
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <div className="mb-10 pb-8 border-b border-zinc-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Terms of Service
              </h1>
              <p className="text-xs sm:text-sm font-mono text-zinc-400 mt-1">
                Effective: October 2026 &bull; Governing Law: England &amp; Wales
              </p>
            </div>
          </div>
          <p className="text-sm text-zinc-300 leading-relaxed">
            Please read these Terms of Service carefully before creating an account or deploying Migraflow migration agents. By accessing or using the platform, you agree to be bound by these terms.
          </p>
        </div>

        <div className="space-y-10 text-sm leading-relaxed text-zinc-300">
          {/* Section 1: Overview */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">01.</span> Service Scope &amp; Architecture
            </h2>
            <p>
              Migraflow provides an automated schema discovery, AI-assisted migration planning, and local agent execution control plane. 
              The actual data transformation and streaming occurs locally on your host environment via the Migraflow Docker Agent.
            </p>
          </section>

          {/* Section 2: Account Responsibilities */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">02.</span> User Accounts &amp; Security
            </h2>
            <p>
              You are responsible for safeguarding your login credentials and agent registration tokens. You must notify us immediately if you suspect unauthorized access to your account.
            </p>
            <ul className="list-disc pl-5 space-y-1 text-xs text-zinc-300">
              <li>Passwords must be at least 8 characters long (supports up to 128 characters).</li>
              <li>Agent registration tokens must be treated as confidential operational secrets.</li>
            </ul>
          </section>

          {/* Section 3: Data Safety & Backups */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">03.</span> Database Safety &amp; Backup Obligations
            </h2>
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs space-y-2 text-zinc-300">
              <div className="flex items-center gap-2 text-amber-400 font-semibold">
                <AlertTriangle className="w-4 h-4" />
                <span>Mandatory Pre-Migration Database Backups</span>
              </div>
              <p className="leading-relaxed">
                While Migraflow provides dry runs, schema verification checkpoints, and atomic batch staging, database migrations inherently interact with live storage. You agree to create a full, verified backup of all source and target databases prior to initiating any production migration run.
              </p>
            </div>
          </section>

          {/* Section 4: Privacy & GDPR */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">04.</span> Data Protection &amp; UK GDPR Compliance
            </h2>
            <p>
              Both parties agree to comply with all applicable data protection legislation, including the UK GDPR and the Data Protection Act 2018. For complete details on how account information is handled, please review our{' '}
              <Link href="/privacy" className="text-cyan-400 hover:underline">
                Privacy Notice
              </Link>.
            </p>
          </section>

          {/* Section 5: Governing Law */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">05.</span> Governing Law &amp; Jurisdiction
            </h2>
            <p>
              These Terms and any dispute or claim arising out of or in connection with them shall be governed by and construed in accordance with the laws of England and Wales.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
