/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
// import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { ClipboardDocumentIcon, CheckIcon } from "@heroicons/react/24/outline";

export function TopBar() {
  // const params = useParams<{ app?: string; graph?: string }>();

  return (
    <div className="flex items-center gap-2 bg-base-200 h-full w-full px-2">
      <Link href={`/`} className="flex items-center py-2">
        <Image
          src="/logo.png"
          alt="Gabber"
          width={100}
          height={100}
          className="object-contain"
        />
      </Link>
      <Link href={`/example`}>Examples</Link>
    </div>
  );
}
