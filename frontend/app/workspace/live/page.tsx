"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Video, Building2 } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { meetingAPI } from "@/lib/meeting";

export default function LiveMeetingPage() {
  const router = useRouter();
  const { isAuthenticated, loadFromStorage } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [organizationId, setOrganizationId] = useState("");
  const [title, setTitle] = useState("Live meeting");
  const [description, setDescription] = useState("Realtime meeting capture and intelligence extraction.");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFromStorage();
    if (typeof window !== "undefined") {
      const storedOrganizationId = window.localStorage.getItem("synapse:lastOrganizationId") || "";
      if (storedOrganizationId) {
        setOrganizationId(storedOrganizationId);
      }
    }
    setLoading(false);
  }, [loadFromStorage]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, loading, router]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!organizationId.trim()) {
      setError("Add an organization ID first, or create one from the dashboard.");
      return;
    }

    try {
      setSaving(true);
      const meeting = await meetingAPI.createMeeting(organizationId.trim(), {
        title: title.trim() || "Live meeting",
        description: description.trim() || null,
      });

      if (typeof window !== "undefined") {
        window.localStorage.setItem("synapse:lastOrganizationId", organizationId.trim());
      }

      router.push(`/workspace/${organizationId.trim()}/meeting/${meeting.id}/intelligence`);
    } catch (submissionError: any) {
      setError(submissionError?.response?.data?.detail || "Unable to create the live meeting.");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(15,23,42,0.08),_transparent_30%),linear-gradient(180deg,_#f8fafc_0%,_#ffffff_45%,_#f8fafc_100%)] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[32px] border border-slate-200 bg-white p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-white">
              <Video size={20} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Live meetings</p>
              <h1 className="text-3xl font-semibold text-slate-950">Launch a meeting session</h1>
            </div>
          </div>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <div className="grid gap-2">
              <label htmlFor="organizationId" className="text-sm font-medium text-slate-700">Organization ID</label>
              <input
                id="organizationId"
                value={organizationId}
                onChange={(event) => setOrganizationId(event.target.value)}
                placeholder="Paste the organization ID here"
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
              />
            </div>

            <div className="grid gap-2">
              <label htmlFor="title" className="text-sm font-medium text-slate-700">Meeting title</label>
              <input
                id="title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
              />
            </div>

            <div className="grid gap-2">
              <label htmlFor="description" className="text-sm font-medium text-slate-700">Description</label>
              <textarea
                id="description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={5}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
              />
            </div>

            {error && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {saving ? "Starting meeting..." : "Start live meeting"}
                <ArrowRight size={16} />
              </button>
              <Link href="/workspace" className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
                Back to hub
              </Link>
            </div>
          </form>
        </div>

        <div className="space-y-5 rounded-[32px] border border-slate-200 bg-slate-950 p-8 text-white shadow-[0_24px_80px_rgba(15,23,42,0.2)]">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-200">
            <Building2 size={14} />
            Uses the last created organization automatically
          </div>
          <div>
            <h2 className="text-3xl font-semibold tracking-tight">Live meeting capture</h2>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              This path creates a meeting record and sends you straight into the intelligence view, where transcript chunks, graph mutations, and extraction updates live.
            </p>
          </div>

          <div className="grid gap-4">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Input required</p>
              <p className="mt-2 text-sm text-slate-200">An organization ID plus a meeting title is enough to launch the flow.</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Next step</p>
              <p className="mt-2 text-sm text-slate-200">After creation, Synapse opens the live intelligence workspace for that meeting.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}