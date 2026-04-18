/**
 * Meridian Airport PMO suite
 * (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
 * Proprietary — unauthorised copying, distribution, modification or use prohibited.
 */
import "./globals.css";

import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Footer } from "@/components/shell/Footer";
import { GlobalHeader } from "@/components/shell/GlobalHeader";
import { Sidebar } from "@/components/shell/Sidebar";
import { endpoints } from "@/lib/api/endpoints";
import type { MeResponse, ModuleRegistryEntry } from "@/lib/types";

export const metadata: Metadata = {
  title: "Meridian — Airport Programme PMIS",
  description:
    "Meridian Airport PMO suite — Programme Management Information System for airport delivery. (c) GV Softwares. Developed by Gaurav Vatsa.",
  applicationName: "Meridian",
  authors: [{ name: "Gaurav Vatsa" }],
  creator: "Gaurav Vatsa",
  publisher: "GV Softwares",
};

// The shell fetches the module registry + current user once per request, server
// side, so the sidebar renders synchronously. Both calls degrade gracefully if
// the API is offline.
async function loadShell(): Promise<{
  modules: ModuleRegistryEntry[];
  me: MeResponse | null;
}> {
  try {
    const [modules, me] = await Promise.all([
      endpoints.modules(),
      endpoints.me().catch(() => null),
    ]);
    return { modules, me };
  } catch {
    return { modules: [], me: null };
  }
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const { modules, me } = await loadShell();
  return (
    <html lang="en">
      <body>
        <div className="flex h-screen">
          <Sidebar modules={modules} />
          <div className="flex-1 flex flex-col overflow-hidden">
            <GlobalHeader me={me} />
            <main className="flex-1 overflow-auto p-6">{children}</main>
            <Footer />
          </div>
        </div>
      </body>
    </html>
  );
}
