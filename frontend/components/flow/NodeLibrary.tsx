/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import React, { useState, useCallback, useMemo } from "react";
import { useEditor } from "@/hooks/useEditor";
import { useReactFlow } from "@xyflow/react";
import {
  GraphLibraryItem_Node,
  GraphLibraryItem_SubGraph,
} from "@/generated/editor";
import {
  XMarkIcon,
  MagnifyingGlassIcon,
  CircleStackIcon,
} from "@heroicons/react/24/outline";

interface NodeLibraryProps {
  setIsModalOpen: (open: boolean) => void;
}

export function NodeLibrary({ setIsModalOpen }: NodeLibraryProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMainCategory, setSelectedMainCategory] = useState<
    string | null
  >(null);
  const [selectedSubcategory1, setSelectedSubcategory1] = useState<
    string | null
  >(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [draggedItem, setDraggedItem] = useState<
    GraphLibraryItem_Node | GraphLibraryItem_SubGraph | null
  >(null);

  const { nodeLibrary, insertNode, insertSubGraph } = useEditor();
  const { screenToFlowPosition } = useReactFlow();

  // Simple dropdown options
  const primaryOptions = useMemo(() => {
    const options = [
      ...new Set(
        nodeLibrary?.map((n) => (n as any).metadata?.primary).filter(Boolean),
      ),
    ];

    // Add "Subgraphs" category if there are any subgraph nodes
    if (nodeLibrary?.some((n) => n.type === "subgraph")) {
      options.push("My Subgraphs");
    }

    return options.sort();
  }, [nodeLibrary]);

  const secondaryOptions = useMemo(
    () =>
      selectedMainCategory
        ? [
            ...new Set(
              nodeLibrary
                ?.filter(
                  (n) => (n as any).metadata?.primary === selectedMainCategory,
                )
                .map((n) => (n as any).metadata?.secondary)
                .filter(Boolean),
            ),
          ].sort()
        : [],
    [nodeLibrary, selectedMainCategory],
  );

  const tagOptions = useMemo(
    () =>
      selectedMainCategory && selectedSubcategory1
        ? [
            ...new Set(
              nodeLibrary
                ?.filter(
                  (n) =>
                    (n as any).metadata?.primary === selectedMainCategory &&
                    (n as any).metadata?.secondary === selectedSubcategory1,
                )
                .flatMap((n) => (n as any).metadata?.tags || []),
            ),
          ].sort()
        : [],
    [nodeLibrary, selectedMainCategory, selectedSubcategory1],
  );

  // Simple, direct filtering
  const filteredBlocks = useMemo(() => {
    return (
      nodeLibrary?.filter((node) => {
        const { metadata } = node as any;

        // Treat subgraph nodes as having a special "My Subgraphs" category
        const effectivePrimary =
          node.type === "subgraph" ? "My Subgraphs" : metadata?.primary;

        // Apply filters only if metadata exists or it's a subgraph
        if (metadata || node.type === "subgraph") {
          if (selectedMainCategory && effectivePrimary !== selectedMainCategory)
            return false;
          if (
            selectedSubcategory1 &&
            metadata?.secondary !== selectedSubcategory1
          )
            return false;
          if (selectedTag && !metadata?.tags?.includes(selectedTag))
            return false;
        }

        // Search filter applies to all nodes
        if (
          searchQuery &&
          !node.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
          return false;

        return true;
      }) || []
    );
  }, [
    nodeLibrary,
    selectedMainCategory,
    selectedSubcategory1,
    selectedTag,
    searchQuery,
  ]);

  const clearAllFilters = useCallback(() => {
    setSelectedMainCategory(null);
    setSelectedSubcategory1(null);
    setSelectedTag(null);
    setSearchQuery("");
  }, []);

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value);
    },
    [],
  );

  const handleBlockSelect = useCallback(
    (block: GraphLibraryItem_Node | GraphLibraryItem_SubGraph) => {
      if (block.type === "subgraph") {
        insertSubGraph({
          type: "insert_sub_graph",
          subgraph_id: block.id,
          subgraph_name: block.name,
          editor_name: block.name,
          editor_position: [0, 0],
        });
      } else if (block.type === "node") {
        insertNode({
          type: "insert_node",
          node_type: block.name,
          editor_name: block.name,
          editor_position: [0, 0],
        });
      }
    },
    [insertNode, insertSubGraph],
  );

  const handleDragStart = useCallback(
    (
      e: React.DragEvent,
      block: GraphLibraryItem_Node | GraphLibraryItem_SubGraph,
    ) => {
      setDraggedItem(block);
      e.dataTransfer.setData("application/reactflow", JSON.stringify(block));
      e.dataTransfer.effectAllowed = "move";

      // Create a simple drag preview
      const dragPreview = document.createElement("div");
      dragPreview.className = `
        absolute -top-[1000px] -left-[1000px] w-[180px] px-3 py-2
        bg-base-300 border-2 border-primary rounded-lg text-primary
        font-semibold text-sm rotate-[5deg] opacity-90
        shadow-[4px_4px_0px_rgba(252,211,77,0.6)] pointer-events-none z-[9999]
      `;

      const description = (block as any).description;
      dragPreview.textContent = description
        ? `${block.name}: ${description}`
        : block.name;

      document.body.appendChild(dragPreview);
      e.dataTransfer.setDragImage(dragPreview, 90, 20);

      // Clean up immediately after the drag starts
      requestAnimationFrame(() => {
        if (document.body.contains(dragPreview)) {
          document.body.removeChild(dragPreview);
        }
      });
    },
    [],
  );

  const handleDragEnd = useCallback(() => {
    setDraggedItem(null);
  }, []);

  // Set up global drop handlers for the canvas
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();

      if (!draggedItem) return;

      // Convert screen coordinates to flow coordinates
      const position = screenToFlowPosition({
        x: e.clientX,
        y: e.clientY,
      });

      if (draggedItem.type === "subgraph") {
        insertSubGraph({
          type: "insert_sub_graph",
          subgraph_id: draggedItem.id,
          subgraph_name: draggedItem.name,
          editor_name: draggedItem.name,
          editor_position: [position.x, position.y],
        });
      } else if (draggedItem.type === "node") {
        insertNode({
          type: "insert_node",
          node_type: draggedItem.name,
          editor_name: draggedItem.name,
          editor_position: [position.x, position.y],
        });
      }

      setDraggedItem(null);
    },
    [
      draggedItem,
      insertNode,
      insertSubGraph,
      screenToFlowPosition,
    ],
  );

  // Attach global listeners for drop anywhere on canvas
  const setupDropZone = useCallback(() => {
    const canvas = document.querySelector(".react-flow");
    if (canvas) {
      canvas.addEventListener("dragover", handleDragOver as any);
      canvas.addEventListener("drop", handleDrop as any);
      return () => {
        canvas.removeEventListener("dragover", handleDragOver as any);
        canvas.removeEventListener("drop", handleDrop as any);
      };
    }
  }, [handleDragOver, handleDrop]);

  // Set up drop zone when component mounts
  React.useEffect(() => {
    const cleanup = setupDropZone();
    return cleanup;
  }, [setupDropZone]);

  return (
    <div className="w-full h-full p-3 bg-base-300 text-base-content overflow-hidden flex flex-col">
      {/* Header */}
      <div className="mb-2 flex justify-between items-center">
        <h2 className="text-lg font-vt323 uppercase tracking-wider text-primary">
          Node Library
        </h2>
        <button
          onClick={() => setIsModalOpen(false)}
          className="text-xs font-medium bg-error/20 text-error border border-error/30 rounded hover:bg-error/30 transition-colors px-1.5 py-0.5"
        >
          Close
        </button>
      </div>

      {/* Search input */}
      <div className="relative mb-2">
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchQuery}
          onChange={handleSearchChange}
          className="w-full py-1.5 px-2 bg-base-100 border border-primary/30 rounded 
                     focus:outline-none focus:border-primary
                     transition-all duration-300 text-sm text-base-content
                     placeholder:text-base-content/50"
        />
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
          <MagnifyingGlassIcon className="h-4 w-4 text-primary/50" />
        </div>
      </div>

      {/* Top Filters */}
      <div className="flex flex-nowrap gap-1.5 mb-2 overflow-x-auto">
        {/* Primary Category Select */}
        <div className="flex-shrink-0">
          <select
            value={selectedMainCategory || ""}
            onChange={(e) => {
              setSelectedMainCategory(e.target.value || null);
              setSelectedSubcategory1(null);
              setSelectedTag(null);
            }}
            className="border border-primary/30 bg-base-200 text-primary px-1.5 py-0.5 text-xs w-[85px] cursor-pointer rounded hover:border-primary/50 hover:bg-base-300 transition-colors"
          >
            <option value="">Primary</option>
            {primaryOptions.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>

        {/* Secondary Select */}
        {selectedMainCategory && (
          <div className="flex-shrink-0">
            <select
              value={selectedSubcategory1 || ""}
              onChange={(e) => {
                setSelectedSubcategory1(e.target.value || null);
                setSelectedTag(null);
              }}
              className="border border-accent/30 bg-base-200 text-accent px-1.5 py-0.5 text-xs w-[85px] cursor-pointer rounded hover:border-accent/50 hover:bg-base-300 transition-colors"
            >
              <option value="">Sub</option>
              {secondaryOptions.map((sub) => (
                <option key={sub} value={sub}>
                  {sub}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Tags Select */}
        {selectedSubcategory1 && (
          <div className="flex-shrink-0">
            <select
              value={selectedTag || ""}
              onChange={(e) => {
                setSelectedTag(e.target.value || null);
              }}
              className="border border-secondary/30 bg-base-200 text-secondary px-1.5 py-0.5 text-xs w-[85px] cursor-pointer rounded hover:border-secondary/50 hover:bg-base-300 transition-colors"
            >
              <option value="">Tags</option>
              {tagOptions.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Clear filters button */}
        {(selectedMainCategory || selectedSubcategory1 || selectedTag) && (
          <button
            onClick={clearAllFilters}
            className="border border-base-content/30 bg-base-200 text-base-content/70 hover:text-base-content px-1.5 py-0.5 text-xs w-12 flex-shrink-0 cursor-pointer rounded hover:border-base-content/50 hover:bg-base-300 transition-colors"
          >
            <XMarkIcon className="h-3 w-3 inline" />
          </button>
        )}
      </div>

      {/* Node List */}
      <div className="flex-1 overflow-y-auto">
        {filteredBlocks.length > 0 ? (
          <div className="px-2 pt-2 pb-4">
            {(() => {
              // Group blocks by primary category
              const groupedBlocks = filteredBlocks.reduce((acc, block) => {
                const primary = block.type === "subgraph" 
                  ? "My Subgraphs" 
                  : (block as any).metadata?.primary || "Other";
                if (!acc[primary]) acc[primary] = [];
                acc[primary].push(block);
                return acc;
              }, {} as Record<string, typeof filteredBlocks>);

              // Sort categories alphabetically
              const sortedCategories = Object.keys(groupedBlocks).sort();

              return sortedCategories.map((category, categoryIndex) => (
                <div key={category} className={categoryIndex > 0 ? "mt-6" : ""}>
                  {/* Category Header */}
                  <div className="mb-3">
                    <h3 className="text-sm font-vt323 uppercase tracking-wider text-primary/70 border-b border-primary/30 pb-1">
                      {category}
                    </h3>
                  </div>

                  {/* Category Blocks */}
                  <div className="space-y-2">
                    {groupedBlocks[category].map((block) => (
                      <div
                        key={block.type === "subgraph" ? block.id : block.name}
                        draggable
                        onDragStart={(e) => handleDragStart(e, block)}
                        onDragEnd={handleDragEnd}
                        onClick={() => handleBlockSelect(block)}
                        className={`
                          group relative p-2 rounded cursor-grab active:cursor-grabbing
                          border border-primary bg-base-200
                          hover:shadow-[1px_1px_0px_0px] hover:shadow-primary/60
                          hover:-translate-x-0.5 hover:-translate-y-0.5
                          active:translate-x-0.5 active:translate-y-0.5
                          transition-all duration-150 ease-in-out
                          ${draggedItem?.type === block.type ? "opacity-50 scale-95" : ""}
                          flex flex-col
                        `}
                      >
                        <div className="flex items-center gap-1.5">
                          <h3 className="font-medium text-sm text-primary group-hover:text-accent transition-colors">
                            {block.name}
                          </h3>
                          {(block as any).metadata?.secondary && (
                            <span className="text-[10px] text-base-content/50 font-mono">
                              ·{(block as any).metadata.secondary}
                            </span>
                          )}
                        </div>
                        {(block as any).description && (
                          <p className="text-xs text-base-content/70 mt-0.5">
                            {(block as any).description}
                          </p>
                        )}
                        <div className="absolute -top-1 -right-1 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 bg-base-300 p-1 rounded-sm">
                          <div className="text-[10px] text-accent font-vt323 bg-base-300 px-1 rounded-sm border border-accent/30">
                            Click = Origin
                          </div>
                          <div className="text-[10px] text-primary font-vt323 bg-base-300 px-1 rounded-sm border border-primary/30">
                            Drag = Place
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ));
            })()}
          </div>
        ) : (
          <div className="text-center py-12">
            <CircleStackIcon className="h-16 w-16 text-base-content/30 mx-auto mb-4" />
            <p className="text-base-content/50 font-medium">
              {searchQuery
                ? "No nodes match your search"
                : "No nodes available"}
            </p>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="mt-2 text-primary hover:text-accent transition-colors font-medium"
              >
                Clear search
              </button>
            )}
          </div>
        )}
      </div>


    </div>
  );
}
