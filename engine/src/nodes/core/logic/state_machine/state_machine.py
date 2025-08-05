# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import TYPE_CHECKING, Any, cast

from core import node, pad
from utils import short_uuid

if TYPE_CHECKING:
    from .state import State
    from .state_transition import StateTransition

ALL_PARAMETER_TYPES: list[pad.types.BasePadType] = [
    pad.types.Float(),
    pad.types.Integer(),
    pad.types.Boolean(),
    pad.types.Trigger(),
    pad.types.String(),
]


class StateMachine(node.Node):
    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="core", secondary="logic", tags=["state_machine", "container"]
        )

    def set_active_state(self, state: "State", ctx: pad.RequestContext):
        current_state = cast(
            pad.PropertySourcePad, self.get_pad_required("current_state")
        )
        self.active_state = state
        push_ctx = pad.RequestContext(parent=ctx)
        current_state.push_item(state.get_name().get_value(), push_ctx)
        # Create a new request context so that call stack increases
        # to prevent infinite recursion in case of loops
        check_ctx = pad.RequestContext(parent=ctx)
        self.active_state.check_transition(check_ctx)
        ctx.complete()
        logging.info(f"Active state set to: {state.get_name().get_value()}")

    def get_property_value_by_name(self, name: str) -> Any:
        pad_groups = self.get_all_parameters()
        for i in range(len(pad_groups)):
            name_pad = self.get_name_pad(i)
            if not name_pad:
                continue
            if name_pad.get_value() == name:
                value_pad = self.get_value_pad(i)
                if value_pad:
                    return value_pad.get_value()

    async def run(self):
        entry = cast(pad.StatelessSourcePad, self.get_pad_required("entry"))
        self.active_state = cast("State", entry.get_next_pads()[0].get_owner_node())
        if not entry.get_next_pads():
            logging.error(
                "StateMachine must have an entry pad connected to a State node."
            )
            return

        async def value_task(p: pad.SinkPad):
            async for item in p:
                if not self.active_state:
                    logging.error("No active state to process value task.")
                    item.ctx.complete()
                    continue
                self.active_state.check_transition(item.ctx)
                item.ctx.complete()

        all_pad_groups = self.get_all_parameters()
        all_value_pads: list[pad.PropertySinkPad] = []
        for pad_group in all_pad_groups:
            for p in pad_group:
                if p.get_id().startswith("parameter_value"):
                    all_value_pads.append(p)

        tasks = [value_task(p) for p in all_value_pads]
        await asyncio.gather(*tasks)

    async def resolve_pads(self):
        entry = cast(pad.StatelessSourcePad, self.get_pad("entry"))
        if not entry:
            entry = pad.StatelessSourcePad(
                id="entry",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
                group="entry",
            )
            self.pads.append(entry)

        current_state = cast(pad.PropertySourcePad, self.get_pad("current_state"))
        if not current_state:
            current_state = pad.PropertySourcePad(
                id="current_state",
                owner_node=self,
                type_constraints=[pad.types.Enum(options=[])],
                group="current_state",
                value="",
            )
            self.pads.append(current_state)
        self.prune_pads()
        next_pads = entry.get_next_pads()
        if len(next_pads) > 1:
            logging.error("StateMachine must only have one entry pad.")
            for np in next_pads[1:]:
                np.disconnect()

        next_pads = entry.get_next_pads()
        for np in next_pads:
            if np.get_owner_node().get_type() != "State":
                logging.error("StateMachine entry pad must connect to a State node.")
                np.disconnect()
                await np.get_owner_node().resolve_pads()

        states, state_transitions = self.get_all_states()
        if entry.get_next_pads():
            self.active_state = cast(
                "State",
                entry.get_next_pads()[0].get_owner_node(),
            )
            current_state.set_value(self.active_state.get_name().get_value())
        current_state.set_type_constraints(
            [pad.types.Enum(options=[s.get_name().get_value() for s in states])]
        )

    # TODO: maybe there's a better way but likely not a big deal
    def get_all_states(self) -> tuple[list["State"], list["StateTransition"]]:
        entry = cast(pad.StatelessSourcePad, self.get_pad("entry"))
        stack: list[pad.SinkPad] = entry.get_next_pads()
        states: list["State"] = []
        state_transitions: list["StateTransition"] = []
        seen: set[pad.SinkPad] = set()
        while stack:
            current_pad = stack.pop()
            if current_pad in seen:
                continue
            seen.add(current_pad)

            owner_node = current_pad.get_owner_node()
            if owner_node.get_type() == "State":
                n = cast("State", owner_node)
                states.append(n)
                stack.extend(n.get_transition().get_next_pads())
            elif owner_node.get_type() == "StateTransition":
                n = cast("StateTransition", owner_node)
                state_transitions.append(n)
                stack.extend(n.get_state_pad().get_next_pads())

        return (states, state_transitions)

    def get_all_parameters(self) -> list[list[pad.PropertySinkPad]]:
        biggest_index = -1
        for p in self.pads:
            p_id = p.get_id()
            if p_id.startswith("parameter"):
                index = int(p_id.split("_")[-1])
                if index > biggest_index:
                    biggest_index = index

        res: list[list[pad.PropertySinkPad]] = []
        for i in range(biggest_index + 1):
            p_pads = self.get_parameter_pads_for_index(i)
            if p_pads:
                res.append(self.get_parameter_pads_for_index(i))
        return res

    def get_parameter_pads_for_index(self, index: int):
        res: list[pad.PropertySinkPad] = []
        for p in self.pads:
            p_id = p.get_id()
            if p_id.startswith("parameter") and p_id.endswith(f"_{index}"):
                if not isinstance(p, pad.PropertySinkPad):
                    logging.warning(
                        f"Pad {p_id} is not a PropertySinkPad, but it should be."
                    )
                    continue
                res.append(p)
        return res

    def get_other_pads(self):
        res: list[pad.Pad] = []
        for p in self.pads:
            p_id = p.get_id()
            if not p_id.startswith("parameter"):
                res.append(p)
        return res

    def get_name_pad(self, index: int) -> pad.PropertySinkPad | None:
        name_pad = self.get_pad(f"parameter_name_{index}")
        return name_pad if isinstance(name_pad, pad.PropertySinkPad) else None

    def get_value_pad(self, index: int) -> pad.PropertySinkPad | None:
        value_pad = self.get_pad(f"parameter_value_{index}")
        return value_pad if isinstance(value_pad, pad.PropertySinkPad) else None

    def prune_pads(self):
        p_pads = self.get_all_parameters()
        remove_p_pads: list[list[pad.PropertySinkPad]] = []
        keep_p_pads: list[list[pad.PropertySinkPad]] = []
        other_pads = self.get_other_pads()
        for pad_group in p_pads:
            p_v: pad.SinkPad | None = None
            p_n: pad.SinkPad | None = None
            for p in pad_group:
                if p.get_id().startswith("parameter_value"):
                    p_v = p
                elif p.get_id().startswith("parameter_name"):
                    p_n = p

            if not p_v or not p_n:
                remove_p_pads.append(pad_group)
                continue

            if not p_v.get_previous_pad():
                remove_p_pads.append(pad_group)
                continue

            keep_p_pads.append(pad_group)

        for pad_group in remove_p_pads:
            for p in pad_group:
                p.disconnect()

        self.pads = other_pads + [p for group in keep_p_pads for p in group]

        self.rename_pads()
        self.update_type_constraints()
        self.update_parameter_names()

        self.pads.extend(self.create_parameter())

    def rename_pads(self):
        p_pads = self.get_all_parameters()
        for i, p_group in enumerate(p_pads):
            for p in p_group:
                old_id = p.get_id()
                split = old_id.split("_")
                new_id = "_".join(split[:-1]) + f"_{i}"
                p.set_id(new_id)

    def create_parameter(self):
        index = len(self.get_all_parameters())
        new_pads = [
            pad.PropertySinkPad(
                id=f"parameter_name_{index}",
                group="parameter",
                owner_node=self,
                type_constraints=[pad.types.String()],
            ),
            pad.PropertySinkPad(
                id=f"parameter_value_{index}",
                group="parameter",
                owner_node=self,
                type_constraints=ALL_PARAMETER_TYPES,
            ),
        ]
        return new_pads

    def update_type_constraints(self):
        pad_groups = self.get_all_parameters()
        for idx, group in enumerate(pad_groups):
            p_v = self.get_pad(f"parameter_value_{idx}")
            assert isinstance(p_v, pad.SinkPad)
            prev_pad = p_v.get_previous_pad()
            if prev_pad:
                intersection = pad.types.INTERSECTION(
                    ALL_PARAMETER_TYPES, prev_pad.get_type_constraints()
                )
                p_v.set_type_constraints(intersection)

    def update_parameter_names(self):
        all_parameters = self.get_all_parameters()

        for i, _ in enumerate(all_parameters):
            name_pad = self.get_pad(f"parameter_name_{i}")
            if not name_pad or not isinstance(name_pad, pad.PropertyPad):
                logging.warning(
                    f"Pad parameter_name_{i} is not a PropertyPad, but it should be."
                )
                continue

            current_name = name_pad.get_value()

            if not current_name:
                default_name = name_pad.get_id()
                name_pad.set_value(default_name)

        existing_names = set()
        for i, _ in enumerate(all_parameters):
            name_pad = self.get_pad(f"parameter_name_{i}")
            if name_pad and isinstance(name_pad, pad.PropertyPad):
                current_name = name_pad.get_value()
                if current_name in existing_names:
                    name_pad.set_value(f"{current_name}_{short_uuid()}")
                else:
                    existing_names.add(current_name)
