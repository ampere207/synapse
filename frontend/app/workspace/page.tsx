"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/auth";
import { Building2, ArrowRight, Video, UploadCloud, Layers3 } from "lucide-react";

type LastOrganization = {
  id?: string;
  name?: string;
};

export default function WorkspacePage() {
  const router = useRouter();
  const { isAuthenticated, loadFromStorage } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [lastOrganization, setLastOrganization] = useState<LastOrganization | null>(null);

  useEffect(() => {
    loadFromStorage();
    if (typeof window !== "undefined") {
      const orgId = window.localStorage.getItem("synapse:lastOrganizationId") || undefined;
      const orgName = window.localStorage.getItem("synapse:lastOrganizationName") || undefined;
      if (orgId || orgName) {
        setLastOrganization({ id: orgId, name: orgName });
      }
    }
    setLoading(false);
  }, [loadFromStorage]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(15,23,42,0.08),_transparent_32%),linear-gradient(180deg,_#f8fafc_0%,_#ffffff_42%,_#f8fafc_100%)] text-slate-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 rounded-[32px] border border-slate-200 bg-white/90 p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
                <Layers3 size={14} />
                Workflow hub
              </div>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">Choose how you want to start.</h1>
                <p className="mt-3 text-sm leading-6 text-slate-600 sm:text-base">
                  Synapse now exposes separate paths for live meetings and file-driven intake.
                  Create an organization first if you need a workspace anchor, then launch the workflow that matches the user&apos;s source material.
                </p>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-slate-950 p-5 text-white shadow-lg shadow-slate-950/10">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10">
                  <Building2 size={20} />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Last organization</p>
                  <p className="mt-1 text-sm font-medium text-white">{lastOrganization?.name || "No organization saved yet"}</p>
                  {lastOrganization?.id && <p className="text-xs text-slate-400">{lastOrganization.id}</p>}
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-[28px] border border-slate-200 bg-slate-950 p-6 text-white shadow-[0_18px_50px_rgba(15,23,42,0.18)]">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500 text-white">
                <Video size={22} />
              </div>
              <h2 className="mt-5 text-2xl font-semibold">Live meeting</h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
                Start a realtime meeting session, capture transcript chunks, and feed the intelligence graph as the conversation unfolds.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/workspace/live"
                  className="inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-medium text-slate-950 transition hover:bg-slate-100"
                >
                  Start live meeting
                  <ArrowRight size={16} />
                </Link>
                <Link
                  href="/dashboard/create-org"
                  className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/10"
                >
                  Create organization
                </Link>
              </div>
            </div>

            <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500 text-white">
                <UploadCloud size={22} />
              </div>
              <h2 className="mt-5 text-2xl font-semibold text-slate-950">Upload workflow</h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600">
                Import transcripts, captions, meeting notes, or audio-backed files into a draft workflow so non-live users can still enter the system.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/workspace/upload"
                  className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
                >
                  Open upload intake
                  <ArrowRight size={16} />
                </Link>
                <Link
                  href="/dashboard/create-org"
                  className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  New organization
                </Link>
              </div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["Live meetings", "Realtime transcript capture and graph mutation updates."],
              ["Transcript uploads", "Paste or upload meeting notes, captions, and text exports."],
              ["Audio and files", "Accept supporting files for later transcription or review."],
            ].map(([title, description]) => (
              <div key={title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-semibold text-slate-950">{title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
