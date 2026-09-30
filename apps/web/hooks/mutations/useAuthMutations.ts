import { useMutation, useQueryClient } from '@tanstack/react-query';
import Cookies from 'js-cookie';
import authService from '../../services/authService';
import {
  UserRegisterPayload,
  UserLoginPayload,
  GoogleAuthRequestPayload,
  UserUpdatePayload,
  ForgotPasswordPayload,
  ResetPasswordPayload,
  TokenResponse,
  MessageResponse,
  UserResponse,
} from '../../types/auth';
import { AUTH_USER_QUERY_KEY } from '../queries/useAuthUser';
import { useAppDispatch } from '../../store';
import { setUser, logout as logoutAction } from '../../store/slices/authSlice';
import toast from 'react-hot-toast';

/**
 * Register mutation hook (POST /auth/register)
 */
export function useRegister() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<TokenResponse, any, UserRegisterPayload>({
    mutationFn: (payload) => authService.register(payload),
    onSuccess: (data) => {
      Cookies.set('logged_in', 'true', { expires: 7, path: '/' });
      dispatch(setUser(data.user));
      queryClient.invalidateQueries({ queryKey: AUTH_USER_QUERY_KEY });
      toast.success(data.message || 'Account created successfully!');
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || error?.message || 'Registration failed';
      toast.error(message);
    },
  });
}

/**
 * Login mutation hook (POST /auth/login)
 */
export function useLogin() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<TokenResponse, any, UserLoginPayload>({
    mutationFn: (payload) => authService.login(payload),
    onSuccess: (data) => {
      Cookies.set('logged_in', 'true', { expires: 7, path: '/' });
      dispatch(setUser(data.user));
      queryClient.invalidateQueries({ queryKey: AUTH_USER_QUERY_KEY });
      toast.success(data.message || 'Login successful!');
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || error?.message || 'Login failed';
      toast.error(message);
    },
  });
}

/**
 * Google Auth mutation hook (POST /auth/google)
 */
export function useGoogleAuth() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<TokenResponse, any, GoogleAuthRequestPayload>({
    mutationFn: (payload) => authService.googleAuth(payload),
    onSuccess: (data) => {
      Cookies.set('logged_in', 'true', { expires: 7, path: '/' });
      dispatch(setUser(data.user));
      queryClient.invalidateQueries({ queryKey: AUTH_USER_QUERY_KEY });
      toast.success(data.message || 'Google authentication successful!');
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || error?.message || 'Google authentication failed';
      toast.error(message);
    },
  });
}

/**
 * Logout mutation hook (POST /auth/logout)
 */
export function useLogout() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<MessageResponse, any, void>({
    mutationFn: () => authService.logout(),
    onSuccess: (data) => {
      Cookies.remove('logged_in', { path: '/' });
      Cookies.remove('active_org_id', { path: '/' });
      dispatch(logoutAction());
      queryClient.clear();
      toast.success(data.message || 'Logged out successfully');
    },
    onError: (error) => {
      Cookies.remove('logged_in', { path: '/' });
      Cookies.remove('active_org_id', { path: '/' });
      dispatch(logoutAction());
      queryClient.clear();
      const message = error?.response?.data?.detail || error?.message || 'Logged out';
      toast.success(message);
    },
  });
}

/**
 * Update Profile mutation hook (PUT /users/me)
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation<UserResponse, any, UserUpdatePayload>({
    mutationFn: (payload) => authService.updateMe(payload),
    onSuccess: (updatedUser) => {
      dispatch(setUser(updatedUser));
      queryClient.setQueryData(AUTH_USER_QUERY_KEY, updatedUser);
      toast.success('Profile updated successfully!');
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || error?.message || 'Profile update failed';
      toast.error(message);
    },
  });
}

/**
 * Forgot Password mutation hook (POST /auth/forgot-password)
 */
export function useForgotPassword() {
  return useMutation<MessageResponse, any, ForgotPasswordPayload>({
    mutationFn: (payload) => authService.forgotPassword(payload),
    onSuccess: (data) => {
      toast.success(data.message || 'Password reset link sent!');
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || error?.message || 'Failed to send reset link';
      toast.error(message);
    },
  });
}

/**
 * Reset Password mutation hook (POST /auth/reset-password)
 */
export function useResetPassword() {
  return useMutation<MessageResponse, any, ResetPasswordPayload>({
    mutationFn: (payload) => authService.resetPassword(payload),
    onSuccess: (data) => {
      toast.success(data.message || 'Password reset successfully!');
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || error?.message || 'Password reset failed';
      toast.error(message);
    },
  });
}

