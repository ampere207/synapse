"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Building2, Layers3 } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { organizationAPI } from "@/lib/organization";

function toSlug(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function CreateOrganizationPage() {
  const router = useRouter();
  const { isAuthenticated, loadFromStorage, user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFromStorage();
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

    const finalName = name.trim();
    const finalSlug = slug.trim() || toSlug(finalName);

    if (!finalName) {
      setError("Organization name is required.");
      return;
    }

    if (!finalSlug) {
      setError("Organization slug is required.");
      return;
    }

    try {
      setSaving(true);
      const organization = await organizationAPI.createOrganization({
        name: finalName,
        slug: finalSlug,
        description: description.trim() || null,
      });

      if (typeof window !== "undefined") {
        window.localStorage.setItem("synapse:lastOrganizationId", organization.id);
        window.localStorage.setItem("synapse:lastOrganizationName", organization.name);
      }

      router.push("/workspace");
    } catch (submissionError: any) {
      setError(submissionError?.response?.data?.detail || "Unable to create the organization.");
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
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(15,23,42,0.08),_transparent_30%),linear-gradient(180deg,_#f8fafc_0%,_#ffffff_45%,_#f8fafc_100%)]">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid w-full gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[32px] border border-slate-200 bg-white/90 p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
            <div className="mb-8 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
                <Building2 size={20} />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Workspace Setup</p>
                <h1 className="text-2xl font-semibold text-slate-950">Create an organization</h1>
              </div>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="grid gap-2">
                <label htmlFor="name" className="text-sm font-medium text-slate-700">Organization name</label>
                <input
                  id="name"
                  value={name}
                  onChange={(event) => {
                    setName(event.target.value);
                    if (!slug) {
                      setSlug(toSlug(event.target.value));
                    }
                  }}
                  placeholder="Acme Operations"
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
                />
              </div>

              <div className="grid gap-2">
                <label htmlFor="slug" className="text-sm font-medium text-slate-700">Slug</label>
                <input
                  id="slug"
                  value={slug}
                  onChange={(event) => setSlug(event.target.value)}
                  placeholder="acme-operations"
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
                />
              </div>

              <div className="grid gap-2">
                <label htmlFor="description" className="text-sm font-medium text-slate-700">Description</label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Teams, meetings, and uploads that should share one intelligence workspace."
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
                  {saving ? "Creating organization..." : "Create organization"}
                  <ArrowRight size={16} />
                </button>
                <Link href="/workspace" className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
                  Cancel
                </Link>
              </div>
            </form>
          </div>

          <div className="space-y-6 rounded-[32px] border border-slate-200 bg-slate-950 p-8 text-white shadow-[0_24px_80px_rgba(15,23,42,0.22)]">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-200">
              <Layers3 size={14} />
              Live meetings and file intake
            </div>
            <div>
              <h2 className="text-3xl font-semibold tracking-tight">Set up the workspace once, then choose how users start.</h2>
              <p className="mt-4 max-w-lg text-sm leading-6 text-slate-300">
                The organization is the anchor for live meetings, transcript uploads, file-driven workflows, and the intelligence graph.
                Once it is created, the workspace hub exposes both intake paths instead of forcing everyone into meetings.
              </p>
            </div>

            <div className="grid gap-4">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Suggested flow</p>
                <p className="mt-2 text-sm text-slate-200">Create organization → open workspace hub → choose live meeting or upload path.</p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Current user</p>
                <p className="mt-2 text-sm text-slate-200">{user?.username || user?.email || "Authenticated user"}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}