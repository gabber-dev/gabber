/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { FlowEdit } from "../flow/FlowEdit";
import { BottomBar } from "./BottomBar";
import { useEditor } from "@/hooks/useEditor";
import { LogList } from "../log/LogList";
import { useRun } from "@/hooks/useRun";

export function AppEditPage() {
  return <AppEditPageInner />;
}

function AppEditPageInner() {
  const { unsavedChanges, logsShowing } = useEditor();
  const { connectionState } = useRun();
  const router = useRouter();

  // Determine if editing should be disabled while the app is running
  const isRunning =
    connectionState === "connected" || connectionState === "connecting";
  const editable = !isRunning;

  // Add beforeunload event listener to warn about unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (unsavedChanges) {
        e.preventDefault();
        return "You have unsaved changes. Are you sure you want to leave?";
      }
    };

    // Handle client-side navigation
    const handleRouteChange = () => {
      if (unsavedChanges) {
        const confirmed = window.confirm(
          "You have unsaved changes. Are you sure you want to leave?",
        );
        if (!confirmed) {
          // Prevent navigation by throwing an error
          throw new Error("Navigation cancelled by user");
        }
      }
    };

    // Listen for beforeunload (refresh/close)
    window.addEventListener("beforeunload", handleBeforeUnload);

    // Listen for popstate (back/forward buttons)
    window.addEventListener("popstate", handleRouteChange);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("popstate", handleRouteChange);
    };
  }, [unsavedChanges]);

  // Override router.push to check for unsaved changes
  useEffect(() => {
    if (!unsavedChanges) return;

    const originalPush = router.push;
    router.push = (...args: Parameters<typeof originalPush>) => {
      const confirmed = window.confirm(
        "You have unsaved changes. Are you sure you want to leave?",
      );
      if (confirmed) {
        originalPush.apply(router, args);
      }
    };

    return () => {
      router.push = originalPush;
    };
  }, [unsavedChanges, router]);

  return (
    <div className="relative w-full h-full flex flex-col overflow-hidden">
      <div className="absolute top-0 left-0 right-0 bottom-16">
        <FlowEdit editable={editable} />
      </div>

      <div
        className={`absolute top-0 right-0 bottom-16 w-1/3 bg-gray-primary transition-transform duration-300 ease-in-out z-10 ${logsShowing ? "translate-x-0" : "translate-x-full"}`}
      >
        <LogList />
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-16">
        <BottomBar
          saveButtonEnabled={true}
          logButtonEnabled={true}
          debugControlsEnabled={true}
        />
      </div>
    </div>
  );
}
