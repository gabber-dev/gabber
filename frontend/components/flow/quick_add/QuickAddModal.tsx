import { useEditor } from "@/hooks/useEditor";

type Props = {
  source_node: string;
  source_pad: string;
  add_position: { x: number; y: number };
  close: () => void;
};
export function QuickAddModal({
  source_node,
  source_pad,
  add_position,
  close,
}: Props) {
  const {} = useEditor();
  return (
    <div>
      <h2>Quick Add</h2>
      <p>Source Node: {source_node}</p>
      <p>Source Pad: {source_pad}</p>
    </div>
  );
}
