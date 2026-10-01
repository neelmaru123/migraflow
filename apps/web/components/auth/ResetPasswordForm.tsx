'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useResetPassword } from '../../hooks/mutations/useAuthMutations';
import { ArrowRight, Lock, Eye, EyeOff, CheckCircle2, AlertTriangle, ArrowLeft } from 'lucide-react';

interface ResetPasswordFormData {
  new_password: string;
  confirm_password: string;
}

export default function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const resetPasswordMutation = useResetPassword();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    mode: 'onTouched',
  });

  const newPasswordValue = watch('new_password');

  if (!token) {
    return (
      <div className="space-y-4">
        <div className="p-4 bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs space-y-2">
          <div className="flex items-center gap-2 font-bold text-amber-400 uppercase tracking-wider text-[11px]">
            <AlertTriangle className="w-4 h-4" />
            <span>Missing Reset Token</span>
          </div>
          <p className="text-zinc-300 leading-relaxed font-sans">
            No valid password reset token was provided in the URL. Please ensure you clicked the complete link from your reset email.
          </p>
        </div>

        <Link
          href="/forgot-password"
          className="w-full py-2.5 px-4 rounded-none bg-sky-400 hover:bg-sky-300 text-black text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 shadow-lg shadow-sky-950/50"
        >
          <span>Request New Reset Link</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  const onSubmit = (data: ResetPasswordFormData) => {
    setErrorMessage(null);
    resetPasswordMutation.mutate(
      {
        token,
        new_password: data.new_password,
      },
      {
        onSuccess: () => {
          setIsSuccess(true);
          setTimeout(() => {
            router.push('/login');
          }, 2500);
        },
        onError: (error: any) => {
          const detail = error?.response?.data?.detail || 'Failed to reset password. The link may have expired.';
          setErrorMessage(detail);
        },
      }
    );
  };

  if (isSuccess) {
    return (
      <div className="space-y-4">
        <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 text-emerald-200 text-xs space-y-2">
          <div className="flex items-center gap-2 font-bold text-emerald-400 uppercase tracking-wider text-[11px]">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Password Updated Successfully</span>
          </div>
          <p className="text-zinc-300 leading-relaxed font-sans">
            Your new password has been securely encrypted and updated in the database. Redirecting you to sign in...
          </p>
        </div>

        <Link
          href="/login"
          className="w-full py-2.5 px-4 rounded-none bg-sky-400 hover:bg-sky-300 text-black text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 shadow-lg shadow-sky-950/50"
        >
          <span>Sign In With New Password</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {errorMessage && (
        <div className="p-3 bg-red-950/40 border border-red-500/40 text-red-300 text-xs space-y-2">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="leading-relaxed font-sans">{errorMessage}</div>
          </div>
          <div className="pt-1">
            <Link
              href="/forgot-password"
              className="text-[11px] font-mono text-sky-400 hover:text-sky-300 underline underline-offset-4"
            >
              Request a new 5-minute link &rarr;
            </Link>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* New Password Field */}
        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-300 mb-1">
            New Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-sky-400">
              <Lock className="w-3.5 h-3.5" />
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Min. 8 characters"
              {...register('new_password', {
                required: 'New password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters',
                },
              })}
              className={`w-full pl-9 pr-10 py-2 bg-sky-400/[0.04] backdrop-blur-md border ${
                errors.new_password ? 'border-red-500' : 'border-sky-400/30 focus:border-sky-400'
              } rounded-none text-xs text-white placeholder-zinc-500 focus:outline-none transition-colors font-sans`}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-400 hover:text-white"
            >
              {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
          {errors.new_password && (
            <p className="mt-1 text-[11px] text-red-400 font-mono">{errors.new_password.message}</p>
          )}
        </div>

        {/* Confirm Password Field */}
        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-300 mb-1">
            Confirm New Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-sky-400">
              <Lock className="w-3.5 h-3.5" />
            </div>
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Repeat your new password"
              {...register('confirm_password', {
                required: 'Please confirm your password',
                validate: (value) => value === newPasswordValue || 'Passwords do not match',
              })}
              className={`w-full pl-9 pr-10 py-2 bg-sky-400/[0.04] backdrop-blur-md border ${
                errors.confirm_password ? 'border-red-500' : 'border-sky-400/30 focus:border-sky-400'
              } rounded-none text-xs text-white placeholder-zinc-500 focus:outline-none transition-colors font-sans`}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-400 hover:text-white"
            >
              {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
          {errors.confirm_password && (
            <p className="mt-1 text-[11px] text-red-400 font-mono">{errors.confirm_password.message}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={resetPasswordMutation.isPending}
          className="w-full py-2.5 px-4 rounded-none bg-sky-400 hover:bg-sky-300 text-black text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 shadow-lg shadow-sky-950/50 disabled:opacity-50 mt-4"
        >
          <span>{resetPasswordMutation.isPending ? 'Updating Password...' : 'Save New Password'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        <div className="text-center pt-2">
          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Cancel and return to Sign In</span>
          </Link>
        </div>
      </form>
    </div>
  );
}
