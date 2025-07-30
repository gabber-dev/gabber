/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { getExample } from "@/lib/repository";
import { ClientPage } from "./client_page";

export default async function Page({
  params,
}: {
  params: Promise<{ example: string }>;
}) {
  const { example } = await params;
  const exampleObj = await getExample(example);
  return <ClientPage existingExample={exampleObj} />;
}
