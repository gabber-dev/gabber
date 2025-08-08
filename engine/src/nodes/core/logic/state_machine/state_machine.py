# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Any, cast, Literal
import logging

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
    id: str
    name: str
    position: StateMachineStatePosition


class StateMachineTransitionCondition(BaseModel):
    parameter_name: str | None = None
    operator: (
        Literal[
            "<",
            "<=",
            "==",
            "!=",
            ">=",
            ">",
            "NON_EMPTY",
            "EMPTY",
            "STARTS_WITH",
            "ENDS_WITH",
            "CONTAINS",
        ]
        | None
    ) = None
    value: Any | None = None


class StateMachineTransition(BaseModel):
    id: str
    from_state: str
    to_state: str
    conditions: list[StateMachineTransitionCondition] = []


class StateMachineConfiguration(BaseModel):
    states: list[StateMachineState]
    transitions: list[StateMachineTransition]
    entry_state: str | None = None
    entry_node_position: StateMachineStatePosition | None = None


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

        # Ensure configuration has necessary keys and set entry_state if needed
        config_dict = configuration.get_value()
        cleaned_dict = {}

        # Validate states
        valid_states = []
        state_ids = set()
        if "states" in config_dict and isinstance(config_dict["states"], list):
            for state_dict in config_dict["states"]:
                try:
                    sm = StateMachineState.model_validate(state_dict)
                    if sm.id in state_ids:
                        logging.warning(
                            f"Duplicate state ID '{sm.id}' found. Skipping."
                        )
                        continue
                    state_ids.add(sm.id)
                    valid_states.append(state_dict)
                except Exception:
                    logging.warning(
                        f"Invalid state configuration: {state_dict}. Skipping."
                    )
        cleaned_dict["states"] = valid_states

        # Validate transitions
        valid_transitions = []
        if "transitions" in config_dict and isinstance(
            config_dict["transitions"], list
        ):
            for trans_dict in config_dict["transitions"]:
                try:
                    tm = StateMachineTransition.model_validate(trans_dict)
                    if tm.from_state not in state_ids or tm.to_state not in state_ids:
                        logging.warning(
                            f"Transition from '{tm.from_state}' to '{tm.to_state}' contains unknown states. Skipping."
                        )
                        continue

                    valid_transitions.append(trans_dict)
                except Exception:
                    logging.warning(
                        f"Invalid transition configuration: {trans_dict}. Skipping."
                    )
        cleaned_dict["transitions"] = valid_transitions
        cleaned_dict["entry_state"] = config_dict.get("entry_state", None)

        entry_node_position = config_dict.get("entry_node_position", None)
        if entry_node_position and isinstance(entry_node_position, dict):
            try:
                cleaned_dict["entry_node_position"] = (
                    StateMachineStatePosition.model_validate(entry_node_position)
                )
            except Exception:
                logging.warning(
                    f"Invalid entry node position configuration: {entry_node_position}. Setting to default."
                )
                cleaned_dict["entry_node_position"] = StateMachineStatePosition(
                    x=0.0, y=0.0
                )

        config = StateMachineConfiguration.model_validate(cleaned_dict)
        if not config.entry_node_position:
            config.entry_node_position = StateMachineStatePosition(x=0.0, y=0.0)

        if not config.entry_state and config.states:
            config.entry_state = config.states[0].id

        elif config.entry_state:
            # Ensure entry state exists in states
            if not any(state.id == config.entry_state for state in config.states):
                logging.warning(
                    f"Entry state '{config.entry_state}' not found in states. Setting to None."
                )
                if len(config.states) > 0:
                    config.entry_state = config.states[0].id
                else:
                    config.entry_state = None

        seen_states = set()
        for state in config.states:
            if state.name in seen_states:
                logging.warning(
                    f"Duplicate state name '{state.name}' found. Renaming to avoid conflicts."
                )
                while state.name in seen_states:
                    state.name += "(1)"
            seen_states.add(state.name)

        configuration.set_value(config.model_dump())

        self._resolve_num_pads()
        self._resolve_value_types()
        self._resolve_pad_mode()
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

    def _resolve_value_types(self):
        for p in self.pads:
            if p.get_id().startswith("parameter_value_"):
                p = cast(pad.SinkPad, p)
                prev_pad = p.get_previous_pad()
                if not prev_pad:
                    p.set_type_constraints(ALL_PARAMETER_TYPES)
                else:
                    tcs = p.get_type_constraints()
                    intersection = pad.types.INTERSECTION(
                        tcs, prev_pad.get_type_constraints()
                    )
                    p.set_type_constraints(intersection)

    def _resolve_pad_mode(self):
        for idx, p in enumerate(self.pads):
            if p.get_id().startswith("parameter_value_"):
                p = cast(pad.SinkPad, p)
                if isinstance(p, pad.PropertyPad):
                    tcs = p.get_type_constraints()
                    prev_pad = p.get_previous_pad()
                    if (
                        tcs
                        and len(tcs) == 1
                        and isinstance(tcs[0], pad.types.Trigger)
                        and prev_pad
                    ):
                        new_pad = pad.StatelessSinkPad(
                            id=p.get_id(),
                            owner_node=self,
                            type_constraints=tcs,
                            group=p.get_group(),
                        )
                        prev_pad.disconnect(p)
                        prev_pad.connect(new_pad)
                        self.pads[idx] = new_pad
                else:
                    tcs = p.get_type_constraints()
                    prev_pad = p.get_previous_pad()
                    if (
                        (
                            tcs
                            and len(tcs) == 1
                            and not isinstance(tcs[0], pad.types.Trigger)
                        )
                        or (not tcs)
                        or (len(tcs) > 1)
                    ):
                        new_pad = pad.PropertySinkPad(
                            id=p.get_id(),
                            owner_node=self,
                            type_constraints=tcs,
                            group=p.get_group(),
                        )
                        if prev_pad:
                            prev_pad.disconnect(p)
                            prev_pad.connect(new_pad)
                        self.pads[idx] = new_pad

    def _resolve_condition_operators(self):
        pass

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
