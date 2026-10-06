import apiClient from './axios';
import {
  UserRegisterPayload,
  UserLoginPayload,
  GoogleAuthRequestPayload,
  UserUpdatePayload,
  UserResponse,
  TokenResponse,
  MessageResponse,
  GoogleLoginUrlResponse,
  ForgotPasswordPayload,
  ResetPasswordPayload,
} from '../types/auth';

export const authService = {
  /**
   * Request password reset link (POST /auth/forgot-password)
   */
  async forgotPassword(payload: ForgotPasswordPayload): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/auth/forgot-password', payload);
    return response.data;
  },

  /**
   * Reset password using token (POST /auth/reset-password)
   */
  async resetPassword(payload: ResetPasswordPayload): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/auth/reset-password', payload);
    return response.data;
  },

  /**
   * Register a new user account (POST /auth/register)
   */
  async register(payload: UserRegisterPayload): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/register', payload);
    return response.data;
  },

  /**
   * Login user with email & password (POST /auth/login)
   */
  async login(payload: UserLoginPayload): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', payload);
    return response.data;
  },

  /**
   * Authenticate via Google OAuth ID Token (POST /auth/google)
   */
  async googleAuth(payload: GoogleAuthRequestPayload): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/google', payload);
    return response.data;
  },

  /**
   * Get Google OAuth consent URL (GET /auth/google/login)
   */
  async getGoogleLoginUrl(): Promise<GoogleLoginUrlResponse> {
    const response = await apiClient.get<GoogleLoginUrlResponse>('/auth/google/login');
    return response.data;
  },

  /**
   * Trigger token refresh rotation via HTTP-only cookie (POST /auth/refresh)
   */
  async refreshToken(): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/refresh');
    return response.data;
  },

  /**
   * Logout user and clear HTTP-only cookies (POST /auth/logout)
   */
  async logout(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/auth/logout');
    return response.data;
  },

  /**
   * Get current authenticated user profile (GET /users/me)
   */
  async getMe(): Promise<UserResponse> {
    const response = await apiClient.get<UserResponse>('/users/me');
    return response.data;
  },

  /**
   * Update profile details for authenticated user (PUT /users/me)
   */
  async updateMe(payload: UserUpdatePayload): Promise<UserResponse> {
    const response = await apiClient.put<UserResponse>('/users/me', payload);
    return response.data;
  },

  /**
   * Delete current logged-in user account (DELETE /users/me)
   */
  async deleteMe(): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>('/users/me');
    return response.data;
  },

  /**
   * Export all user data as JSON (GET /users/me/export)
   */
  async exportUserData(): Promise<any> {
    const response = await apiClient.get('/users/me/export');
    return response.data;
  },

  /**
   * Trigger browser file download of user data export JSON
   */
  async downloadUserDataExport(): Promise<void> {
    const data = await this.exportUserData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `migraflow_data_export_${new Date().toISOString().split('T')[0]}.json`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

export default authService;
