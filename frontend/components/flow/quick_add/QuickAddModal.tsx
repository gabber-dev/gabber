import { EligibleLibraryItem } from "@/generated/editor";
import { useEditor } from "@/hooks/useEditor";
import { useCallback, useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

type Props = {
  sourceNode: string;
  sourcePad: string;
  addPosition: { x: number; y: number };
  close: () => void;
};
export function QuickAddModal({
  sourceNode,
  sourcePad,
  addPosition,
  close,
}: Props) {
  const { queryEligibleLibraryItems, addLibraryItem } = useEditor();
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
      console.log("Fetched eligible library items:", items);
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
    <div className="flex flex-col h-full w-full">
      <div>
        <button
          className="btn btn-sm btn-circle absolute right-2 top-2"
          onClick={close}
        >
          ✕
        </button>
        <h2 className="text-lg font-bold">Quick Add</h2>
        <p className="text-sm">Source Node: {sourceNode}</p>
        <p className="text-sm mb-4">Source Pad: {sourcePad}</p>
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
          <ul className="menu bg-base-200 rounded-box">
            {filteredItems.map((item, idx) => (
              <li key={idx}>
                <EligibleItem
                  item={item}
                  onPadClick={(padId: string) => {
                    addLibraryItem({
                      libraryItemId: item.library_item.id,
                      sourceNodeId: sourceNode,
                      sourcePadId: sourcePad,
                      targetPadId: padId,
                      position: addPosition,
                    })
                      .then(() => {
                        close();
                      })
                      .catch((error) => {
                        console.error("Error adding library item:", error);
                        toast.error("Failed to add item");
                      });
                  }}
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
  onPadClick: (padId: string) => void;
};

function EligibleItem({ item, onPadClick }: EligibleItemProps) {
  return (
    <div>
      <h3 className="font-semibold">{item.library_item.name}</h3>
      <p className="text-sm">Type: {item.library_item.type}</p>
      <div className="flex flex-wrap gap-2 mt-2">
        {item.pads.map((pad) => (
          <button
            key={pad.id}
            className="btn btn-xs btn-primary"
            onClick={() => onPadClick(pad.id)}
          >
            {pad.id}
          </button>
        ))}
      </div>
    </div>
  );
}
