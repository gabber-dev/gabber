import {
  ArrowRightIcon,
  MinusIcon,
  PlusIcon,
} from "@heroicons/react/24/outline";
import { useStateMachine } from "./useStateMachine";
import {
  StateMachineTransition,
  StateMachineTransitionCondition,
} from "@/generated/stateMachine";
import { useState } from "react";

export function StateMachineTransitionEdit() {
  const { editingTransition, updateTransition } = useStateMachine();
  const { transition, fromState, toState } = editingTransition || {};
  if (!editingTransition) {
    return null;
  }
  return (
    <div className="max-w-md mx-auto">
      <div className="w-full flex flex-col items-center">
        <div className="border-b w-full flex flex-col gap-2 items-center">
          <h2 className="text-lg font-bold">Editing Transition</h2>
          <div className="flex items-center gap-2 mb-4">
            <span className="badge badge-primary">{fromState?.name}</span>
            <ArrowRightIcon className="w-5 h-5 text-base-content" />
            <span className="badge badge-primary">{toState?.name}</span>
          </div>
        </div>

        <div>
          <div className="flex gap-2">
            <h3 className="text-lg font-semibold mb-2">Conditions:</h3>
            <div className="flex">
              <button
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
                className="btn btn-sm btn-primary mr-2"
              >
                <PlusIcon className="w-full h-full" />
              </button>
              <button
                onClick={() => {
                  updateTransition(editingTransition.transition.id, {
                    ...editingTransition.transition,
                    conditions: editingTransition.transition.conditions?.slice(
                      0,
                      -1,
                    ),
                  });
                }}
                className="btn btn-sm btn-secondary"
              >
                <MinusIcon className="w-full h-full" />
              </button>
            </div>
          </div>
          {transition?.conditions ? (
            transition.conditions.map((condition, index) => (
              <Condition key={index} condition={condition} />
            ))
          ) : (
            <p className="text-gray-500 italic">No conditions available.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function Condition({
  condition,
}: {
  condition: StateMachineTransitionCondition;
}) {
  const { parameterPads } = useStateMachine();

  const selectedPad = parameterPads.find(
    (pad) => pad.namePadId === condition.parameter_name,
  );
  const valueType = (selectedPad?.valueType?.type || "unknown") as string;
  const isTrigger = valueType === "Trigger";
  const selectedOperator = condition.operator || "";
  const isUnaryOperator = ["NON_EMPTY", "EMPTY"].includes(selectedOperator);

  const operatorOptions = [
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

  let availableOperators: { value: string; label: string }[] = [];
  if (valueType === "string") {
    availableOperators = operatorOptions;
  } else if (valueType === "number") {
    availableOperators = operatorOptions.filter((op) =>
      ["<", "<=", "==", "!=", ">=", ">"].includes(op.value),
    );
  }
  // For other types, default to empty or handle as needed

  return (
    <div className="flex items-center gap-2">
      <select
        className="select select-bordered w-32"
        value={condition.parameter_name || ""}
        onChange={(e) => {
          // Handle parameter name change
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
          className="select select-bordered w-32"
          value={selectedOperator}
          onChange={(e) => {
            // Handle operator change
          }}
        >
          {availableOperators.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>
      )}
      {!isTrigger && !isUnaryOperator && (
        <input
          type="text"
          className="input input-bordered w-32"
          value={(condition.value as unknown as string) || ""}
          onChange={(e) => {
            // Handle value change
          }}
        />
      )}
      <button
        className="btn btn-sm btn-error"
        onClick={() => {
          // Handle condition removal
        }}
      >
        Remove
      </button>
    </div>
  );
}
