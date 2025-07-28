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
      setIsModalOpen(false);
    },
    [insertNode, insertSubGraph, setIsModalOpen],
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
      setIsModalOpen(false);
    },
    [
      draggedItem,
      insertNode,
      insertSubGraph,
      screenToFlowPosition,
      setIsModalOpen,
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
    <div className="w-full h-full p-4 bg-base-300 text-base-content overflow-hidden flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-vt323 uppercase tracking-wider text-primary">
          Node Library
        </h2>
        <p className="text-sm text-base-content/70 font-medium mb-2">
          Drag blocks onto the canvas or click to add at origin
        </p>
      </div>

      {/* Top Filters */}
      <div className="flex flex-nowrap gap-2 mb-4 overflow-x-auto">
        {/* Primary Category Select */}
        <div className="flex-shrink-0">
          <select
            value={selectedMainCategory || ""}
            onChange={(e) => {
              setSelectedMainCategory(e.target.value || null);
              setSelectedSubcategory1(null);
              setSelectedTag(null);
            }}
            className="border border-primary/30 bg-base-200 text-primary px-2 py-1 text-xs w-20 cursor-pointer rounded hover:border-primary/50 hover:bg-base-300 transition-colors"
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
              className="border border-accent/30 bg-base-200 text-accent px-2 py-1 text-xs w-20 cursor-pointer rounded hover:border-accent/50 hover:bg-base-300 transition-colors"
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
              className="border border-secondary/30 bg-base-200 text-secondary px-2 py-1 text-xs w-20 cursor-pointer rounded hover:border-secondary/50 hover:bg-base-300 transition-colors"
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
            className="border border-base-content/30 bg-base-200 text-base-content/70 hover:text-base-content px-2 py-1 text-xs w-16 flex-shrink-0 cursor-pointer rounded hover:border-base-content/50 hover:bg-base-300 transition-colors"
          >
            <XMarkIcon className="h-3 w-3 mr-1 inline" />
            Clear
          </button>
        )}
      </div>

      {/* Search input */}
      <div className="relative mb-6">
        <input
          type="text"
          placeholder="Search nodes by name, description, or tags..."
          value={searchQuery}
          onChange={handleSearchChange}
          className="w-full p-3 bg-base-100 border-2 border-primary/30 rounded-lg 
                     focus:outline-none focus:border-primary focus:shadow-[0_0_10px_rgba(252,211,77,0.3)]
                     transition-all duration-300 font-medium text-base-content
                     placeholder:text-base-content/50"
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <MagnifyingGlassIcon className="h-5 w-5 text-primary/50" />
        </div>
      </div>

      {/* Node List */}
      <div className="flex-1 overflow-y-auto pr-1">
        {filteredBlocks.length > 0 ? (
          <div className="space-y-3 p-2">
            {filteredBlocks.map((block) => {
              const metadata = (block as any).metadata;
              const tags = metadata?.tags || [];

              return (
                <div
                  key={block.type === "subgraph" ? block.id : block.name}
                  draggable
                  onDragStart={(e) => handleDragStart(e, block)}
                  onDragEnd={handleDragEnd}
                  onClick={() => handleBlockSelect(block)}
                  className={`
                    group relative p-4 rounded-lg cursor-grab active:cursor-grabbing
                    border-2 border-primary bg-base-200
                    hover:shadow-[2px_2px_0px_0px] hover:shadow-primary/60
                    hover:-translate-x-0.5 hover:-translate-y-0.5
                    active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_0px]
                    transition-all duration-150 ease-in-out
                    ${draggedItem?.type === block.type ? "opacity-50 scale-95" : ""}
                    ambient-float-delay
                    flex flex-col
                  `}
                >
                  {/* Header with title */}
                  <div className="flex items-start justify-between mb-2">
                    <h3
                      className={`
                        font-bold text-primary group-hover:text-accent transition-colors
                        ${block.name.length > 25 ? "text-sm" : "text-base"}
                        flex-1
                      `}
                    >
                      {block.name}
                    </h3>
                  </div>

                  {/* Description */}
                  {(block as any).description && (
                    <p className="text-sm text-base-content/70 leading-relaxed mb-3">
                      {(block as any).description}
                    </p>
                  )}

                  {/* Tags */}
                  {tags.length > 0 && (
                    <div className="flex items-center gap-1 mt-auto text-xs">
                      {tags.slice(0, 3).map((tag: string) => (
                        <span
                          key={tag}
                          className="px-1.5 py-0.5 rounded font-vt323 bg-accent/20 text-accent border border-accent/30"
                        >
                          {tag}
                        </span>
                      ))}
                      {tags.length > 3 && (
                        <span className="px-1.5 py-0.5 rounded font-vt323 bg-base-100 text-base-content border border-base-300">
                          +{tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Drag hint */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="text-xs text-primary font-vt323 uppercase bg-base-300 px-1 py-0.5 rounded border border-primary/30">
                      Drag
                    </div>
                  </div>

                  {/* Arcade-style corner decorations */}
                  <div className="absolute top-1 left-1 w-2 h-2 border-l-2 border-t-2 border-primary/30"></div>
                  <div className="absolute bottom-1 right-1 w-2 h-2 border-r-2 border-b-2 border-primary/30"></div>
                </div>
              );
            })}
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

      {/* Footer with instructions */}
      <div className="mt-4 pt-4 border-t border-primary/20">
        <div className="text-xs text-base-content/60 font-medium space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-accent rounded-full"></div>
            <span>Click to add at origin</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary rounded-full"></div>
            <span>Drag to position on canvas</span>
          </div>
        </div>
      </div>
    </div>
  );
}
