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
import ReactModal from "react-modal";
import { StateMachineTransitionEdit } from "./StateMachineTransitionEdit";
import StateMachineEdge from "./StateMachineEdge";
import StateMachineConnectionLine from "./StateMachineConnectionLine";

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
    editingTransition,
    setEditingTransition,
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
    <div className="relative h-full w-full">
      <ReactFlow
        className="h-full w-full bg-base-300"
        nodes={reactFlowRepresentation.nodes}
        edges={reactFlowRepresentation.edges}
<<<<<<< HEAD
        edgeTypes={{ default: StateMachineEdge }}
        connectionLineComponent={StateMachineConnectionLine}
=======
>>>>>>> neil/sm
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
<<<<<<< HEAD
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-base-content/60 bg-base-200/70 px-2 py-1 rounded-md pointer-events-none select-none">
        Drag off the entry node to create the initial state. Drag off a state to create next possible states. Transitions are created automatically; click the filter icon on an edge to configure parameters.
      </div>
=======
>>>>>>> neil/sm
      <div
        className={`absolute top-0 right-0 h-full w-100 bg-base-200 shadow-lg transition-all duration-300 z-50 p-2 ${
          editingTransition ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <StateMachineTransitionEdit />
      </div>
    </div>
  );
}
