"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, UploadCloud, FileText, AudioLines } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { meetingAPI } from "@/lib/meeting";

type UploadAsset = {
  name: string;
  type: string;
  size: number;
  extractedText?: string | null;
};

function isTextLikeFile(file: File) {
  return file.type.startsWith("text/") || /\.(txt|md|markdown|srt|vtt|csv|json|log)$/i.test(file.name);
}

function readFileAsText(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("Unable to read file"));
    reader.readAsText(file);
  });
}

export default function UploadWorkflowPage() {
  const router = useRouter();
  const { isAuthenticated, loadFromStorage } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [organizationId, setOrganizationId] = useState("");
  const [title, setTitle] = useState("Uploaded workflow");
  const [description, setDescription] = useState("Transcript, notes, and file-driven intake.");
  const [transcriptText, setTranscriptText] = useState("");
  const [assets, setAssets] = useState<UploadAsset[]>([]);
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

  const totalCharacters = useMemo(
    () => transcriptText.trim().length + assets.reduce((sum, asset) => sum + (asset.extractedText?.trim().length || 0), 0),
    [assets, transcriptText]
  );

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    if (selectedFiles.length === 0) {
      return;
    }

    const processedAssets = await Promise.all(
      selectedFiles.map(async (file) => ({
        name: file.name,
        type: file.type || "application/octet-stream",
        size: file.size,
        extractedText: isTextLikeFile(file) ? await readFileAsText(file) : null,
      }))
    );

    setAssets((current) => [...current, ...processedAssets]);
    event.target.value = "";
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!organizationId.trim()) {
      setError("Add an organization ID first, or create one from the dashboard.");
      return;
    }

    if (!transcriptText.trim() && assets.length === 0) {
      setError("Add a transcript, notes file, or upload at least one file.");
      return;
    }

    try {
      setSaving(true);
      const meeting = await meetingAPI.createMeeting(organizationId.trim(), {
        title: title.trim() || "Uploaded workflow",
        description: description.trim() || null,
      });

      const draft = {
        meetingId: meeting.id,
        organizationId: organizationId.trim(),
        title: title.trim() || "Uploaded workflow",
        description: description.trim() || null,
        transcriptText: transcriptText.trim(),
        assets,
        createdAt: new Date().toISOString(),
      };

      if (typeof window !== "undefined") {
        window.localStorage.setItem(`synapse:upload-draft:${meeting.id}`, JSON.stringify(draft));
        window.localStorage.setItem("synapse:lastOrganizationId", organizationId.trim());
      }

      router.push(`/workspace/${organizationId.trim()}/meeting/${meeting.id}/intelligence`);
    } catch (submissionError: any) {
      setError(submissionError?.response?.data?.detail || "Unable to prepare the upload workflow.");
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
      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-[32px] border border-slate-200 bg-white p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500 text-white">
              <UploadCloud size={20} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Upload intake</p>
              <h1 className="text-3xl font-semibold text-slate-950">Create a file-based workflow</h1>
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
              <label htmlFor="title" className="text-sm font-medium text-slate-700">Workflow title</label>
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
                rows={4}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
              />
            </div>

            <div className="grid gap-2">
              <label htmlFor="transcriptText" className="text-sm font-medium text-slate-700">Transcript or notes</label>
              <textarea
                id="transcriptText"
                value={transcriptText}
                onChange={(event) => setTranscriptText(event.target.value)}
                rows={8}
                placeholder="Paste transcript text, captions, or meeting notes here."
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
              />
            </div>

            <div className="grid gap-3 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5">
              <div>
                <label htmlFor="files" className="text-sm font-medium text-slate-700">Attach transcript, captions, audio, or docs</label>
                <p className="mt-1 text-xs text-slate-500">Text files are previewed immediately. Audio files are captured as workflow assets.</p>
              </div>
              <input
                id="files"
                type="file"
                multiple
                accept=".txt,.md,.markdown,.srt,.vtt,.csv,.json,.log,.mp3,.wav,.m4a,.ogg,.flac,.pdf,.docx"
                onChange={handleFileChange}
                className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-2xl file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-800"
              />
            </div>

            {assets.length > 0 && (
              <div className="space-y-3 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-center gap-2 text-slate-500">
                  <FileText size={16} />
                  <span className="text-xs font-semibold uppercase tracking-[0.2em]">Attached assets</span>
                </div>
                <div className="space-y-3">
                  {assets.map((asset) => (
                    <div key={`${asset.name}-${asset.size}`} className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-medium text-slate-950">{asset.name}</p>
                          <p className="text-xs text-slate-500">{asset.type || "unknown type"}</p>
                        </div>
                        {asset.extractedText ? (
                          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                            Previewed as text
                          </span>
                        ) : (
                          <span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                            Binary asset
                          </span>
                        )}
                      </div>
                      {asset.extractedText && <p className="mt-3 line-clamp-3 text-xs leading-5 text-slate-500">{asset.extractedText.slice(0, 240)}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

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
                {saving ? "Preparing workflow..." : "Save upload workflow"}
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
            <AudioLines size={14} />
            Transcript-first upload path
          </div>
          <div>
            <h2 className="text-3xl font-semibold tracking-tight">File-based intake</h2>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              Users can paste text, attach captions, or bring in audio and document assets. The workflow is saved with a meeting shell so the intelligence view can pick it up.
            </p>
          </div>

          <div className="grid gap-4">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Current payload</p>
              <p className="mt-2 text-sm text-slate-200">{assets.length} attached asset(s) and {totalCharacters.toLocaleString()} captured characters.</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">What is saved</p>
              <p className="mt-2 text-sm text-slate-200">A workflow draft is stored locally and the meeting shell is created so the intake can be revisited in intelligence view.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}