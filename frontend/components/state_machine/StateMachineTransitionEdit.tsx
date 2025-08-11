import {
  ArrowRightIcon,
  MinusIcon,
  PlusIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import { useStateMachine } from "./useStateMachine";
import {
  Operator,
  StateMachineTransition,
  StateMachineTransitionCondition,
} from "@/generated/stateMachine";
import { useMemo, useState } from "react";

export function StateMachineTransitionEdit() {
  const { editingTransition, updateTransition } = useStateMachine();
  const { transition, fromState, toState } = editingTransition || {};
  if (!editingTransition) {
    return null;
  }
  return (
    <div className="flex h-full w-full flex-col gap-2">
      <div className="border-b w-full flex flex-col gap-2 items-center">
        <h2 className="text-lg font-bold">Editing Transition</h2>
        <div className="flex items-center gap-2 mb-4">
          <span className="badge badge-primary">{fromState?.name}</span>
          <ArrowRightIcon className="w-5 h-5 text-base-content" />
          <span className="badge badge-primary">{toState?.name}</span>
        </div>
      </div>

      <div className="flex gap-2">
        <h3 className="text-lg font-semibold mb-2">Conditions:</h3>
      </div>
      <div className="flex flex-col gap-2 w-full overflow-y-auto overflow-x-hidden">
        {transition?.conditions ? (
          transition.conditions.map((condition, idx) => (
            <Condition
              key={idx}
              condition={condition}
              conditionIdx={idx}
              transition={transition}
            />
          ))
        ) : (
          <p className="text-gray-500 italic">No conditions available.</p>
        )}
      </div>
      <button
        className="btn btn-sm btn-primary"
        onClick={() => {
          updateTransition(editingTransition.transition.id, {
            ...editingTransition.transition,
            conditions: [
              ...(editingTransition.transition.conditions || []),
              {
                parameter_name: null,
                operator: null,
                value: null,
              },
            ],
          });
        }}
      >
        Add Condition
      </button>
    </div>
  );
}

function Condition({
  condition,
  conditionIdx,
  transition,
}: {
  condition: StateMachineTransitionCondition;
  conditionIdx: number;
  transition: StateMachineTransition;
}) {
  const { parameterPads, updateTransition } = useStateMachine();
  const selectedPad = useMemo(() => {
    if (!condition.parameter_name) return undefined;
    return parameterPads.find(
      (pad) => pad.nameValue === condition.parameter_name,
    );
  }, [condition.parameter_name, parameterPads]);

  const valueType = (selectedPad?.valueType?.type || "unknown") as string;
  console.log(
    "NEIL Condition valueType:",
    selectedPad,
    valueType,
    parameterPads,
  );
  const isTrigger = valueType === "Trigger";
  const selectedOperator = condition.operator || "";
  const isUnaryOperator = ["NON_EMPTY", "EMPTY"].includes(selectedOperator);

  const operatorOptions: { value: Operator; label: string }[] = [
    { value: "<", label: "&lt;" },
    { value: "<=", label: "&lt;=" },
    { value: "==", label: "==" },
    { value: "!=", label: "!=" },
    { value: ">=", label: "&gt;=" },
    { value: ">", label: "&gt;" },
    { value: "NON_EMPTY", label: "NON_EMPTY" },
    { value: "EMPTY", label: "EMPTY" },
    { value: "STARTS_WITH", label: "STARTS_WITH" },
    { value: "ENDS_WITH", label: "ENDS_WITH" },
    { value: "CONTAINS", label: "CONTAINS" },
  ];

  let availableOperators: { value: Operator; label: string }[] = [];
  if (valueType === "string") {
    availableOperators = operatorOptions;
  } else if (valueType === "number") {
    availableOperators = operatorOptions.filter((op) =>
      ["<", "<=", "==", "!=", ">=", ">"].includes(op.value || ""),
    );
  }
  // For other types, default to empty or handle as needed

  return (
    <div className="flex items-center gap-1 w-full">
      <select
        className="select select-bordered select-xs grow !outline-none"
        value={condition.parameter_name || ""}
        onChange={(e) => {
          updateTransition(transition.id, {
            ...transition,
            conditions: transition.conditions?.map((cond, idx) =>
              idx === conditionIdx
                ? {
                    ...cond,
                    parameter_name: e.target.value,
                  }
                : cond,
            ),
          });
        }}
      >
        {parameterPads.map((pad) => (
          <option key={pad.namePadId} value={pad.namePadId}>
            {pad.nameValue || pad.namePadId}
          </option>
        ))}
      </select>
      {!isTrigger && (
        <select
          className="select select-bordered select-xs w-40 !outline-none"
          value={selectedOperator}
          onChange={(e) => {
            updateTransition(transition.id, {
              ...transition,
              conditions: transition.conditions?.map((cond, idx) =>
                idx === conditionIdx
                  ? { ...cond, operator: e.target.value as Operator }
                  : cond,
              ),
            });
          }}
        >
          {availableOperators.map((op) => (
            <option key={op.value} value={op.value as string}>
              {op.label}
            </option>
          ))}
        </select>
      )}
      {!isTrigger && !isUnaryOperator && (
        <input
          type="text"
          className="input input-bordered grow select-xs !outline-none"
          value={(condition.value as unknown as string) || ""}
          onChange={(e) => {
            // Handle value change
          }}
        />
      )}
      <button
        className="btn btn-sm rounded-full bg-transparent aspect-square h-8 p-1"
        onClick={() => {
          updateTransition(transition.id, {
            ...transition,
            conditions: transition.conditions?.filter(
              (_, idx) => idx !== conditionIdx,
            ),
          });
        }}
      >
        <XCircleIcon className="w-full h-full text-error" />
      </button>
    </div>
  );
}
