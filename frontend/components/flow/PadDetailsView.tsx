import { useEditor } from "@/hooks/useEditor";
import { usePropertyPad } from "./blocks/components/pads/hooks/usePropertyPad";
import { ContextMessage, List, PadValue } from "@gabber/client-react";
import { ContextMessageContentItem } from "@/generated/editor";

export function PadDetailsView() {
  const { detailedView } = useEditor();

  if (!detailedView) {
    return null;
  }

  if (detailedView.type === "property") {
    return (
      <div className="w-full h-full overflow-auto p-1">
        <PadDetailsViewInnerProperty
          nodeId={detailedView.nodeId}
          padId={detailedView.padId}
        />
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
  if (!runtimeValue) {
    return <div className="alert alert-info">No Data</div>;
  }

  return (
    <div className="w-full card">
      <Item item={runtimeValue} />
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

  return (
    <div className="flex flex-col p-2 bg-base-200 card">
      <div className={`badge ${roleBadgeClass} text-xs`}>{item.role.value}</div>
      <div className="max-w-none pt-1">
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
        Image
        <div className="flex gap-1">
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
        <div className="flex gap-1">
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
        <div className="mockup-browser border p-2">
          <video className="w-48" controls>
            <track kind="captions" />
            Your browser does not support the video tag.
          </video>
        </div>
        <div className="flex gap-1 flex-wrap">
          <div className="badge badge-info badge-sm">
            W: {item.video?.width || "N/A"}
          </div>
          <div className="badge badge-info badge-sm">
            H: {item.video?.height || "N/A"}
          </div>
          <div className="badge badge-info badge-sm">
            Dur: {item.video?.duration || "N/A"}
          </div>
        </div>
      </div>
    );
  }
  return null;
}
