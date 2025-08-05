# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import Any, cast

from core import pad

from .state_machine_member import StateMachineMember
from .state_transition import StateTransition


class State(StateMachineMember):
    def get_name(self) -> pad.PropertySinkPad:
        res = self.get_pad_required("name")
        return cast(pad.PropertySinkPad, res)

    def get_transition(self) -> pad.StatelessSourcePad:
        res = self.get_pad_required("transition")
        return cast(pad.StatelessSourcePad, res)

    async def resolve_pads(self):
        await super().resolve_pads()
        name = cast(pad.PropertySinkPad | None, self.get_pad("name"))
        if not name:
            name = pad.PropertySinkPad(
                id="name",
                owner_node=self,
                type_constraints=[pad.types.String()],
                group="name",
            )
            self.pads.append(name)

        transition = cast(pad.StatelessSourcePad | None, self.get_pad("transition"))
        if not transition:
            transition = pad.StatelessSourcePad(
                id="transition",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
                group="transition",
            )
            self.pads.append(transition)

    def check_transition(
        self,
        ctx: pad.RequestContext,
        property_values: dict[str, Any],
        triggers: dict[str, bool],
    ) -> None:
        for np in self.get_transition().get_next_pads():
            transition_node = np.get_owner_node()
            if not isinstance(transition_node, StateTransition):
                logging.error(
                    f"State {self.get_name().get_value()} has a transition pad connected to a non-StateTransition node: {np.get_owner_node().get_type()}"
                )
                ctx.complete()
                continue

            if transition_node.check_condition_met(ctx, property_values, triggers):
                state_pad = cast(
                    pad.StatelessSourcePad,
                    transition_node.get_pad_required("state"),
                )
                next_pads = state_pad.get_next_pads()
                if not next_pads:
                    logging.error(
                        f"StateTransition {transition_node.id} does not connect to any State node."
                    )
                    ctx.complete()
                    continue

                new_state = next_pads[0].get_owner_node()
                if not isinstance(new_state, State):
                    logging.error(
                        f"StateTransition {transition_node.id} does not connect to a valid State node."
                    )
                    ctx.complete()
                    continue
                if self.state_machine:
                    self.state_machine.set_active_state(new_state, ctx)
                    ctx.complete()
                    return

        ctx.complete()

    def reset_all_transitions(self):
        for np in self.get_transition().get_next_pads():
            transition_node = np.get_owner_node()
            if isinstance(transition_node, StateTransition):
                pass
