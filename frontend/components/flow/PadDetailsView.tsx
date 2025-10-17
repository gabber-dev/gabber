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
      <PadDetailsViewInnerProperty
        nodeId={detailedView.nodeId}
        padId={detailedView.padId}
      />
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
    return "No Data";
  }

  console.log("NEIL PadDetailsViewInnerProperty runtimeValue:", runtimeValue);

  return <Item item={runtimeValue} />;
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
    <div className="flex flex-col w-full h-full gap-1">
      {item.items.map((it, index) => (
        <div key={index} className="p-2 border-b border-base-300">
          <Item item={it} />
        </div>
      ))}
    </div>
  );
}

function ContextMessageItem({ item }: { item: ContextMessage }) {
  return (
    <div className="p-2 border-b border-base-300">
      <div className="font-bold">{item.role.value}</div>
      <div>
        {item.content.map((contentItem, index) => (
          <ContentItem key={index} item={contentItem} />
        ))}
      </div>
    </div>
  );
}

function ContentItem({ item }: { item: ContextMessageContentItem }) {
  if (item.content_type === "text") {
    return <div>{item.text}</div>;
  } else if (item.content_type === "image") {
    return <div>Image</div>;
  } else if (item.content_type === "audio") {
    return <div>Audio</div>;
  } else if (item.content_type === "video") {
    return <div>Video</div>;
  }
  return null;
}
