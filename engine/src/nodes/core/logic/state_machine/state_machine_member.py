# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging

from core import node, pad

from .state_machine import StateMachine


class StateMachineMember(node.Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state_machine: StateMachine | None = None

    async def resolve_pads(self):
        self.resolve_entry_pads()
        self.rename_entry_pads()
        self.make_empty_entry()
        self.resolve_state_machine()

    def resolve_state_machine(self):
        for p in self.pads:
            if p.get_group() == "entry" and isinstance(p, pad.SinkPad):
                prev_pad = p.get_previous_pad()
                if prev_pad is None:
                    continue

                owner_node = prev_pad.get_owner_node()
                if isinstance(owner_node, StateMachine):
                    if (
                        self.state_machine is not None
                        and owner_node != self.state_machine
                    ):
                        logging.warning(
                            f"Multiple StateMachines found for {self.id}. "
                            "This is not allowed. Please ensure only one StateMachine is connected."
                        )
                        p.disconnect()
                        continue

                    self.state_machine = owner_node
                elif isinstance(owner_node, StateMachineMember):
                    if (
                        self.state_machine is not None
                        and owner_node.state_machine != self.state_machine
                    ):
                        logging.warning(
                            f"Multiple StateMachines found for {self.id}. "
                            "This is not allowed. Please ensure only one StateMachine is connected."
                        )
                        p.disconnect()
                        continue

                    if self.state_machine is not None:
                        owner_node.state_machine = self.state_machine
                    elif owner_node.state_machine is not None:
                        self.state_machine = owner_node.state_machine

    def resolve_entry_pads(self):
        entry_pads = self.get_entry_pads()
        to_remove: list[pad.StatelessSinkPad] = []
        for p in entry_pads:
            if p.get_previous_pad() is None:
                to_remove.append(p)

        for p in to_remove:
            p.disconnect()
            self.pads.remove(p)

    def get_entry_pads(self):
        res: list[pad.StatelessSinkPad] = []
        for p in self.pads:
            if isinstance(p, pad.StatelessSinkPad) and p.get_group() == "entry":
                res.append(p)
        return res

    def rename_entry_pads(self):
        entry_pads = self.get_entry_pads()
        for i, p in enumerate(entry_pads):
            p.set_id(f"entry_{i}")

    def make_empty_entry(self):
        all_entries = self.get_entry_pads()
        needs_new = True
        for entry in all_entries:
            if entry.get_previous_pad() is None:
                needs_new = False
                break

        if needs_new:
            self.pads.append(
                pad.StatelessSinkPad(
                    id=f"entry_{len(all_entries)}",
                    group="entry",
                    owner_node=self,
                    type_constraints=[pad.types.Trigger()],
                )
            )
