import { useAuthStore } from "@/store/auth";
import { useCallback } from "react";
import { authAPI, LoginCredentials, SignupCredentials } from "@/lib/auth";

export const useAuth = () => {
  const { user, token, isAuthenticated, setAuth, logout } = useAuthStore();

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      try {
        const response = await authAPI.login(credentials);
        setAuth(response, response.access_token);
        return { success: true };
      } catch (error: any) {
        return {
          success: false,
          error: error.response?.data?.detail || "Login failed",
        };
      }
    },
    [setAuth]
  );

  const signup = useCallback(
    async (credentials: SignupCredentials) => {
      try {
        const response = await authAPI.signup(credentials);
        // After signup, auto-login
        return { success: true, user: response };
      } catch (error: any) {
        return {
          success: false,
          error: error.response?.data?.detail || "Signup failed",
        };
      }
    },
    []
  );

  return { user, token, isAuthenticated, login, signup, logout };
};
