import React from 'react';
import Link from 'next/link';
import { Shield, ArrowLeft, Lock, FileText, Database, Server, RefreshCw, AlertCircle } from 'lucide-react';

export const metadata = {
  title: 'Privacy Notice — Migraflow',
  description: 'UK GDPR and Data Protection Act 2018 Privacy Policy and Transparency Notice.',
};

export default function PrivacyPage() {
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
            <span className="text-[10px] font-mono uppercase bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 px-2 py-0.5 rounded-full">
              UK GDPR Notice
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <div className="mb-10 pb-8 border-b border-zinc-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                UK GDPR Privacy Notice
              </h1>
              <p className="text-xs sm:text-sm font-mono text-zinc-400 mt-1">
                Last updated: October 2026 &bull; Compliant with UK GDPR, Data Protection Act 2018 & PECR
              </p>
            </div>
          </div>
          <p className="text-sm text-zinc-300 leading-relaxed">
            This Privacy Notice explains how Migraflow Platform (&ldquo;Migraflow&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;, or &ldquo;our&rdquo;) processes and protects your personal data when you visit our website, register an account, or deploy our database migration agents.
          </p>
        </div>

        <div className="space-y-10 text-sm leading-relaxed text-zinc-300">
          {/* Section 1: Controller Identity */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">01.</span> Data Controller Information
            </h2>
            <p>
              The data controller responsible for personal data processed through Migraflow is:
            </p>
            <div className="p-4 rounded-xl bg-zinc-900/70 border border-zinc-800 font-mono text-xs space-y-1 text-zinc-300">
              <p className="font-semibold text-white">Migraflow Platform Ltd</p>
              <p>Privacy & Data Protection Office</p>
              <p>Email: <a href="mailto:privacy@migraflow.io" className="text-cyan-400 hover:underline">privacy@migraflow.io</a></p>
              <p>United Kingdom</p>
            </div>
          </section>

          {/* Section 2: Local Agent Architecture & Zero-Cloud Principle */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">02.</span> Local Architecture &amp; Zero-Cloud Data Principle
            </h2>
            <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/30 text-xs space-y-2">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold">
                <Database className="w-4 h-4" />
                <span>Your Customer &amp; Business Database Records Never Leave Your Network</span>
              </div>
              <p className="text-zinc-300 leading-relaxed">
                Migraflow operates an <strong>agent-centric architecture</strong>. When you execute an ETL database migration, the migration engine runs locally inside a Docker container within your private infrastructure. Customer database rows, credentials, and sensitive payload data stream directly between your source and target databases through DuckDB/Polars streaming.
                They are <strong>never transmitted to, stored in, or processed by Migraflow central cloud servers</strong>.
              </p>
            </div>
          </section>

          {/* Section 3: Data We Collect */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">03.</span> What Personal Data We Collect &amp; Why
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-zinc-800 rounded-lg overflow-hidden">
                <thead className="bg-zinc-900 text-zinc-200 uppercase font-mono">
                  <tr>
                    <th className="p-3 border-b border-zinc-800">Category</th>
                    <th className="p-3 border-b border-zinc-800">Data Fields</th>
                    <th className="p-3 border-b border-zinc-800">Lawful Basis (UK GDPR)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/80 text-zinc-300">
                  <tr>
                    <td className="p-3 font-semibold text-white">Account &amp; Auth</td>
                    <td className="p-3">Full Name, Email Address, Bcrypt Hashed Password, Google OAuth Subject ID</td>
                    <td className="p-3 font-mono text-cyan-400">Art. 6(1)(b) Contract</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-white">Agent Metadata</td>
                    <td className="p-3">Agent Name, OS/Architecture, Heartbeat timestamps, Schema metadata snapshots (table/column names only)</td>
                    <td className="p-3 font-mono text-cyan-400">Art. 6(1)(b) Contract</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-white">Migration Plans</td>
                    <td className="p-3">Plan titles, transformation expressions, execution job status, row counts</td>
                    <td className="p-3 font-mono text-cyan-400">Art. 6(1)(b) Contract</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-white">Security &amp; Logs</td>
                    <td className="p-3">Audit logs, masked email traces, IP addresses, rate-limiting tokens</td>
                    <td className="p-3 font-mono text-cyan-400">Art. 6(1)(f) Legitimate Interest</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-white">3D Visuals &amp; Analytics</td>
                    <td className="p-3">Interactive Spline 3D canvas assets, optional UI responsiveness telemetry</td>
                    <td className="p-3 font-mono text-cyan-400">Art. 6(1)(a) Consent (PECR)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Section 4: Sub-processors & AI Prompt Sanitization */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">04.</span> Third-Party Sub-Processors &amp; AI Minimization
            </h2>
            <p>
              We integrate with trusted third-party providers under strict data processing agreements:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-xs text-zinc-300">
              <li>
                <strong className="text-white">Google OAuth &amp; Gmail SMTP:</strong> Used for optional Google Single Sign-On and transactional security emails (such as 5-minute expiring password reset links).
              </li>
              <li>
                <strong className="text-white">AI Diagnosis Providers (Google Gemini / OpenAI):</strong> When an execution error occurs and AI diagnosis is triggered, our built-in <em>CredentialSanitizer</em> strips all database connection URIs, passwords, private keys, constraint values, and email addresses prior to prompt synthesis.
              </li>
              <li>
                <strong className="text-white">Spline CDN:</strong> Delivers 3D visual assets on the landing page only after you provide affirmative consent in our Cookie Consent Banner.
              </li>
            </ul>
          </section>

          {/* Section 5: Data Retention */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">05.</span> Storage Limitation &amp; Data Retention
            </h2>
            <p>
              In compliance with UK GDPR Article 5(1)(e), we enforce strict retention schedules:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-xs text-zinc-300">
              <li><strong>User Account Data:</strong> Retained while your account is active. Deleted immediately upon self-service account deletion.</li>
              <li><strong>Temporary Local Staging (DuckDB):</strong> Cleaned up automatically upon job completion, failure, or cancellation.</li>
              <li><strong>Access &amp; Refresh Tokens:</strong> Access tokens expire after 15 minutes; refresh tokens rotate and expire after 7 days.</li>
              <li><strong>Password Reset Tokens:</strong> Expire after 5 minutes in Redis and are deleted immediately upon single use.</li>
            </ul>
          </section>

          {/* Section 6: Your Data Subject Rights */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">06.</span> Your Data Subject Rights
            </h2>
            <p>
              Under Chapter III of the UK GDPR, you have comprehensive rights regarding your personal data:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <span className="font-semibold text-white block mb-1">Right to Access (Art. 15)</span>
                View your complete profile and migration plan metadata at any time in your dashboard.
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <span className="font-semibold text-white block mb-1">Right to Portability (Art. 20)</span>
                Download a machine-readable JSON archive of all your accounts, plans, and jobs via <Link href="/settings" className="text-cyan-400 hover:underline">Settings &gt; Data Export</Link>.
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <span className="font-semibold text-white block mb-1">Right to Erasure (Art. 17)</span>
                Permanently delete your account and all associated configuration directly via <Link href="/settings" className="text-cyan-400 hover:underline">Settings &gt; Delete Account</Link>.
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <span className="font-semibold text-white block mb-1">Right to Withdraw Consent</span>
                Revoke optional 3D visuals and analytics consent anytime using the <em>Cookie settings</em> link in the footer.
              </div>
            </div>
          </section>

          {/* Section 7: Supervisory Authority */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">07.</span> Lodging a Complaint with the ICO
            </h2>
            <p>
              If you have concerns about our processing of your personal data, we invite you to contact our Data Protection Office at{' '}
              <a href="mailto:privacy@migraflow.io" className="text-cyan-400 hover:underline">privacy@migraflow.io</a>.
            </p>
            <p>
              You also have the right to lodge a complaint with the UK supervisory authority:
            </p>
            <div className="p-4 rounded-xl bg-zinc-900/70 border border-zinc-800 font-mono text-xs text-zinc-300">
              <p className="font-semibold text-white">Information Commissioner&apos;s Office (ICO)</p>
              <p>Wycliffe House, Water Lane, Wilmslow, Cheshire, SK9 5AF</p>
              <p>Helpline: 0303 123 1113 &bull; Website: <a href="https://ico.org.uk" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">ico.org.uk</a></p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
