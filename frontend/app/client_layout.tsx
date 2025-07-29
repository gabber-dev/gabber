"use client";

import { Toaster } from "react-hot-toast";

export function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Toaster />
      <div className="h-full grow overflow-y-auto">{children}</div>
    </>
  );
}
