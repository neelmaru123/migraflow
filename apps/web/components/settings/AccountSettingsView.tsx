'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuthUser } from '@/hooks/queries/useAuthUser';
import authService from '@/services/authService';
import { triggerOpenCookieSettings } from '@/hooks/useCookieConsent';
import { useLogout } from '@/hooks/mutations/useAuthMutations';
import toast from 'react-hot-toast';
import {
  User,
  Download,
  Trash2,
  Lock,
  Mail,
  Sliders,
  AlertTriangle,
  ArrowLeft,
  Database,
  RefreshCw,
  LogOut,
} from 'lucide-react';

export const AccountSettingsView: React.FC = () => {
  const { data: currentUser, refetch: refetchUser } = useAuthUser();

  // Logout state & mutation
  const logoutMutation = useLogout();
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logoutMutation.mutateAsync();
    } catch {
      // Handled in mutation hook
    } finally {
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  };

  // Profile update state
  const [name, setName] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [updating, setUpdating] = useState<boolean>(false);

  // Sync state on user load
  React.useEffect(() => {
    if (currentUser?.name) {
      setName(currentUser.name);
    }
  }, [currentUser]);

  // Data export state
  const [exporting, setExporting] = useState<boolean>(false);

  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
  const [deleteConfirmationText, setDeleteConfirmationText] = useState<string>('');
  const [deleting, setDeleting] = useState<boolean>(false);

  // Handle Profile Update
  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error('Name cannot be empty.');
      return;
    }

    setUpdating(true);
    try {
      const payload: { name: string; password?: string } = { name: name.trim() };
      if (newPassword.trim()) {
        if (newPassword.length < 8 || newPassword.length > 128) {
          toast.error('Password must be between 8 and 128 characters.');
          setUpdating(false);
          return;
        }
        payload.password = newPassword;
      }
      await authService.updateMe(payload);
      toast.success('Profile updated successfully.');
      setNewPassword('');
      refetchUser();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setUpdating(false);
    }
  };

  // Handle Data Export
  const handleExportData = async () => {
    setExporting(true);
    try {
      await authService.downloadUserDataExport();
      toast.success('Your account data archive has been downloaded.');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to generate data export.');
    } finally {
      setExporting(false);
    }
  };

  // Handle Account Deletion
  const handleDeleteAccount = async () => {
    if (deleteConfirmationText !== 'DELETE') {
      toast.error('Please type DELETE to confirm.');
      return;
    }

    setDeleting(true);
    try {
      await authService.deleteMe();
      toast.success('Your account and associated data have been permanently erased.');
      if (typeof window !== 'undefined') {
        window.location.href = '/register';
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete account.');
      setDeleting(false);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight uppercase">
            Account &amp; Security Settings
          </h1>
          <p className="text-zinc-400 text-xs sm:text-sm font-mono mt-1">
            Manage your profile, credentials, and account data archive.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="py-1.5 px-3.5 rounded-xl bg-zinc-900 hover:bg-rose-950/40 text-zinc-300 hover:text-rose-400 text-xs font-mono font-bold uppercase tracking-wider border border-zinc-800 hover:border-rose-500/40 transition-colors flex items-center gap-2 disabled:opacity-50"
            title="Sign out of your session"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>{isLoggingOut ? 'Logging out...' : 'Logout'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Profile & Credentials (2 spans) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Profile Card */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-5 sm:p-6 shadow-xl">
            <div className="flex items-center gap-3 mb-5 pb-4 border-b border-zinc-800/80">
              <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Profile Information</h2>
                <p className="text-xs text-zinc-400">Update your account name and authentication password.</p>
              </div>
            </div>

            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-zinc-300 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    value={currentUser?.email || ''}
                    disabled
                    className="w-full pl-9 pr-3 py-2 bg-zinc-900/60 border border-zinc-800 rounded-xl text-xs text-zinc-400 font-mono cursor-not-allowed"
                  />
                </div>
                <p className="text-[11px] text-zinc-500 mt-1 font-mono">
                  Primary identifier associated with your account.
                </p>
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-300 uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your Name"
                  required
                  className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 focus:border-cyan-500 rounded-xl text-xs text-white placeholder-zinc-500 focus:outline-none transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-300 uppercase tracking-wider mb-1.5">
                  New Password <span className="text-zinc-500 lowercase">(leave blank to keep current)</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••••••"
                    minLength={8}
                    maxLength={128}
                    className="w-full pl-9 pr-3 py-2 bg-zinc-900 border border-zinc-800 focus:border-cyan-500 rounded-xl text-xs text-white placeholder-zinc-500 focus:outline-none transition-colors"
                  />
                </div>
                <p className="text-[11px] text-zinc-500 mt-1 font-mono">
                  Must be between 8 and 128 characters.
                </p>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={updating}
                  className="px-4 py-2 text-xs font-semibold rounded-xl bg-cyan-500 hover:bg-cyan-400 text-zinc-950 transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50 flex items-center gap-1.5"
                >
                  {updating ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <span>Save Changes</span>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Export Account Data */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-5 sm:p-6 shadow-xl">
            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-zinc-800/80">
              <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <Download className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Export Account Data</h2>
                <p className="text-xs text-zinc-400">Download a complete structured JSON archive of your account.</p>
              </div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed mb-4">
              Download a copy of your personal data in a structured JSON format. This export includes your profile details, registered migration agents, schema metadata snapshots, migration plans, and job history.
            </p>

            <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono text-zinc-300">migraflow_user_data_export.json</span>
              </div>
              <button
                onClick={handleExportData}
                disabled={exporting}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 transition-all shadow-md shadow-emerald-500/20 disabled:opacity-50 flex items-center gap-1.5"
              >
                {exporting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Exporting...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Archive</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Privacy, Cookies & Danger Zone */}
        <div className="space-y-6">
          {/* Cookie & Consent Settings */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-3 border-b border-zinc-800/80">
              <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
                <Sliders className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Cookie Preferences</h3>
                <p className="text-[11px] text-zinc-400">Manage site cookies</p>
              </div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              Control which optional cookies and third-party visual scripts (such as Spline 3D canvas) are active during your session.
            </p>

            <button
              onClick={triggerOpenCookieSettings}
              className="w-full py-2 px-3 rounded-xl border border-zinc-700 hover:bg-zinc-900 text-xs font-medium text-zinc-200 transition-colors flex items-center justify-center gap-2"
            >
              <Sliders className="w-3.5 h-3.5 text-sky-400" />
              <span>Modify Cookie Preferences</span>
            </button>

            <div className="pt-2 text-center">
              <Link href="/privacy" className="text-[11px] text-cyan-400 hover:underline">
                Read our full Privacy Notice &rarr;
              </Link>
            </div>
          </div>

          {/* Account Session & Logout */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-3 border-b border-zinc-800/80">
              <div className="p-2 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
                <LogOut className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Active Session</h3>
                <p className="text-[11px] text-zinc-400">Account authentication</p>
              </div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              Signed in as <span className="text-zinc-200 font-mono font-medium">{currentUser?.email}</span>. Terminate your current session and clear browser credentials.
            </p>

            <button
              type="button"
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="w-full py-2 px-3 rounded-xl bg-zinc-900 hover:bg-rose-950/40 border border-zinc-800 hover:border-rose-500/40 text-rose-400 hover:text-rose-300 text-xs font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>{isLoggingOut ? 'Signing out...' : 'Sign Out / Logout'}</span>
            </button>
          </div>

          {/* Danger Zone: Account Deletion */}
          <div className="bg-zinc-950 border border-red-500/30 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-3 border-b border-red-500/20">
              <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
                <Trash2 className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-red-400">Delete Account</h3>
                <p className="text-[11px] text-zinc-400">Permanently delete account</p>
              </div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              Permanently delete your account and all associated data. This action is irreversible and erases all registered agents, plans, and job history.
            </p>

            <button
              onClick={() => setShowDeleteModal(true)}
              className="w-full py-2 px-3 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/40 text-red-400 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete My Account</span>
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="max-w-md w-full bg-zinc-950 border border-red-500/40 rounded-2xl p-6 shadow-2xl text-zinc-200 space-y-4">
            <div className="flex items-center gap-3 text-red-400">
              <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-bold text-white">Permanently Delete Account?</h2>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              This action is <strong>irreversible</strong>. Your profile, authentication credentials, registered agents, and migration plans will be permanently removed immediately.
            </p>

            <div className="space-y-1.5">
              <label className="block text-[11px] font-mono text-zinc-400">
                Type <strong className="text-white">DELETE</strong> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmationText}
                onChange={(e) => setDeleteConfirmationText(e.target.value)}
                placeholder="DELETE"
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 focus:border-red-500 rounded-xl text-xs text-white placeholder-zinc-600 focus:outline-none font-mono"
              />
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteConfirmationText('');
                }}
                disabled={deleting}
                className="px-4 py-2 text-xs font-medium rounded-xl border border-zinc-700 hover:bg-zinc-900 text-zinc-300 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={deleting || deleteConfirmationText !== 'DELETE'}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-red-500 hover:bg-red-400 text-white transition-all shadow-md shadow-red-500/20 disabled:opacity-40 flex items-center gap-1.5"
              >
                {deleting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Confirm Deletion</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
