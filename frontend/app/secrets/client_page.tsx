/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { SecretsPage } from "@/components/secrets/SecretsPage";

export function ClientPage() {
  // Determine if this is a local deployment to show the .secret file message
  // Local deployment is indicated by the absence of specific environment variables
  const isLocalDeployment =
    !process.env.REPOSITORY_HOST && !process.env.GABBER_PUBLIC_HOST;

  const storageDescription = isLocalDeployment
    ? "Secrets are stored in your configured .secret file. Make sure to keep this file secure and never commit it to version control."
    : null; // Hide the message for cloud deployments

  return <SecretsPage storageDescription={storageDescription} />;
}
