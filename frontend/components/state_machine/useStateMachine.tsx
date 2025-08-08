import { BasePadType, NodeEditorRepresentation } from "@/generated/editor";
import {
  Edge,
  EdgeChange,
  Node,
  NodeChange,
  useNodesData,
} from "@xyflow/react";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { usePropertyPad } from "../flow/blocks/components/pads/hooks/usePropertyPad";
import { v4 } from "uuid";
import {
  StateMachineConfiguration,
  StateMachineState,
  StateMachineTransition,
} from "@/generated/stateMachine";

type StateMachineContextType = {
  handleNodeChanges: (changes: NodeChange[]) => void;
  handleEdgeChanges: (changes: EdgeChange[]) => void;
  updateState: (id: string, name: string) => void;
  deleteState: (id: string) => void;
  addTransition: (source: string, target: string) => void;
  updateTransition: (id: string, newTransition: StateMachineTransition) => void;
  deleteTransition: (transitionId: string) => void;
  setEntryState: (state: string) => void;
  addParameter: () => void;
  removeParameter: () => void;
  addStateAndTransition: (
    source: string,
    newPosition: { x: number; y: number },
  ) => void;
  selectedNodes: string[];
  parameterPads: StateMachineParameterPads[];
  editorNode?: NodeEditorRepresentation;
  reactFlowRepresentation: { nodes: Node[]; edges: Edge[] };
  editingTransition?: {
    transition: StateMachineTransition;
    fromState: StateMachineState;
    toState: StateMachineState;
  };
  setEditingTransition?: (transitionId: string) => void;
};

const StateMachineContext = createContext<StateMachineContextType | undefined>(
  undefined,
);

type Props = {
  nodeId: string;
  children: React.ReactNode;
};

export function StateMachineProvider({ children, nodeId }: Props) {
  const node = useNodesData<Node<NodeEditorRepresentation>>(nodeId || "");
  const editorNode = node?.data;
  const { setEditorValue, editorValue } = usePropertyPad(
    nodeId || "",
    "num_parameters",
  );
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [editingTransitionId, setEditingTransitionId] = useState<
    string | undefined
  >(undefined);

  const { editorValue: configuration, setEditorValue: setConfiguration } =
    usePropertyPad<StateMachineConfiguration>(nodeId || "", "configuration");

  const updateState = useCallback(
    (stateId: string, newName: string) => {
      if (!configuration) {
        return;
      }
      const updatedStates = configuration.states.map((state) =>
        state.id === stateId ? { ...state, name: newName } : state,
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
    (source: string, target: string) => {
      if (!configuration) {
        return;
      }
      const newTransition: StateMachineTransition = {
        id: v4(),
        from_state: source,
        to_state: target,
      };
      setConfiguration({
        ...configuration,
        transitions: [...(configuration.transitions || []), newTransition],
      });
    },
    [configuration, setConfiguration],
  );

  const updateTransition = useCallback(
    (id: string, newTransition: StateMachineTransition) => {
      if (!configuration) {
        return;
      }
      const updatedTransitions = configuration.transitions.map((t) =>
        t.id === id ? newTransition : t,
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
              state.id === change.id
                ? { ...state, position: change.position || { x: 0, y: 0 } }
                : state,
            );
            setConfiguration({ ...prevConfiguration, states: updatedStates });
          }
        } else if (change.type === "select") {
          if (change.id === "__ENTRY__") {
            continue;
          }
          if (change.selected) {
            setSelectedNodes((prev) => [...prev, change.id]);
          } else {
            setSelectedNodes((prev) => prev.filter((id) => id !== change.id));
          }
        } else if (change.type === "remove") {
          if (change.id === "__ENTRY__") {
            console.warn("Cannot remove entry node");
            continue;
          }
          const updatedStates = prevConfiguration.states.filter(
            (state) => state.id !== change.id,
          );
          setConfiguration({
            ...prevConfiguration,
            states: updatedStates,
          });
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
      const newState: StateMachineState = {
        id: v4(),
        name: "New State",
        position: newPosition,
      };
      prevConfiguration.states.push(newState);

      if (source === "__ENTRY__") {
        setConfiguration({
          ...prevConfiguration,
          entry_state: newState.id,
        });
        return;
      }

      setConfiguration({
        ...prevConfiguration,
        states: prevConfiguration.states,
        transitions: [
          ...(prevConfiguration.transitions || []),
          {
            id: v4(),
            from_state: source,
            to_state: newState.id,
            conditions: [],
          },
        ],
      });
    },
    [configuration, setConfiguration],
  );

  const handleEdgeChanges = useCallback(
    (changes: EdgeChange[]) => {
      for (const change of changes) {
        if (change.type === "remove") {
          if (change.id.startsWith("__ENTRY__-")) {
            console.warn("Cannot remove entry state transition");
            continue;
          }
          const prevConfiguration = configuration || {
            states: [],
            entry_state: "",
            entry_node_position: { x: 0, y: 0 },
            transitions: [],
          };

          const updatedTransitions = prevConfiguration.transitions.filter(
            (t) => t.id !== change.id,
          );
          setConfiguration({
            ...prevConfiguration,
            transitions: updatedTransitions,
          });
        } else if (change.type === "select") {
          if (change.selected) {
            setEditingTransitionId(change.id);
          } else {
            setEditingTransitionId(undefined);
          }
        }
      }
      console.log("Edge changes:", changes);
      // Handle edge changes here
    },
    [configuration, setConfiguration],
  );

  const editingTransition = useMemo(() => {
    if (!editingTransitionId || !configuration) {
      return undefined;
    }
    const transition = configuration.transitions.find(
      (t) => t.id === editingTransitionId,
    );
    if (!transition) {
      return undefined;
    }
    const fromState = configuration.states.find(
      (s) => s.id === transition.from_state,
    );
    const toState = configuration.states.find(
      (s) => s.id === transition.to_state,
    );
    if (!fromState || !toState) {
      return undefined;
    }
    return { transition, fromState, toState };
  }, [editingTransitionId, configuration]);

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
        id: state.id,
        type: "default",
        position: state.position,
        measured: { width: 10, height: 10 },
        data: state,
        selected: selectedNodes.includes(state.id),
      });
    }

    const edges: Edge[] = [];

    if (configuration?.entry_state) {
      edges.push({
        id: "entry_edge",
        source: "__ENTRY__",
        target: configuration.entry_state,
        type: "default",
      });
    }

    for (const transition of configuration?.transitions || []) {
      edges.push({
        id: transition.id,
        source: transition.from_state,
        target: transition.to_state,
        type: "default",
        selected: editingTransition?.transition.id === transition.id,
      });
    }

    return { nodes, edges };
  }, [
    configuration?.entry_node_position?.x,
    configuration?.entry_node_position?.y,
    configuration?.entry_state,
    configuration?.states,
    configuration?.transitions,
    editingTransition?.transition.id,
    selectedNodes,
  ]);

  const parameterPads = useMemo(() => {
    const namePads =
      editorNode?.pads.filter((pad) => pad.id.startsWith("parameter_name_")) ||
      [];

    const valuePads =
      editorNode?.pads.filter((pad) => pad.id.startsWith("parameter_value_")) ||
      [];

    const res: StateMachineParameterPads[] = [];

    for (let i = 0; i < namePads.length; i += 1) {
      const tcs = valuePads[i]?.allowed_types;
      console.log("NEIL Parameter pads:", namePads[i], valuePads[i], tcs);
      let valueType: BasePadType | undefined = undefined;
      if (tcs?.length === 1) {
        valueType = tcs[0];
      }
      res.push({
        namePadId: namePads[i].id,
        nameValue: namePads[i].value as string,
        valuePadId: valuePads[i]?.id,
        valueType,
      });
    }
    return res;
  }, [editorNode]);

  return (
    <StateMachineContext.Provider
      value={{
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
        editingTransition,
        selectedNodes,
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
  nameValue: string;
  valuePadId: string;
  valueType: BasePadType | undefined;
};
