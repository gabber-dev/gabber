# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Any, cast

from core import node, pad
from pydantic import BaseModel

ALL_PARAMETER_TYPES: list[pad.types.BasePadType] = [
    pad.types.Float(),
    pad.types.Integer(),
    pad.types.Boolean(),
    pad.types.Trigger(),
    pad.types.String(),
]


class StateMachineStatePosition(BaseModel):
    x: float
    y: float


class StateMachineState(BaseModel):
    name: str
    position: StateMachineStatePosition


class StateMachineTransitionCondition(BaseModel):
    type: str
    value: Any


class StateMachineTransition(BaseModel):
    id: str
    from_state: str
    to_state: str
    conditions: list[str] = []


class StateMachineConfiguration(BaseModel):
    states: list[StateMachineState]
    transitions: list[StateMachineTransition]
    entry_state: str
    entry_node_position: StateMachineStatePosition


class StateMachine(node.Node):
    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="core", secondary="logic", tags=["state_machine", "container"]
        )

    async def resolve_pads(self):
        configuration = cast(pad.PropertySinkPad, self.get_pad("configuration"))
        if not configuration:
            configuration = pad.PropertySinkPad(
                id="configuration",
                owner_node=self,
                type_constraints=[pad.types.Object()],
                group="configuration",
                value={"states": [], "transitions": []},
            )
            self.pads.append(configuration)

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

        if num_parameters.get_value() < 0:
            num_parameters.set_value(0)

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

        self._resolve_num_pads()
        self._sort_and_rename_pads()

    async def run(self):
        configuration_pad = cast(pad.PropertySinkPad, self.get_pad("configuration"))
        current_state_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("current_state")
        )

    def _resolve_num_pads(self):
        current_num = len(self._get_parameter_indices())
        target_num: int = cast(
            pad.PropertySinkPad, self.get_pad("num_parameters")
        ).get_value()

        if target_num > current_num:
            for idx in range(current_num, target_num):
                self._add_parameter(idx)
        elif target_num < current_num:
            for _ in range(current_num - target_num):
                self._remove_last_parameter()

    def _add_parameter(self, idx: int):
        new_pads = [
            pad.PropertySinkPad(
                id=f"parameter_name_{idx}",
                owner_node=self,
                type_constraints=[pad.types.String()],
                group="parameters",
                value=None,
            ),
            pad.PropertySinkPad(
                id=f"parameter_value_{idx}",
                owner_node=self,
                type_constraints=ALL_PARAMETER_TYPES,
                group="parameter_values",
                value=None,
            ),
        ]
        self.pads.extend(new_pads)

    def _remove_last_parameter(self):
        indices = self._get_parameter_indices()
        if not indices:
            return

        last_index = max(indices)
        pads_to_remove = cast(
            list[pad.SinkPad],
            [
                p
                for p in self.pads
                if p.get_id()
                in [f"parameter_name_{last_index}", f"parameter_value_{last_index}"]
            ],
        )
        for p in pads_to_remove:
            p.disconnect()
            self.pads.remove(p)

    def _sort_and_rename_pads(self):
        configuration_pad = cast(
            pad.PropertySinkPad, self.get_pad_required("configuration")
        )
        num_parameters_pad = cast(
            pad.PropertySinkPad, self.get_pad_required("num_parameters")
        )
        current_state_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("current_state")
        )

        indices = self._get_parameter_indices()

        parameter_pads: list[pad.Pad] = []

        for order_idx, pad_name_idx in enumerate(indices):
            name_pad, value_pad = self._get_pads(pad_name_idx)
            name_pad.set_id(f"parameter_name_{order_idx}")
            value_pad.set_id(f"parameter_value_{order_idx}")
            parameter_pads.append(name_pad)
            parameter_pads.append(value_pad)

        self.pads = [
            configuration_pad,
            num_parameters_pad,
            current_state_pad,
        ] + parameter_pads

    def _get_parameter_indices(self):
        p_names = [
            p.get_id().split("_")[-1]
            for p in self.pads
            if p.get_id().startswith("parameter_name_")
        ]

        return [int(name) for name in p_names if name.isdigit()]

    def _get_pads(self, index: int) -> tuple[pad.SinkPad, pad.SinkPad]:
        name_pad = cast(
            pad.PropertySinkPad, self.get_pad_required(f"parameter_name_{index}")
        )
        value_pad = cast(
            pad.PropertySinkPad, self.get_pad_required(f"parameter_value_{index}")
        )
        return name_pad, value_pad
