import React, { Suspense } from 'react';
import AuthLayout from '../../components/auth/AuthLayout';
import ResetPasswordForm from '../../components/auth/ResetPasswordForm';

export const metadata = {
  title: 'Reset Password | Migraflow Platform',
  description: 'Choose a new password for your Migraflow account',
};

const AUTH_SPLINE_URL = 'https://my.spline.design/flow-vD4AAB4End71ev0QfMLT00qI/';

export default function ResetPasswordPage() {
  return (
    <AuthLayout
      title="Create New Password"
      subtitle="Enter a new password for your account. Once updated, your old password will be invalidated immediately."
      sceneUrl={AUTH_SPLINE_URL}
    >
      <Suspense fallback={<div className="text-zinc-500 text-xs py-4 text-center">Loading password reset form...</div>}>
        <ResetPasswordForm />
      </Suspense>
    </AuthLayout>
  );
}
