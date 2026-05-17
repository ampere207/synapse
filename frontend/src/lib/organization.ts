import apiClient from "@/lib/api";

export const organizationAPI = {
  createOrganization: async (data: any) => {
    const response = await apiClient.post("/organizations/", data);
    return response.data;
  },

  getOrganization: async (orgId: string) => {
    const response = await apiClient.get(`/organizations/${orgId}`);
    return response.data;
  },

  updateOrganization: async (orgId: string, data: any) => {
    const response = await apiClient.patch(`/organizations/${orgId}`, data);
    return response.data;
  },
};
