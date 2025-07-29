/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
import React from "react";

import { AppList } from "@/components/home/AppList";

export function ClientPage() {
  return (
    <div className="h-full w-full p-2">
      <AppList />
    </div>
  );
}
