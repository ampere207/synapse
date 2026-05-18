"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import Link from "next/link";
import { Building2, Video, UploadCloud, ArrowRight } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, user, loadFromStorage } = useAuthStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFromStorage();
    setLoading(false);
  }, [loadFromStorage]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-900">Synapse</h1>
          <div className="flex items-center space-x-4">
            <span className="text-slate-600">{user?.username}</span>
            <button
              onClick={() => {
                useAuthStore.getState().logout();
                router.push("/auth/login");
              }}
              className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="space-y-12">
          {/* Welcome section */}
          <div>
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              Welcome to Synapse
            </h2>
            <p className="text-slate-600 mb-8">
              Transform meetings, transcripts, and uploads into operational intelligence.
            </p>
          </div>

          {/* Quick actions */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white">
                <Building2 size={20} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-3">
                Create Organization
              </h3>
              <p className="text-slate-600 mb-4">
                Set up a workspace for your team, then choose how data enters the system.
              </p>
              <Link
                href="/dashboard/create-org"
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition"
              >
                Get Started
                <ArrowRight size={16} />
              </Link>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-600 text-white">
                <Video size={20} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-3">
                Start a Live Meeting
              </h3>
              <p className="text-slate-600 mb-4">
                Launch a realtime session with transcript capture and graph updates.
              </p>
              <Link
                href="/workspace/live"
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition"
              >
                New Meeting
                <ArrowRight size={16} />
              </Link>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-500 text-white">
                <UploadCloud size={20} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-3">
                Upload Transcript or Audio
              </h3>
              <p className="text-slate-600 mb-4">
                Import transcripts, meeting notes, captions, or audio files into a workflow draft.
              </p>
              <Link
                href="/workspace/upload"
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition"
              >
                Upload Files
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>

          {/* Features */}
          <div className="bg-white rounded-lg border border-slate-200 p-8">
            <h3 className="text-xl font-bold text-slate-900 mb-6">Features</h3>
            <ul className="space-y-4 text-slate-600">
              <li className="flex items-start">
                <span className="text-slate-400 mr-3">✓</span>
                <span>Live meeting transcription and realtime updates</span>
              </li>
              <li className="flex items-start">
                <span className="text-slate-400 mr-3">✓</span>
                <span>Transcript and file upload workflows for non-live intake</span>
              </li>
              <li className="flex items-start">
                <span className="text-slate-400 mr-3">✓</span>
                <span>AI-powered decision and action item extraction</span>
              </li>
              <li className="flex items-start">
                <span className="text-slate-400 mr-3">✓</span>
                <span>Visual relationship and execution graphs</span>
              </li>
              <li className="flex items-start">
                <span className="text-slate-400 mr-3">✓</span>
                <span>Multi-user collaboration in real-time</span>
              </li>
              <li className="flex items-start">
                <span className="text-slate-400 mr-3">✓</span>
                <span>Organizational memory and history</span>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
