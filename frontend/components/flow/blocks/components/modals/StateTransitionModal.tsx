/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { useCallback, useMemo } from "react";
import ReactModal from "react-modal";
import { PropertyPad } from "../pads/PropertyPad";

interface StateTransitionModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodeData: NodeEditorRepresentation;
}

interface ConditionGroup {
  index: number;
  parameter: any;
  operator?: any;
  value?: any;
}

export function StateTransitionModal({
  isOpen,
  onClose,
  nodeData,
}: StateTransitionModalProps) {
  // Get the number of conditions from the num_conditions pad
  const numConditionsPad = useMemo(() => {
    return nodeData.pads.find((p) => p.id === "num_conditions");
  }, [nodeData]);

  // Group condition pads together
  const conditionGroups = useMemo(() => {
    const groups: ConditionGroup[] = [];
    const numConditions = Number(numConditionsPad?.value || 1);

    for (let i = 0; i < numConditions; i++) {
      const parameter = nodeData.pads.find(
        (p) => p.id === `condition_parameter_${i}`
      );
      
      if (parameter) {
        // Check if this is a trigger condition
        const isTrigger = parameter.type_constraints?.some(
          (c: any) => c.type === "Trigger"
        );

        if (isTrigger) {
          groups.push({
            index: i,
            parameter,
          });
        } else {
          const operator = nodeData.pads.find(
            (p) => p.id === `condition_operator_${i}`
          );
          const value = nodeData.pads.find(
            (p) => p.id === `condition_value_${i}`
          );

          groups.push({
            index: i,
            parameter,
            operator,
            value,
          });
        }
      }
    }

    return groups;
  }, [nodeData, numConditionsPad?.value]);

  return (
    <>
      <div ref={(el) => ReactModal.setAppElement(el as HTMLElement)} />
      <ReactModal
        isOpen={isOpen}
        onRequestClose={onClose}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center"
        className="w-full max-w-2xl bg-base-100 rounded-xl shadow-xl outline-none"
        shouldCloseOnOverlayClick={true}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-6 border-b border-base-300">
            <h2 className="text-lg font-semibold text-primary">
              Edit State Transition
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-base-200 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="p-6 flex-1">
            {/* Number of conditions */}
            <div className="mb-6">
              <div className="flex items-center gap-4">
                <div className="w-32 text-base-content/70">
                  num_conditions
                </div>
                <div className="flex-1">
                  <PropertyPad 
                    nodeId={nodeData.id} 
                    data={numConditionsPad!}
                  />
                </div>
              </div>
            </div>

            {/* Condition groups */}
            <div className="space-y-6">
              {conditionGroups.map((group) => {
                const isTrigger = group.parameter.type_constraints?.some(
                  (c: any) => c.type === "Trigger"
                );

                return (
                  <div 
                    key={group.index} 
                    className="p-4 bg-base-200 rounded-lg space-y-3"
                  >
                    <div className="text-sm font-medium text-primary mb-2">
                      {isTrigger ? "Trigger" : "Condition"} {group.index + 1}
                    </div>
                    
                    {/* Parameter */}
                    <div className="flex items-center gap-4">
                      <div className="w-32 text-base-content/70">
                        Parameter
                      </div>
                      <div className="flex-1">
                        <PropertyPad 
                          nodeId={nodeData.id} 
                          data={group.parameter}
                        />
                      </div>
                    </div>

                    {/* Operator and Value (only for non-trigger conditions) */}
                    {!isTrigger && group.operator && group.value && (
                      <>
                        <div className="flex items-center gap-4">
                          <div className="w-32 text-base-content/70">
                            Operator
                          </div>
                          <div className="flex-1">
                            <PropertyPad 
                              nodeId={nodeData.id} 
                              data={group.operator}
                            />
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="w-32 text-base-content/70">
                            Value
                          </div>
                          <div className="flex-1">
                            <PropertyPad 
                              nodeId={nodeData.id} 
                              data={group.value}
                            />
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex justify-end gap-3 p-6 border-t border-base-300">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm hover:bg-base-200 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </ReactModal>
    </>
  );
}