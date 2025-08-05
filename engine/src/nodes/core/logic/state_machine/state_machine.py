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
        self.active_state.check_transition(
            check_ctx,
            self._get_property_values(),
            {name: False for name in self._get_trigger_names()},
        )
        ctx.complete()
        logging.info(f"Active state set to: {state.get_name().get_value()}")

    async def run(self):
        entry = cast(pad.StatelessSourcePad, self.get_pad_required("entry"))
        self.active_state = cast("State", entry.get_next_pads()[0].get_owner_node())
        if not entry.get_next_pads():
            logging.error(
                "StateMachine must have an entry pad connected to a State node."
            )
            return

        trigger_names = self._get_trigger_names()
        triggers_set = {name: False for name in trigger_names}
        req_parent: str = "UNSET"

        async def value_task(p: pad.SinkPad):
            nonlocal triggers_set
            async for item in p:
                if not self.active_state:
                    logging.error("No active state to process value task.")
                    item.ctx.complete()
                    continue
                if item.ctx.original_request.id != req_parent:
                    triggers_set = {name: False for name in trigger_names}

                name_id = p.get_id().replace("parameter_value_", "parameter_name_")
                name_pad = cast(pad.PropertySinkPad, self.get_pad(name_id))
                name = cast(str, name_pad.get_value())
                triggers_set[name] = True

                self.active_state.check_transition(
                    item.ctx, self._get_property_values(), triggers_set
                )
                item.ctx.complete()

        all_pad_groups = self.get_all_parameters()
        all_value_pads: list[pad.SinkPad] = []
        for pad_group in all_pad_groups:
            for p in pad_group:
                if p.get_id().startswith("parameter_value"):
                    all_value_pads.append(p)

        tasks = [value_task(p) for p in all_value_pads]
        await asyncio.gather(*tasks)

    def _get_property_values(self) -> dict[str, Any]:
        property_values: dict[str, Any] = {}
        for p in self.pads:
            if (
                isinstance(p, pad.PropertySinkPad)
                and p.get_id().startswith("parameter_value_")
                and p.get_previous_pad() is not None
            ):
                name_id = p.get_id().replace("parameter_value_", "parameter_name_")
                name = cast(
                    str,
                    cast(pad.PropertySinkPad, self.get_pad(name_id)).get_value(),
                )
                value = p.get_value()
                property_values[name] = value
        return property_values

    def _get_trigger_names(self) -> list[str]:
        trigger_names: list[str] = []
        for p in self.pads:
            if (
                isinstance(p, pad.StatelessSinkPad)
                and p.get_id().startswith("parameter_value_")
                and p.get_previous_pad() is not None
            ):
                name_id = p.get_id().replace("parameter_value_", "parameter_name_")
                name = cast(
                    str,
                    cast(pad.PropertySinkPad, self.get_pad(name_id)).get_value(),
                )
                trigger_names.append(name)
        return trigger_names

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

        num_parameters = cast(pad.PropertySinkPad, self.get_pad("num_parameters"))
        if not num_parameters:
            num_parameters = pad.PropertySinkPad(
                id="num_parameters",
                owner_node=self,
                type_constraints=[pad.types.Integer()],
                group="num_parameters",
                value=1,
            )
            self.pads.append(num_parameters)

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

        all_parameters = self.get_all_parameters()
        delta = num_parameters.get_value() - len(all_parameters)
        # Need to remove parameters
        pgs_to_remove: list[list[pad.SinkPad]] = []
        pgs_to_add: list[list[pad.SinkPad]] = []
        if delta < 0:
            to_remove = delta * -1
            while to_remove > 0:
                for pg in all_parameters:
                    # first try removing unconnected parameters
                    for p in pg:
                        if p.get_id().startswith("parameter_value_"):
                            if p.get_previous_pad() is None:
                                pgs_to_remove.append(pg)
                                to_remove -= 1

                    if to_remove <= 0:
                        break

                    # Next remove connected parameters
                    for p in pg:
                        if p.get_id().startswith("parameter_value_"):
                            p.disconnect()
                            to_remove -= 1
                            if to_remove <= 0:
                                break
        else:
            # Need to add parameters
            for i in range(len(all_parameters), num_parameters.get_value()):
                new_pads = self.create_parameter()
                pgs_to_add.append(cast(list[pad.SinkPad], new_pads))

        for pg in pgs_to_remove:
            for p in pg:
                p.disconnect()
                self.pads.remove(p)

        for pg in pgs_to_add:
            for p in pg:
                self.pads.append(p)

        self.rename_pads()
        self.update_type_constraints()
        self.update_parameter_names()
        self.update_pad_types()

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

    def get_all_parameters(self) -> list[list[pad.SinkPad]]:
        biggest_index = -1
        for p in self.pads:
            p_id = p.get_id()
            if p_id.startswith("parameter"):
                index = int(p_id.split("_")[-1])
                if index > biggest_index:
                    biggest_index = index

        res: list[list[pad.SinkPad]] = []
        for i in range(biggest_index + 1):
            p_pads = self.get_parameter_pads_for_index(i)
            if p_pads:
                res.append(self.get_parameter_pads_for_index(i))
        return res

    def get_parameter_pads_for_index(self, index: int):
        res: list[pad.SinkPad] = []
        for p in self.pads:
            p_id = p.get_id()
            if p_id.startswith("parameter") and p_id.endswith(f"_{index}"):
                if not isinstance(p, pad.SinkPad):
                    logging.warning(f"Pad {p_id} is not a SinkPad, but it should be.")
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

    def update_pad_types(self):
        for p in self.pads:
            if not p.get_id().startswith("parameter_value"):
                continue
            tcs = p.get_type_constraints()
            if not tcs:
                continue

            if len(tcs) == 1:
                if isinstance(p, pad.PropertySinkPad) and isinstance(
                    tcs[0], pad.types.Trigger
                ):
                    prev_pad = p.get_previous_pad()
                    p.disconnect()
                    idx = self.pads.index(p)
                    new_pad = pad.StatelessSinkPad(
                        id=p.get_id(),
                        owner_node=self,
                        type_constraints=tcs,
                        group=p.get_group(),
                    )
                    self.pads[idx] = new_pad
                    if prev_pad:
                        prev_pad.connect(new_pad)
                elif isinstance(p, pad.StatelessSinkPad) and not isinstance(
                    tcs[0], pad.types.Trigger
                ):
                    prev_pad = p.get_previous_pad()
                    p.disconnect()
                    idx = self.pads.index(p)
                    new_pad = pad.PropertySinkPad(
                        id=p.get_id(),
                        owner_node=self,
                        type_constraints=tcs,
                        group=p.get_group(),
                    )
                    self.pads[idx] = new_pad
                    if prev_pad:
                        prev_pad.connect(new_pad)

            else:
                if isinstance(p, pad.StatelessSinkPad):
                    prev_pad = p.get_previous_pad()
                    p.disconnect()
                    idx = self.pads.index(p)
                    new_pad = pad.PropertySinkPad(
                        id=p.get_id(),
                        owner_node=self,
                        type_constraints=tcs,
                        group=p.get_group(),
                    )
                    self.pads[idx] = new_pad
                    if prev_pad:
                        prev_pad.connect(new_pad)
