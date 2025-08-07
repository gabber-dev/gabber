import { NodeEditorRepresentation } from "@/generated/editor";
import {
  Edge,
  EdgeChange,
  Node,
  NodeChange,
  useNodeId,
  useNodesData,
} from "@xyflow/react";
import { createContext, useCallback, useContext, useMemo } from "react";
import { usePropertyPad } from "../flow/blocks/components/pads/hooks/usePropertyPad";
import { v4 } from "uuid";
import {
  StateMachineConfiguration,
  StateMachineTransition,
} from "@/generated/stateMachine";

type StateMachineContextType = {
  handleNodeChanges: (changes: NodeChange[]) => void;
  handleEdgeChanges: (changes: EdgeChange[]) => void;
  addState: (name: string) => void;
  updateState: (oldName: string, newName: string) => void;
  deleteState: (name: string) => void;
  addTransition: (transition: StateMachineTransition) => void;
  updateTransition: (
    oldTransition: StateMachineTransition,
    newTransition: StateMachineTransition,
  ) => void;
  deleteTransition: (transitionId: string) => void;
  setEntryState: (state: string) => void;
  addParameter: () => void;
  removeParameter: () => void;
  addStateAndTransition: (
    source: string,
    newPosition: { x: number; y: number },
  ) => void;
  parameterPads: StateMachineParameterPads[];
  editorNode?: NodeEditorRepresentation;
  reactFlowRepresentation: { nodes: Node[]; edges: Edge[] };
};

const StateMachineContext = createContext<StateMachineContextType | undefined>(
  undefined,
);

export function StateMachineProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const nodeId = useNodeId();
  const node = useNodesData<Node<NodeEditorRepresentation>>(nodeId || "");
  const editorNode = node?.data;
  const { setEditorValue, editorValue } = usePropertyPad(
    nodeId || "",
    "num_parameters",
  );

  const { editorValue: configuration, setEditorValue: setConfiguration } =
    usePropertyPad<StateMachineConfiguration>(nodeId || "", "configuration");

  const addState = useCallback(
    (name: string) => {
      if (!configuration) {
        return;
      }
      setConfiguration({
        ...configuration,
        states: [
          ...(configuration.states || []),
          { name, position: { x: 0, y: 0 } },
        ],
      });
    },
    [configuration, setConfiguration],
  );

  const updateState = useCallback(
    (oldName: string, newName: string) => {
      if (!configuration) {
        return;
      }
      const updatedStates = configuration.states.map((state) =>
        state.name === oldName ? { ...state, name: newName } : state,
      );
      setConfiguration({ ...configuration, states: updatedStates });
    },
    [configuration, setConfiguration],
  );

  const deleteState = useCallback(
    (name: string) => {
      if (!configuration) {
        return;
      }
      const updatedStates = configuration.states.filter(
        (state) => state.name !== name,
      );
      setConfiguration({ ...configuration, states: updatedStates });
    },
    [configuration, setConfiguration],
  );

  const addTransition = useCallback(
    (transition: StateMachineTransition) => {
      if (!configuration) {
        return;
      }
      setConfiguration({
        ...configuration,
        transitions: [...(configuration.transitions || []), transition],
      });
    },
    [configuration, setConfiguration],
  );

  const updateTransition = useCallback(
    (
      oldTransition: StateMachineTransition,
      newTransition: StateMachineTransition,
    ) => {
      if (!configuration) {
        return;
      }
      const updatedTransitions = configuration.transitions.map((t) =>
        t.id === oldTransition.id ? newTransition : t,
      );
      setConfiguration({ ...configuration, transitions: updatedTransitions });
    },
    [configuration, setConfiguration],
  );

  const deleteTransition = useCallback(
    (transitionId: string) => {
      if (!configuration) {
        return;
      }
      const updatedTransitions = configuration.transitions.filter(
        (t) => t.id !== transitionId,
      );
      setConfiguration({ ...configuration, transitions: updatedTransitions });
    },
    [configuration, setConfiguration],
  );

  const setEntryState = useCallback(
    (state: string) => {
      if (!configuration) {
        return;
      }
      setConfiguration({ ...configuration, entry_state: state });
    },
    [configuration, setConfiguration],
  );

  const addParameter = useCallback(async () => {
    if (editorValue === undefined || typeof editorValue !== "number") {
      setEditorValue(1);
      return;
    }
    setEditorValue(editorValue + 1);
  }, [editorValue, setEditorValue]);

  const removeParameter = useCallback(async () => {
    if (editorValue === undefined || typeof editorValue !== "number") {
      return;
    }
    setEditorValue(editorValue - 1);
  }, [editorValue, setEditorValue]);

  const handleNodeChanges = useCallback(
    (changes: NodeChange[]) => {
      const prevConfiguration = configuration || {
        states: [],
        entry_state: "",
        entry_node_position: { x: 0, y: 0 },
        transitions: [],
      };

      for (const change of changes) {
        if (change.type === "position") {
          if (change.id === "__ENTRY__") {
            setConfiguration({
              ...prevConfiguration,
              entry_node_position: {
                x: change.position?.x || 0,
                y: change.position?.y || 0,
              },
            });
          } else {
            const updatedStates = prevConfiguration.states.map((state) =>
              state.name === change.id
                ? { ...state, position: change.position || { x: 0, y: 0 } }
                : state,
            );
            setConfiguration({ ...prevConfiguration, states: updatedStates });
          }
        } else if (change.type === "select") {
          if (change.id === "__ENTRY__") {
            continue;
          }
          const updatedStates = prevConfiguration.states.map((state) =>
            state.name === change.id
              ? { ...state, name: change.selected ? change.id : state.name }
              : state,
          );
          setConfiguration({ ...prevConfiguration, states: updatedStates });
        } else {
          console.warn("Unhandled node change type:", change.type);
        }
      }
    },
    [configuration, setConfiguration],
  );

  const addStateAndTransition = useCallback(
    (source: string, newPosition: { x: number; y: number }) => {
      const prevConfiguration = configuration || {
        states: [],
        entry_state: "",
        entry_node_position: { x: 0, y: 0 },
        transitions: [],
      };
      prevConfiguration.states.push({
        name: "New State",
        position: newPosition,
      });
      setConfiguration({
        ...prevConfiguration,
        states: prevConfiguration.states,
        transitions: [
          ...(prevConfiguration.transitions || []),
          {
            id: v4(),
            from_state: source,
            to_state: "New State",
            conditions: [],
          },
        ],
      });
    },
    [configuration, setConfiguration],
  );

  const handleEdgeChanges = useCallback((changes: EdgeChange[]) => {
    console.log("Edge changes:", changes);
    // Handle edge changes here
  }, []);

  const reactFlowRepresentation = useMemo(() => {
    const entryNode: Node = {
      id: "__ENTRY__",
      type: "default",
      position: {
        x: configuration?.entry_node_position?.x || 0,
        y: configuration?.entry_node_position?.y || 0,
      },
      measured: { width: 10, height: 10 },
      data: {},
    };
    const nodes = [entryNode];
    for (const state of configuration?.states || []) {
      nodes.push({
        id: state.name,
        type: "default",
        position: state.position,
        measured: { width: 10, height: 10 },
        data: {},
      });
    }

    const edges: Edge[] = [];

    if (configuration?.entry_state) {
      edges.push({
        id: `__ENTRY__-${configuration.entry_state}`,
        source: "__ENTRY__",
        target: configuration.entry_state,
        type: "default",
      });
    }

    return { nodes, edges };
  }, [
    configuration?.entry_node_position?.x,
    configuration?.entry_node_position?.y,
    configuration?.entry_state,
    configuration?.states,
  ]);

  const parameterPads = useMemo(() => {
    const allParamPads =
      editorNode?.pads.filter((pad) => pad.id.startsWith("parameter_")) || [];

    const res: StateMachineParameterPads[] = [];

    for (let i = 0; i < allParamPads.length; i += 2) {
      res.push({
        namePadId: allParamPads[i].id,
        valuePadId: allParamPads[i + 1]?.id,
      });
    }
    return res;
  }, [editorNode]);

  return (
    <StateMachineContext.Provider
      value={{
        addState,
        updateState,
        deleteState,
        addTransition,
        updateTransition,
        deleteTransition,
        setEntryState,
        addParameter,
        removeParameter,
        handleNodeChanges,
        handleEdgeChanges,
        addStateAndTransition,
        parameterPads,
        reactFlowRepresentation,
        editorNode,
      }}
    >
      {children}
    </StateMachineContext.Provider>
  );
}

export function useStateMachine() {
  const context = useContext(StateMachineContext);
  if (!context) {
    throw new Error(
      "useStateMachine must be used within a StateMachineProvider",
    );
  }
  return context;
}

export type StateMachineParameterPads = {
  namePadId: string;
  valuePadId: string;
};
