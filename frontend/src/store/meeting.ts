import { create } from "zustand";

export interface Meeting {
  id: string;
  organization_id: string;
  title: string;
  description?: string;
  status: "draft" | "live" | "completed" | "archived";
  created_at: string;
  updated_at: string;
}

export interface TranscriptChunk {
  id: string;
  speaker?: string;
  text: string;
  timestamp?: number;
  sequence_number: number;
}

interface MeetingStore {
  currentMeeting: Meeting | null;
  transcriptChunks: TranscriptChunk[];
  setCurrentMeeting: (meeting: Meeting) => void;
  addTranscriptChunk: (chunk: TranscriptChunk) => void;
  clearMeeting: () => void;
}

export const useMeetingStore = create<MeetingStore>((set) => ({
  currentMeeting: null,
  transcriptChunks: [],
  setCurrentMeeting: (meeting) => set({ currentMeeting: meeting }),
  addTranscriptChunk: (chunk) =>
    set((state) => ({
      transcriptChunks: [...state.transcriptChunks, chunk],
    })),
  clearMeeting: () => set({ currentMeeting: null, transcriptChunks: [] }),
}));
