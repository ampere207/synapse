import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Synapse - AI Meeting Intelligence",
  description:
    "Transform meetings, transcripts, and discussions into living operational intelligence graphs",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
