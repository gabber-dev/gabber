/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { getApp, getEditorUrl } from "@/lib/repository";
import { ClientPage } from "./client_page";

export default async function Page({
  params,
}: {
  params: Promise<{ app: string }>;
}) {
  const { app } = await params;
  const appObj = await getApp(app);
  const editorUrl = getEditorUrl();
  return <ClientPage existingApp={appObj} editorUrl={editorUrl} />;
}
