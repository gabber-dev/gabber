/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

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
  useEffect,
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
    fromName: string;
    toName: string;
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
  // Local RF nodes buffer for smooth drag visual updates
  const [rfRepresentation, setRfRepresentation] = useState<{
    nodes: Node[];
    edges: Edge[];
  }>({ nodes: [], edges: [] });

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
      if (source === "__ENTRY__") {
        setConfiguration({
          ...configuration,
          entry_state: target,
        });
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
      console.log("Updating transition", id, newTransition.conditions);
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
          if (change.dragging) {
            setRfRepresentation((prev) => ({
              ...prev,
              nodes: prev.nodes.map((node) =>
                node.id === change.id
                  ? {
                      ...node,
                      position: change.position || { x: 0, y: 0 },
                      measured: { width: 20, height: 20 },
                    }
                  : node,
              ),
            }));
          } else {
            // Commit final position to configuration on drop
            if (change.id === "__ENTRY__") {
              setConfiguration({
                ...prevConfiguration,
                entry_node_position: {
                  x: change.position?.x || 0,
                  y: change.position?.y || 0,
                },
              });
            } else if (change.id === "__ANY__") {
              setConfiguration({
                ...prevConfiguration,
                special_any_state_position: {
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
          }
        } else if (change.type === "select") {
          if (change.id === "__ENTRY__" || change.id === "__ANY__") {
            continue;
          }
          if (change.selected) {
            setSelectedNodes((prev) => [...prev, change.id]);
          } else {
            setSelectedNodes((prev) => prev.filter((id) => id !== change.id));
          }
        } else if (change.type === "remove") {
          if (change.id === "__ENTRY__" || change.id === "__ANY__") {
            console.warn("Cannot remove ENTRY node or ANY node");
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
    let fromName = fromState?.name;
    if (transition.from_state === "__ANY__") {
      fromName = "Any";
    }
    if (fromName === undefined) {
      return undefined;
    }

    const toState = configuration.states.find(
      (s) => s.id === transition.to_state,
    );
    const toName = toState?.name;
    if (toName === undefined) {
      return undefined;
    }
    return { transition, fromName, toName };
  }, [editingTransitionId, configuration]);

  useEffect(() => {
    setRfRepresentation(
      configToRF(configuration, selectedNodes, editingTransition?.transition),
    );
  }, [
    configuration?.states,
    configuration?.entry_node_position?.x,
    configuration?.entry_node_position?.y,
    selectedNodes,
    configuration,
    editingTransition?.transition,
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
        reactFlowRepresentation: rfRepresentation,
        editorNode,
        setEditingTransition: setEditingTransitionId,
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

function configToRF(
  config: StateMachineConfiguration | undefined,
  selectedNodes: string[],
  editingTransition: StateMachineTransition | undefined,
): {
  nodes: Node[];
  edges: Edge[];
} {
  const entryNode: Node = {
    id: "__ENTRY__",
    type: "default",
    position: {
      x: config?.entry_node_position?.x ?? 0,
      y: config?.entry_node_position?.y ?? 0,
    },
    data: {},
  };
  const specialAnyNode: Node = {
    id: "__ANY__",
    type: "default",
    position: config?.special_any_state_position || { x: 0, y: 0 },
    data: {},
    selected: false,
  };

  const nodes = [entryNode, specialAnyNode];
  for (const state of config?.states || []) {
    nodes.push({
      id: state.id,
      type: "default",
      position: state.position,
      data: state,
      selected: selectedNodes.includes(state.id),
    });
  }

  const edges: Edge[] = [];

  if (config?.entry_state) {
    edges.push({
      id: "entry_edge",
      source: "__ENTRY__",
      target: config.entry_state,
      type: "default",
    });
  }

  for (const transition of config?.transitions || []) {
    edges.push({
      id: transition.id,
      source: transition.from_state,
      target: transition.to_state,
      type: "default",
      selected: editingTransition?.id === transition.id,
    });
  }

  return { nodes, edges };
}
