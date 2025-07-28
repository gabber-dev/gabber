/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import React from "react";
import { TopBar } from "@/components/TopBar";

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative h-full w-full">
      <div className="absolute top-2 left-2 z-50">
        <TopBar />
      </div>
      <div className="absolute top-0 bottom-0 left-0 right-0 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
