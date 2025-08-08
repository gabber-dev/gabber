import {
  Background,
  BackgroundVariant,
  FinalConnectionState,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import { useStateMachine } from "./useStateMachine";
import { StateMachineStateBlock } from "./StateMachineStateBlock";
import { useCallback } from "react";

export function StateMachineGraphEdit() {
  return (
    <ReactFlowProvider>
      <Inner />
    </ReactFlowProvider>
  );
}

function Inner() {
  const {
    reactFlowRepresentation,
    handleEdgeChanges,
    handleNodeChanges,
    addStateAndTransition,
    addTransition,
  } = useStateMachine();
  const { screenToFlowPosition } = useReactFlow();

  const onConnectEnd = useCallback(
    (event: MouseEvent | TouchEvent, connectionState: FinalConnectionState) => {
      // when a connection is dropped on the pane it's not valid
      if (!connectionState.isValid) {
        // we need to remove the wrapper bounds, in order to get the correct position
        const { clientX, clientY } =
          "changedTouches" in event ? event.changedTouches[0] : event;
        const position = screenToFlowPosition({
          x: clientX,
          y: clientY,
        });

        if (!connectionState.fromNode) {
          console.warn("No fromNode in connection state");
          return;
        }

        addStateAndTransition(connectionState.fromNode.id, position);
      } else {
        if (!connectionState.fromNode || !connectionState.toNode) {
          console.warn("Invalid connection state, missing fromNode or toNode");
          return;
        }
        addTransition(connectionState.fromNode.id, connectionState.toNode.id);
      }
    },
    [addStateAndTransition, addTransition, screenToFlowPosition],
  );
  return (
    <ReactFlow
      className="h-full w-full bg-base-300"
      nodes={reactFlowRepresentation.nodes}
      edges={reactFlowRepresentation.edges}
      onNodesChange={(changes) => {
        handleNodeChanges(changes);
      }}
      onEdgesChange={(changes) => {
        handleEdgeChanges(changes);
      }}
      onDragEnd={(event) => {
        console.log("Drag ended", event);
      }}
      onConnectEnd={onConnectEnd}
      fitView
      nodeTypes={{ default: StateMachineStateBlock }}
      snapGrid={[12, 12]}
      snapToGrid={true}
      proOptions={{
        hideAttribution: true,
      }}
    >
      <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
    </ReactFlow>
  );
}
