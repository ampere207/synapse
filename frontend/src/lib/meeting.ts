import apiClient from "@/lib/api";

export const meetingAPI = {
  createMeeting: async (orgId: string, data: any) => {
    const response = await apiClient.post(
      `/organizations/${orgId}/meetings`,
      data
    );
    return response.data;
  },

  getMeeting: async (orgId: string, meetingId: string) => {
    const response = await apiClient.get(
      `/organizations/${orgId}/meetings/${meetingId}`
    );
    return response.data;
  },

  updateMeeting: async (orgId: string, meetingId: string, data: any) => {
    const response = await apiClient.patch(
      `/organizations/${orgId}/meetings/${meetingId}`,
      data
    );
    return response.data;
  },

  listMeetings: async (orgId: string) => {
    const response = await apiClient.get(`/organizations/${orgId}/meetings`);
    return response.data;
  },
};
