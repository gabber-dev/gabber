/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
// import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { BeakerIcon } from "@heroicons/react/24/outline";

export function TopBar() {
  // const params = useParams<{ app?: string; graph?: string }>();

  return (
    <div className="flex items-center justify-between bg-base-200 h-full w-full px-4">
      <div className="flex items-center gap-4">
        <Link href={`/`} className="flex items-center py-2">
          <Image
            src="https://gabber-v2.gabber.dev/gabber-logo%201.png"
            alt="Gabber"
            width={100}
            height={100}
            className="object-contain"
            priority
          />
        </Link>
        <Link
          href={`/example`}
          className="btn btn-sm btn-ghost gap-2 normal-case border border-base-300 hover:border-base-content/20"
        >
          <BeakerIcon className="w-4 h-4" />
          Examples
        </Link>
      </div>

      <Link
        href="https://github.com/gabber-dev/gabber"
        target="_blank"
        rel="noopener noreferrer"
        className="btn btn-sm btn-ghost gap-2 normal-case border border-base-300 hover:border-base-content/20"
      >
        <svg viewBox="0 0 16 16" className="w-5 h-5 fill-current">
          <path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z" />
        </svg>
        GitHub
        <svg viewBox="0 0 16 16" className="w-4 h-4 fill-current">
          <path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z" />
        </svg>
      </Link>
    </div>
  );
}
