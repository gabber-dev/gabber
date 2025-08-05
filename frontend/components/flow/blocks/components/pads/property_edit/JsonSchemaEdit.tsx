/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

// JsonSchemaEdit.tsx
import { useState } from "react";
import { JsonSchemaModal } from "./JsonSchemaModal";
import ReactModal from "react-modal";
import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";

export function JsonSchemaEdit({ nodeId, padId }: PropertyEditProps) {
  const [showModal, setShowModal] = useState(false);
  const { runtimeValue, setEditorValue: setValue } = usePropertyPad(
    nodeId,
    padId,
  );

  return (
    <>
      <div ref={(el) => ReactModal.setAppElement(el as any)} />
      <button onClick={() => setShowModal(true)} className="btn">
        Edit JSON Schema
      </button>
      <ReactModal
        isOpen={showModal}
        onRequestClose={() => setShowModal(false)}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center"
        className="w-full max-w-lg bg-white dark:bg-neutral-800 rounded-lg shadow-lg outline-none"
        shouldCloseOnOverlayClick={true}
      >
        <JsonSchemaModal
          title="Edit JSON Schema"
          schema={runtimeValue as any}
          setSchema={setValue}
        />
      </ReactModal>
    </>
  );
}
