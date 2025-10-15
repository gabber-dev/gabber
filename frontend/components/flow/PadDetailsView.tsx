import { useEditor } from "@/hooks/useEditor";
import { usePropertyPad } from "./blocks/components/pads/hooks/usePropertyPad";
import { useRun } from "@/hooks/useRun";
import { PadValue } from "@gabber/client-react";
import {
  PadValue_ContextMessageContentItem,
  PadValue_List,
} from "@gabber/client/dist/generated/runtime";
import { PadType } from "@/generated/editor";

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
  const { connectionState } = useRun();
  const { editorValue, runtimeValue, singleAllowedType } = usePropertyPad<
    PadValue | unknown
  >(nodeId, padId);
  if (connectionState === "connected") {
    console.log("PadDetailsViewInnerProperty runtimeValue:", runtimeValue);
    const rv = runtimeValue as PadValue;
    if (rv?.type === "list") {
      return <ListPadView value={rv} singleAllowedType={singleAllowedType} />;
    }
  } else {
    if (Array.isArray(editorValue)) {
      return (
        <ListPadView
          value={editorValue}
          singleAllowedType={singleAllowedType}
        />
      );
    }
  }

  return <div className="w-full h-full">Property Pad View</div>;
}

type ContextMessageProps = {
  role: string;
  content: PadValue_ContextMessageContentItem[];
};

function ListPadView({
  value,
  singleAllowedType,
}: {
  value: Array<unknown> | PadValue_List;
  singleAllowedType?: PadType;
}) {
  if (!singleAllowedType) {
    return <div className="w-full h-full">List Pad View - Unknown type</div>;
  }
  const items = Array.isArray(value) ? value : value.items || [];
  const count = Array.isArray(value) ? value.length : value.count || 0;
  return (
    <div className="w-full h-full">List Pad View - {items.length} items</div>
  );
}

function ContextMessage({ role, content }: ContextMessageProps) {
  return (
    <div>
      <div className="badge">{role}</div>
    </div>
  );
}
