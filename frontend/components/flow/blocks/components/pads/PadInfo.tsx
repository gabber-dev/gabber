import { NodeNote, PadEditorRepresentation } from "@/generated/editor";

type Props = {
  data: PadEditorRepresentation;
  direction: "source" | "sink";
  allowedTypeNames: string[] | null;
  notes: NodeNote[];
};
export function PadInfo({ data, direction, allowedTypeNames, notes }: Props) {
  const getIcon = (level: string) => {
    switch (level) {
      case "info":
        return "ℹ️";
      case "warning":
        return "⚠️";
      case "error":
        return "❌";
      default:
        return "ℹ️";
    }
  };

  return (
    <div>
      <div className="space-y-2">
        <div className="border-b border-primary/30 pb-2">
          <h3 className="text-accent font-medium">Pad Info</h3>
        </div>
        <div className="space-y-1">
          <div className="flex justify-between items-start">
            <span className="text-primary font-medium text-xs">ID:</span>
            <span className="text-accent text-xs break-all ml-2">
              {data.id}
            </span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-primary font-medium text-xs">Type:</span>
            <span className="text-accent text-xs break-all ml-2">
              {data.type}
            </span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-primary font-medium text-xs">Direction:</span>
            <span className="text-accent text-xs break-all ml-2">
              {direction}
            </span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-primary font-medium text-xs">Allowed:</span>
            <div className="flex flex-wrap gap-1 ml-2">
              {allowedTypeNames === null && (
                <span className="text-accent text-xs">ANY</span>
              )}
              {allowedTypeNames !== null &&
                allowedTypeNames.length > 0 &&
                allowedTypeNames.map((name, idx) => (
                  <span
                    key={idx}
                    className="border rounded-sm text-xs px-1 text-accent break-normal"
                  >
                    {name}
                  </span>
                ))}
              {allowedTypeNames !== null && allowedTypeNames.length === 0 && (
                <span className="text-accent text-xs">NONE</span>
              )}
            </div>
          </div>
        </div>
        {notes.length > 0 && (
          <div className="space-y-1 pt-2 border-t border-primary/30">
            <div className="space-y-1">
              {notes.map((note, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-xs flex-shrink-0 mt-0.5">
                    {getIcon(note.level)}
                  </span>
                  <span className="text-accent text-xs break-words">
                    {note.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
