import apiClient from "@/lib/api";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials extends LoginCredentials {
  username: string;
  full_name?: string;
}

export const authAPI = {
  login: async (credentials: LoginCredentials) => {
    const response = await apiClient.post("/auth/login", credentials);
    return response.data;
  },

  signup: async (credentials: SignupCredentials) => {
    const response = await apiClient.post("/auth/register", credentials);
    return response.data;
  },

  refresh: async (refreshToken: string) => {
    const response = await apiClient.post("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },
};
