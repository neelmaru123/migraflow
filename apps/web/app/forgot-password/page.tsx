import React, { Suspense } from 'react';
import AuthLayout from '../../components/auth/AuthLayout';
import ForgotPasswordForm from '../../components/auth/ForgotPasswordForm';

export const metadata = {
  title: 'Forgot Password | Migraflow Platform',
  description: 'Request a secure password reset link for your Migraflow account',
};

const AUTH_SPLINE_URL = 'https://my.spline.design/flow-vD4AAB4End71ev0QfMLT00qI/';

export default function ForgotPasswordPage() {
  return (
    <AuthLayout
      title="Reset Password"
      subtitle="Enter your verified email to receive a secure password reset link valid for 5 minutes."
      sceneUrl={AUTH_SPLINE_URL}
    >
      <Suspense fallback={<div className="text-zinc-500 text-xs py-4 text-center">Loading password reset...</div>}>
        <ForgotPasswordForm />
      </Suspense>
    </AuthLayout>
  );
}
