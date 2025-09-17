/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import type { Metadata } from "next";
import "../globals.css";
import "@fontsource/fredoka/300.css";
import "@fontsource/fredoka/400.css";
import "@fontsource/fredoka/500.css";
import "@fontsource/fredoka/600.css";
import "@fontsource/fredoka/700.css";
import "@fontsource/inter/300.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import React from "react";
import { ClientLayout } from "./client_layout";
import {
  listApps,
  listExamples,
  listPreMadeSubGraphs,
  listSubGraphs,
} from "@/lib/repository";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Gabber - Real-time AI Engine",
  description: "Real-time AI Engine for building interactive applications",
  icons: "/favicon.ico",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const apps = await listApps();
  const subgraphs = await listSubGraphs();
  const examples = await listExamples();
  const premadeSubGraphs = await listPreMadeSubGraphs();

  return (
    <html lang="en" data-theme="gabber-arcade">
      <body className="absolute w-full h-full bg-base-100">
        <ClientLayout
          initialApps={apps}
          initialSubGraphs={subgraphs}
          initialPremadeSubGraphs={premadeSubGraphs}
          examples={examples}
        >
          {children}
        </ClientLayout>
      </body>
    </html>
  );
}
