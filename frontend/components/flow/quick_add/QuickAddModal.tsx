/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { EligibleLibraryItem, PortalEnd } from "@/generated/editor";
import { useEditor } from "@/hooks/useEditor";
import { useCallback, useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { v4 } from "uuid";

type PortalInfo = {
  portalId: string;
  portalEnd: PortalEnd;
};
export type QuickAddProps = {
  sourceNode: string;
  sourcePad: string;
  portalInfo?: PortalInfo;
  addPosition: { x: number; y: number };
  close: () => void;
};
export function QuickAddModal({
  sourceNode,
  sourcePad,
  addPosition,
  portalInfo,
  close,
}: QuickAddProps) {
  const { queryEligibleLibraryItems } = useEditor();
  const [eligibleItems, setEligibleItems] = useState<
    EligibleLibraryItem[] | undefined
  >(undefined);
  const [searchQuery, setSearchQuery] = useState("");
  const loadingRef = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const fetchItems = useCallback(async () => {
    if (!sourceNode || !sourcePad) return;
    if (loadingRef.current) return;
    loadingRef.current = true;
    try {
      const items = await queryEligibleLibraryItems({
        sourceNode,
        sourcePad,
      });
      setEligibleItems(items);
    } catch (error) {
      toast.error("Error fetching eligible library items");
      console.error("Error fetching eligible library items:", error);
    } finally {
      loadingRef.current = false;
    }
  }, [queryEligibleLibraryItems, sourceNode, sourcePad]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems, queryEligibleLibraryItems, sourceNode, sourcePad]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  function fuzzyMatch(str: string, query: string): boolean {
    str = str.toLowerCase();
    query = query.toLowerCase();
    let i = 0;
    for (const char of str) {
      if (char === query[i]) i++;
      if (i === query.length) return true;
    }
    return false;
  }

  const filteredItems =
    eligibleItems?.filter((item) =>
      fuzzyMatch(item.library_item.name, searchQuery),
    ) || [];

  return (
    <div className="flex flex-col h-full w-full p-2">
      <div className="w-full flex items-center justify-center">
        {portalInfo === undefined && (
          <CreatePortalButton
            addPosition={addPosition}
            fromNodeId={sourceNode}
            fromPadId={sourcePad}
            close={close}
          />
        )}
      </div>
      <div className="divider">Eligible Nodes</div>
      <div>
        <button
          className="btn btn-sm btn-circle absolute right-2 top-2"
          onClick={close}
        >
          ✕
        </button>
        <input
          ref={inputRef}
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input input-bordered w-full mb-4"
          placeholder="Search items..."
        />
      </div>
      <div className="flex flex-col overflow-y-auto">
        {eligibleItems === undefined ? (
          <p className="text-center">Loading...</p>
        ) : filteredItems.length === 0 ? (
          <p className="text-center">No matching items found.</p>
        ) : (
          <ul className="bg-base-200 rounded-box">
            {filteredItems.map((item, idx) => (
              <li key={idx} className="p-2 hover:bg-base-300">
                <EligibleItem
                  item={item}
                  sourceNodeId={sourceNode}
                  sourcePadId={sourcePad}
                  addPosition={addPosition}
                  portalInfo={portalInfo}
                  close={close}
                />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

type EligibleItemProps = {
  item: EligibleLibraryItem;
  sourceNodeId: string;
  sourcePadId: string;
  addPosition: { x: number; y: number };
  portalInfo?: PortalInfo;
  close: () => void;
};

function EligibleItem({
  item,
  sourceNodeId,
  sourcePadId,
  addPosition,
  portalInfo,
  close,
}: EligibleItemProps) {
  const { insertNode, connectPad, updatePortalEnd } = useEditor();
  return (
    <div>
      <div className="flex items-center">
        <h3 className="font-semibold">{item.library_item.name}</h3>
        <span className="ml-2 text-xs italic text-gray-500">
          ({item.library_item.type})
        </span>
      </div>
      <div className="flex flex-wrap gap-1 mt-1">
        {item.pads.map((pad) => (
          <button
            key={pad.id}
            onClick={() => {
              if (item.library_item.type === "node") {
                const id =
                  `${item.library_item.name}_${v4().toString().slice(0, 8)}`.toLowerCase();
                insertNode({
                  id: id,
                  data: { label: pad.id },
                  editor_position: [addPosition.x, addPosition.y],
                  editor_name: item.library_item.name,
                  node_type: item.library_item.name,
                  type: "insert_node",
                });
                connectPad({
                  node: sourceNodeId,
                  pad: sourcePadId,
                  type: "connect_pad",
                  connected_node: id,
                  connected_pad: pad.id,
                });
                if (portalInfo) {
                  updatePortalEnd({
                    type: "update_portal_end",
                    portal_id: portalInfo.portalId,
                    portal_end_id: portalInfo.portalEnd.id,
                    next_pads: [
                      ...portalInfo.portalEnd.next_pads,
                      { node: id, pad: pad.id },
                    ],
                    editor_position: portalInfo.portalEnd.editor_position,
                  });
                }
                close();
              }
            }}
            className="btn btn-xs btn-primary"
          >
            {pad.id}
          </button>
        ))}
      </div>
    </div>
  );
}

function CreatePortalButton({
  addPosition,
  fromNodeId,
  fromPadId,
  close,
}: {
  addPosition: { x: number; y: number };
  fromNodeId: string;
  fromPadId: string;
  close: () => void;
}) {
  const { createPortal } = useEditor();
  return (
    <button
      onClick={() => {
        createPortal({
          editor_position: [addPosition?.x || 0, addPosition?.y || 0],
          source_node: fromNodeId,
          source_pad: fromPadId,
          type: "create_portal",
        });
        close();
      }}
      className="btn btn-primary btn-sm gap-2"
    >
      Create Portal
    </button>
  );
}
