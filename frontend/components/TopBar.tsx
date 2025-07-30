/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
// import { useParams } from "next/navigation";
import Link from "next/link";

export function TopBar() {
  // const params = useParams<{ app?: string; graph?: string }>();

  return (
    <div className="flex items-center gap-2 bg-base-200 h-full w-full px-2">
      <Link href={`/`} className="">
        Gabber
      </Link>
      <Link href={`/example`}>Examples</Link>
    </div>
  );
}
