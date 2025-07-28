/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import Link from "next/link";
import { ClipboardDocumentIcon, CheckIcon } from "@heroicons/react/24/outline";

export function TopBar() {
  const params = useParams<{ app?: string; version?: string; flow?: string }>();
  const appId = params.app as string | undefined;

  const [copied, setCopied] = useState(false);

  const selectedFlowObj = useMemo(() => {
    return params.flow ? { data: { name: params.flow } } : null;
  }, [params.flow]);

  return (
    <div className="flex items-center gap-2 text-white">
      <Link
        href={`/`}
        className="btn btn-ghost btn-md text-md text-warning/80 font-vt323 flex items-center gap-1"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="1.5"
          stroke="currentColor"
          className="h-5 w-5 text-orange-400"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 14.25V6.75a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6.75v7.5M21 14.25l-4.5-4.5M21 14.25l-4.5 4.5M3 14.25l4.5-4.5M3 14.25l4.5 4.5"
          />
        </svg>
        MY APPS
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
          {params.version && (
            <>
              <span className="opacity-70">→</span>
              <Link
                href={`/apps/${params.app}`}
                className="text-sm opacity-70 hover:opacity-100 hover:scale-105 transform transition-all duration-200 ease-out cursor-pointer"
              >
                Version {params.version}
              </Link>
            </>
          )}
          {params.flow && selectedFlowObj && (
            <>
              <span className="opacity-70">→</span>
              <span className="text-sm opacity-70">Flows</span>
              <span className="opacity-70">→</span>
              <span className="text-sm opacity-70 hover:opacity-100 hover:scale-105 transform transition-all duration-200 ease-out cursor-pointer">
                {selectedFlowObj.data.name}
              </span>
            </>
          )}
        </>
      )}
    </div>
  );
}
