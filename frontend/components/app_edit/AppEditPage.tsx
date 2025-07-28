/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ConsolePanel } from "./ConsolePanel";
import { FlowEdit } from "../flow/FlowEdit";
import { BottomBar } from "./BottomBar";
import { useEditor } from "@/hooks/useEditor";

export function AppEditPage() {
  return (
    <ConsoleProvider>
      <AppEditPageInner />
    </ConsoleProvider>
  );
}

function AppEditPageInner() {
  const [isConsoleOpen, setIsConsoleOpen] = useState(false);
  const { unsavedChanges } = useEditor();
  const router = useRouter();

  const handleConsoleToggle = useCallback(() => {
    setIsConsoleOpen(!isConsoleOpen);
  }, [isConsoleOpen]);

  // Add beforeunload event listener to warn about unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (unsavedChanges) {
        e.preventDefault();
        e.returnValue =
          "You have unsaved changes. Are you sure you want to leave?";
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
    <div className="relative w-full h-full flex flex-col">
      <div className="absolute top-0 left-0 right-0 bottom-16">
        <FlowEdit />
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-16">
        <BottomBar
          isConsoleOpen={isConsoleOpen}
          onConsoleToggle={handleConsoleToggle}
        />
      </div>

      <ConsolePanel
        isOpen={isConsoleOpen}
        onClose={() => setIsConsoleOpen(false)}
      />
    </div>
  );
}
