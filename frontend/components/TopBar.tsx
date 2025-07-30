/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { ClipboardDocumentIcon, CheckIcon } from "@heroicons/react/24/outline";

export function TopBar() {
  const params = useParams<{ app?: string; graph?: string }>();
  const appId = params.app as string | undefined;

  const [copied, setCopied] = useState(false);

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
      {params.app && (
        <>
          <span className="opacity-70">→</span>
          <div className="flex items-center gap-1 group">
            <Link
              href={`app/${params.app}`}
              className="text-sm opacity-70 group-hover:opacity-100 transform transition-all duration-200 ease-out cursor-pointer"
            >
              {appId}
            </Link>
            <button
              onClick={() => {
                navigator.clipboard.writeText(appId || "");
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
              className="opacity-50 hover:opacity-90 transition-opacity"
              title="Copy App ID"
            >
              {copied ? (
                <CheckIcon className="h-4 w-4 text-success" />
              ) : (
                <ClipboardDocumentIcon className="h-4 w-4" />
              )}
            </button>
            {copied && (
              <span className="text-success text-xs ml-1">Copied</span>
            )}
          </div>
        </>
      )}
    </div>
  );
}
