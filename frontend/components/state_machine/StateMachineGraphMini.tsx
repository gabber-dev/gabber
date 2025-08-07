import { useState } from "react";
import ReactModal from "react-modal";
import { StateMachineGraphEdit } from "./StateMachineGraphEdit";
export function StateMachineGraphMini() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div
        ref={(el) => {
          if (el) {
            ReactModal.setAppElement(el);
          }
        }}
      />
      <button onClick={() => setIsOpen(true)}>Edit</button>
      <ReactModal
        isOpen={isOpen}
        onRequestClose={() => setIsOpen(false)}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center z-11"
        shouldCloseOnOverlayClick={true}
      >
        <div className="fixed top-10 left-10 right-10 bottom-10 flex justify-center items-center border border-purple-500 border-2 rounded-lg overflow-hidden bg-base-100">
          <button
            className="btn bg-purple-500 text-white absolute top-2 right-2 z-10"
            onClick={() => setIsOpen(false)}
          >
            Close
          </button>
          <StateMachineGraphEdit />
        </div>
      </ReactModal>
    </div>
  );
}
