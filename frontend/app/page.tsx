import React from "react";

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-bold text-slate-900">Synapse</h1>
        <p className="text-xl text-slate-600">
          AI Meeting Intelligence Platform
        </p>
        <p className="text-slate-500 max-w-md mx-auto">
          Transform meetings, transcripts, and discussions into living operational intelligence graphs
        </p>
        <div className="pt-8 space-x-4">
          <a
            href="/auth/login"
            className="inline-block px-6 py-3 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition"
          >
            Login
          </a>
          <a
            href="/auth/signup"
            className="inline-block px-6 py-3 bg-slate-200 text-slate-900 rounded-lg font-medium hover:bg-slate-300 transition"
          >
            Sign Up
          </a>
        </div>
      </div>
    </main>
  );
}
