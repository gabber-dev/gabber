/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { SecretsPage } from "@/components/secrets/SecretsPage";

export function ClientPage() {
  return (
    <SecretsPage storageDescription="Secrets are stored in your configured .secret file. Make sure to keep this file secure and never commit it to version control." />
  );
}
