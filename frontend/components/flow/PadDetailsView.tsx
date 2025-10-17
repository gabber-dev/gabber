import { useEditor } from "@/hooks/useEditor";
import { usePropertyPad } from "./blocks/components/pads/hooks/usePropertyPad";
import { ContextMessage, List, PadValue } from "@gabber/client-react";
import { ContextMessageContentItem } from "@/generated/editor";
import { useEffect, useRef, useState } from "react";

export function PadDetailsView() {
  const { detailedView, setDetailedView } = useEditor();

  if (!detailedView) {
    return null;
  }

  if (detailedView.type === "property") {
    return (
      <div className="w-full h-full overflow-auto p-1 flex flex-col">
        <button
          className="btn btn-error self-end btn-sm"
          onClick={() => {
            setDetailedView(undefined);
          }}
        >
          Close
        </button>
        <div className="flex-1 overflow-auto">
          <PadDetailsViewInnerProperty
            nodeId={detailedView.nodeId}
            padId={detailedView.padId}
          />
        </div>
      </div>
    );
  } else if (detailedView.type === "stateless") {
    return null;
  }

  return null;
}

function PadDetailsViewInnerProperty({
  nodeId,
  padId,
}: {
  nodeId: string;
  padId: string;
}) {
  const { runtimeValue } = usePropertyPad<PadValue>(nodeId, padId);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (isAtBottom && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
    }
  }, [runtimeValue, isAtBottom]);

  // Handle scroll events to detect if user is at bottom
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } =
      scrollContainerRef.current;
    const isNearBottom = scrollTop + clientHeight >= scrollHeight - 10; // 10px threshold

    setIsAtBottom(isNearBottom);
    setShowScrollToBottom(!isNearBottom);
  };

  // Scroll to bottom function
  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
      setIsAtBottom(true);
      setShowScrollToBottom(false);
    }
  };

  if (!runtimeValue) {
    return <div className="alert alert-info">No Data</div>;
  }

  return (
    <div className="relative w-full h-full">
      <div
        ref={scrollContainerRef}
        className="w-full h-full overflow-auto"
        onScroll={handleScroll}
      >
        <div className="w-full card">
          <Item item={runtimeValue} />
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollToBottom && (
        <button
          className="fixed bottom-4 right-4 btn btn-primary btn-sm shadow-lg z-10"
          onClick={scrollToBottom}
        >
          ↓ Scroll to Bottom
        </button>
      )}
    </div>
  );
}

function Item({ item }: { item: PadValue }) {
  if (item?.type === "list") {
    return <ListItem item={item} />;
  } else if (item?.type === "context_message") {
    return <ContextMessageItem item={item} />;
  }
  return null;
}

function ListItem({ item }: { item: List }) {
  return (
    <div className="flex flex-col w-full gap-1">
      {item.items.map((it, index) => (
        <div key={index} className="">
          <Item item={it} />
        </div>
      ))}
    </div>
  );
}

function ContextMessageItem({ item }: { item: ContextMessage }) {
  const roleBadgeClass = getRoleBadgeClass(item.role.value);

  // Get unique content types for this message
  const contentTypes = [...new Set(item.content.map((c) => c.content_type))];

  return (
    <div className="relative flex flex-col p-2 bg-base-200 card">
      {/* Media type tags in top-right */}
      <div className="absolute top-2 right-2 flex gap-1 flex-wrap">
        {contentTypes.map((type) => {
          switch (type) {
            case "text":
              return (
                <div
                  key={type}
                  className="badge badge-neutral badge-sm font-semibold"
                >
                  TEXT
                </div>
              );
            case "image":
              return (
                <div
                  key={type}
                  className="badge badge-secondary badge-sm font-semibold"
                >
                  IMAGE
                </div>
              );
            case "audio":
              return (
                <div
                  key={type}
                  className="badge badge-accent badge-sm font-semibold"
                >
                  AUDIO
                </div>
              );
            case "video":
              return (
                <div
                  key={type}
                  className="badge badge-primary badge-sm font-semibold"
                >
                  VIDEO
                </div>
              );
            default:
              return null;
          }
        })}
      </div>

      <div className={`badge ${roleBadgeClass} text-xs`}>{item.role.value}</div>
      <div className="max-w-none pt-1 pr-20">
        {item.content.map((contentItem, index) => (
          <ContentItem key={index} item={contentItem} />
        ))}
      </div>
    </div>
  );
}

function getRoleBadgeClass(role: string): string {
  switch (role.toLowerCase()) {
    case "user":
      return "badge-primary";
    case "assistant":
      return "badge-success";
    case "system":
      return "badge-secondary";
    default:
      return "badge-info";
  }
}

function ContentItem({ item }: { item: ContextMessageContentItem }) {
  if (item.content_type === "text") {
    return <div className="mb-1">{item.text}</div>;
  } else if (item.content_type === "image") {
    return (
      <div className="flex flex-col items-center mb-1">
        <div className="flex gap-1 flex-wrap">
          <div>Time: {item.image?.timestamp || "N/A"}</div>
          <div className="badge badge-secondary badge-sm">
            W: {item.image?.width || "N/A"}
          </div>
          <div className="badge badge-secondary badge-sm">
            H: {item.image?.height || "N/A"}
          </div>
        </div>
      </div>
    );
  } else if (item.content_type === "audio") {
    return (
      <div className="flex flex-col gap-1 mb-1">
        <div className="flex gap-1 flex-wrap">
          <div className="badge badge-accent badge-sm">
            Dur: {item.audio?.duration || "N/A"}
          </div>
        </div>
        {item.audio?.transcription && (
          <div className="p-1 bg-base-200 rounded-box">
            <span className="font-mono text-xs">
              {item.audio?.transcription}
            </span>
          </div>
        )}
      </div>
    );
  } else if (item.content_type === "video") {
    return (
      <div className="flex flex-col items-center gap-1 mb-1">
        <div className="flex gap-1 flex-wrap">
          <div className="badge badge-info badge-sm">
            W: {item.video?.width || "N/A"}
          </div>
          <div className="badge badge-info badge-sm">
            H: {item.video?.height || "N/A"}
          </div>
          <div className="badge badge-info badge-sm">
            Dur:{" "}
            {item.video?.duration
              ? Math.round(item.video.duration * 100) / 100
              : "N/A"}
          </div>
          <div className="badge badge-info badge-sm">
            Frames: {item.video?.frame_count || "N/A"}
          </div>
        </div>
      </div>
    );
  }
  return null;
}
