'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import Link from 'next/link';
import { useForgotPassword } from '../../hooks/mutations/useAuthMutations';
import { ForgotPasswordPayload } from '../../types/auth';
import { ArrowRight, ArrowLeft, Mail, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function ForgotPasswordForm() {
  const forgotPasswordMutation = useForgotPassword();
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [submittedEmail, setSubmittedEmail] = useState<string>('');
  const [cooldown, setCooldown] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldown <= 0) return;
    const interval = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [cooldown]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordPayload>({
    mode: 'onTouched',
  });

  const onSubmit = (data: ForgotPasswordPayload) => {
    setErrorMessage(null);
    forgotPasswordMutation.mutate(data, {
      onSuccess: () => {
        setIsSubmitted(true);
        setSubmittedEmail(data.email);
        setCooldown(60); // 1-minute cooldown
      },
      onError: (error: any) => {
        const detail = error?.response?.data?.detail || '';
        // Check if 429 rate limit error with remaining seconds
        const match = detail.match(/(\d+)\s*seconds/i);
        if (match && match[1]) {
          const seconds = parseInt(match[1], 10);
          setCooldown(seconds);
        }
        setErrorMessage(detail || 'Failed to request password reset link. Please try again.');
      },
    });
  };

  return (
    <div className="space-y-4">
      {errorMessage && (
        <div className="p-3 bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed font-sans">{errorMessage}</div>
        </div>
      )}

      {isSubmitted ? (
        <div className="space-y-4">
          {/* Success Banner */}
          <div className="p-4 bg-sky-950/40 border border-sky-400/40 text-sky-200 text-xs space-y-2">
            <div className="flex items-center gap-2 font-bold text-sky-400 uppercase tracking-wider text-[11px]">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Reset Link Dispatched</span>
            </div>
            <p className="text-zinc-300 leading-relaxed font-sans">
              A password reset link has been dispatched to <strong className="text-white">{submittedEmail}</strong>. Please check your inbox and spam folder.
            </p>
            <div className="flex items-center gap-1.5 pt-1 text-[11px] font-mono text-amber-400">
              <Clock className="w-3.5 h-3.5" />
              <span>Link expires in exactly 5 minutes</span>
            </div>
          </div>

          <div className="pt-2 space-y-3">
            <button
              onClick={() => {
                if (cooldown === 0) {
                  onSubmit({ email: submittedEmail });
                }
              }}
              disabled={cooldown > 0 || forgotPasswordMutation.isPending}
              className="w-full py-2.5 px-4 rounded-none bg-sky-400/10 hover:bg-sky-400/20 border border-sky-400/40 text-sky-300 text-xs font-mono uppercase tracking-wider transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {cooldown > 0 ? (
                <>
                  <Clock className="w-3.5 h-3.5 animate-spin" />
                  <span>Resend available in {cooldown}s</span>
                </>
              ) : (
                <span>Resend Reset Email</span>
              )}
            </button>

            <Link
              href="/login"
              className="w-full py-2.5 px-4 rounded-none bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-semibold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 border border-zinc-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Sign In</span>
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <p className="text-xs text-zinc-400 leading-relaxed">
            Enter the email address associated with your Migraflow account and we will send you a secure link to reset your password.
          </p>

          {/* Email Field */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-300 mb-1">
              Registered Email
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-sky-400">
                <Mail className="w-3.5 h-3.5" />
              </div>
              <input
                type="email"
                placeholder="user@example.com"
                {...register('email', {
                  required: 'Email address is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Please enter a valid email address',
                  },
                })}
                className={`w-full pl-9 pr-3 py-2 bg-sky-400/[0.04] backdrop-blur-md border ${
                  errors.email ? 'border-red-500' : 'border-sky-400/30 focus:border-sky-400'
                } rounded-none text-xs text-white placeholder-zinc-500 focus:outline-none transition-colors font-sans`}
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-[11px] text-red-400 font-mono">{errors.email.message}</p>
            )}
          </div>

          {/* 5-Min Expiry & 1-Min Cooldown Notice */}
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-400 pt-1">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            <span>Reset links expire in 5 min &bull; 1-min retry cooldown</span>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={forgotPasswordMutation.isPending || cooldown > 0}
            className="w-full py-2.5 px-4 rounded-none bg-sky-400 hover:bg-sky-300 text-black text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 shadow-lg shadow-sky-950/50 disabled:opacity-50 mt-4"
          >
            {cooldown > 0 ? (
              <span>Wait {cooldown}s to Retry</span>
            ) : (
              <>
                <span>{forgotPasswordMutation.isPending ? 'Sending Link...' : 'Send Reset Link'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          {/* Return to Sign In */}
          <div className="text-center pt-2">
            <p className="text-xs text-zinc-400">
              Remember your password?{' '}
              <Link href="/login" className="text-sky-400 hover:text-sky-300 font-semibold underline underline-offset-4">
                Sign In
              </Link>
            </p>
          </div>
        </form>
      )}
    </div>
  );
}
