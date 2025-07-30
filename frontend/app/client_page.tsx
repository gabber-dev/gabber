/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
import React from "react";

import { AppList } from "@/components/home/AppList";
import { SubGraphList } from "@/components/home/SubGraphList";

export function ClientPage() {
  return (
    <div className="h-full w-full p-2 flex flex-col gap-2">
      <AppList />
      <SubGraphList />
    </div>
  );
}
