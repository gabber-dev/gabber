import { useEditor } from "@/hooks/useEditor";
import { usePropertyPad } from "./blocks/components/pads/hooks/usePropertyPad";
import { useRun } from "@/hooks/useRun";
import { PadValue } from "@gabber/client-react";
import {} from "@/generated/editor";

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
  return null;
}
