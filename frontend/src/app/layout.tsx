import type { Metadata } from "next";

import "./globals.css";
import { AppShell } from "@/components/shell";

export const metadata: Metadata = {
  title: "AI-TriboTwin | Experimental workspace",
  description: "Scientific data intake and experiment planning workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
