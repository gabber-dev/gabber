/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
import { ExampleList } from "@/components/home/ExampleList";
import React from "react";

export function ClientPage() {
  return (
    <div className="h-full w-full p-2 flex flex-col gap-2">
      <ExampleList />
    </div>
  );
}
