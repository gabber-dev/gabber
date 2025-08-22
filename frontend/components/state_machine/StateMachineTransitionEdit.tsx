/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { ArrowRightIcon, XCircleIcon } from "@heroicons/react/24/outline";
import { StateMachineParameterPads, useStateMachine } from "./useStateMachine";
import {
  Operator,
  StateMachineTransition,
  StateMachineTransitionCondition,
} from "@/generated/stateMachine";
import { useEffect, useMemo } from "react";

export function StateMachineTransitionEdit() {
  const { editingTransition, updateTransition } = useStateMachine();
  const { transition, fromName, toName } = editingTransition || {};
  if (!editingTransition) {
    return null;
  }
  return (
    <div className="flex h-full w-full flex-col gap-2">
      <div className="border-b w-full flex flex-col gap-2 items-center">
        <h2 className="text-lg font-bold">Editing Transition</h2>
        <div className="flex items-center gap-2 mb-4">
          <span className="badge badge-primary">{fromName}</span>
          <ArrowRightIcon className="w-5 h-5 text-base-content" />
          <span className="badge badge-primary">{toName}</span>
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

  // Default parameter on first render for better UX
  useEffect(() => {
    if (!condition.parameter_name && parameterPads.length > 0) {
      const first = parameterPads[0].nameValue;
      updateTransition(transition.id, {
        ...transition,
        conditions: transition.conditions?.map((cond, idx) =>
          idx === conditionIdx ? { ...cond, parameter_name: first } : cond,
        ),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [condition.parameter_name, parameterPads.length]);

  const valueType = (
    (selectedPad?.valueType?.type || "unknown") as string
  ).toLowerCase();
  const isTrigger = valueType === "trigger";
  const isBoolean = valueType === "boolean";
  const isCompare = !isTrigger && !isBoolean;

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
          <option key={pad.nameValue} value={pad.nameValue}>
            {pad.nameValue || ""}
          </option>
        ))}
      </select>
      {isBoolean && (
        <BooleanCondition condition={condition} conditionIdx={conditionIdx} />
      )}
      {isCompare && (
        <CompareCondition
          condition={condition}
          conditionIdx={conditionIdx}
          selectedPad={selectedPad}
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

function CompareCondition({
  condition,
  conditionIdx,
  selectedPad,
}: {
  condition: StateMachineTransitionCondition;
  conditionIdx: number;
  selectedPad: StateMachineParameterPads | undefined;
}) {
  const { editingTransition, updateTransition } = useStateMachine();
  const { transition } = editingTransition || {};

  const operators: Operator[] = useMemo(() => {
    if (selectedPad?.valueType?.type === "string") {
      return [
        "==",
        "!=",
        "STARTS_WITH",
        "ENDS_WITH",
        "CONTAINS",
        "NON_EMPTY",
        "EMPTY",
      ];
    } else if (
      selectedPad?.valueType?.type === "number" ||
      selectedPad?.valueType?.type === "integer" ||
      selectedPad?.valueType?.type === "float"
    ) {
      return ["<", "<=", "==", "!=", ">=", ">"];
    }
    return [];
  }, [selectedPad?.valueType?.type]);

  const inputType = useMemo(() => {
    if (selectedPad?.valueType?.type === "string") {
      return "text";
    }
    if (
      selectedPad?.valueType?.type === "number" ||
      selectedPad?.valueType?.type === "integer" ||
      selectedPad?.valueType?.type === "float"
    ) {
      return "number";
    }
    return "text"; // Default fallback
  }, [selectedPad?.valueType?.type]);

  if (!transition) {
    return null;
  }

  return (
    <>
      <select
        className="select select-bordered select-xs w-20 !outline-none w-10"
        value={condition.operator || ""}
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
        {operators.map((op) => (
          <option key={op} value={op as string}>
            {op}
          </option>
        ))}
      </select>
      {condition.operator !== "EMPTY" && condition.operator !== "NON_EMPTY" && (
        <input
          className="input input-bordered input-xs !outline-none"
          type={inputType}
          value={(condition.value as string | number) || ""}
          onChange={(e) => {
            const newValue =
              inputType === "number" ? Number(e.target.value) : e.target.value;
            updateTransition(transition.id, {
              ...transition,
              conditions: transition.conditions?.map((cond, idx) =>
                idx === conditionIdx ? { ...cond, value: newValue } : cond,
              ),
            });
          }}
          step={
            selectedPad?.valueType?.type === "integer"
              ? "1"
              : selectedPad?.valueType?.type === "float" ||
                  selectedPad?.valueType?.type === "number"
                ? "any"
                : undefined
          }
        />
      )}
    </>
  );
}

function BooleanCondition({
  condition,
  conditionIdx,
}: {
  condition: StateMachineTransitionCondition;
  conditionIdx: number;
}) {
  const { editingTransition, updateTransition } = useStateMachine();
  const { transition } = editingTransition || {};

  if (!transition) {
    return null;
  }

  return (
    <select
      className="select select-bordered select-xs w-40 !outline-none"
      value={(condition.operator as string) || "TRUE"}
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
      <option value="TRUE">True</option>
      <option value="FALSE">False</option>
    </select>
  );
}
