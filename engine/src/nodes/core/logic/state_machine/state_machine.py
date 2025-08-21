# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, Literal, cast

from pydantic import BaseModel

from core import node, pad, runtime_types

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
            "TRUE",
            "FALSE",
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
    special_any_state_position: StateMachineStatePosition | None = None


class StateMachine(node.Node):
    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="core", secondary="logic", tags=["state_machine", "container"]
        )

    @classmethod
    def get_description(cls) -> str:
        return "Create logic to control the flow of your application based on parameter conditions."

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

        previous_state = cast(pad.PropertySourcePad, self.get_pad("previous_state"))
        if not previous_state:
            previous_state = pad.PropertySourcePad(
                id="previous_state",
                owner_node=self,
                type_constraints=[pad.types.Enum(options=[])],
                group="previous_state",
                value="",
            )
            self.pads.append(previous_state)

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
                    if (
                        tm.from_state != "__ANY__"
                        and tm.from_state not in state_ids
                        or tm.to_state not in state_ids
                    ):
                        logging.warning(
                            f"Transition from '{tm.from_state}' to '{tm.to_state}' contains unknown states. Skipping."
                        )
                        continue

                    if tm.to_state == "__ANY__":
                        logging.warning(
                            "Transition to '__ANY__' state is not allowed. Skipping."
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

        special_any_state_position = config_dict.get("special_any_state_position", None)
        if special_any_state_position and isinstance(special_any_state_position, dict):
            try:
                cleaned_dict["special_any_state_position"] = (
                    StateMachineStatePosition.model_validate(special_any_state_position)
                )
            except Exception:
                logging.warning(
                    f"Invalid special any state position configuration: {special_any_state_position}. Setting to default."
                )
                cleaned_dict["special_any_state_position"] = StateMachineStatePosition(
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

        # Update current_state enum options and default value from configuration
        try:
            enum_options = [s.name for s in config.states]
            previous_state.set_type_constraints([pad.types.Enum(options=enum_options)])
            current_state.set_type_constraints([pad.types.Enum(options=enum_options)])

            # Set current state value to entry state's name if present, else blank
            if config.entry_state:
                entry = next(
                    (s for s in config.states if s.id == config.entry_state), None
                )
                previous_state.set_value(entry.name if entry else "")
                current_state.set_value(entry.name if entry else "")
            else:
                previous_state.set_value("")
                current_state.set_value("")
        except Exception as e:
            logging.warning(f"Failed to update current_state pad: {e}")

        configuration.set_value(config.model_dump())

        self._resolve_num_pads()
        self._fix_missing_pads()
        self._resolve_value_types()
        self._resolve_pad_mode()
        self._sort_and_rename_pads()
        self._resolve_condition_operators()

    async def run(self):
        configuration_pad = cast(pad.PropertySinkPad, self.get_pad("configuration"))
        current_state_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("current_state")
        )
        previous_state_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("previous_state")
        )

        triggers: dict[str, bool] = {}
        original_trigger_ctx: pad.RequestContext | None = None

        def get_current_state() -> StateMachineState:
            state_name = cast(str, current_state_pad.get_value())
            config_dict = configuration_pad.get_value()
            config = StateMachineConfiguration.model_validate(config_dict)
            for state in config.states:
                if state.name == state_name:
                    return state
            raise ValueError(
                f"Current state '{state_name}' not found in configuration."
            )

        def get_outgoing_transitions(state_id: str) -> list[StateMachineTransition]:
            config_dict = configuration_pad.get_value()
            config = StateMachineConfiguration.model_validate(config_dict)
            return [
                transition
                for transition in config.transitions
                if transition.from_state == state_id
            ]

        def check_transitions(
            *, ctx: pad.RequestContext, from_id: str, current_state_name: str
        ):
            transitions = get_outgoing_transitions(from_id)

            if len(transitions) == 0:
                return

            config_dict = configuration_pad.get_value()
            config = StateMachineConfiguration.model_validate(config_dict)

            parameter_name_value: dict[str, Any] = {}
            trigger_params = set[str]()
            for idx in self._get_parameter_indices():
                name_pad, value_pad = self._get_pads(idx)
                name = cast(str, name_pad.get_value())
                if isinstance(value_pad, pad.PropertyPad):
                    parameter_name_value[name] = value_pad.get_value()
                else:
                    trigger_params.add(name)

            for transition in transitions:
                res = True
                for c in transition.conditions:
                    if c.parameter_name in trigger_params:
                        res = res and triggers.get(c.parameter_name, False)
                    elif c.parameter_name in parameter_name_value:
                        param_value = parameter_name_value[c.parameter_name]
                        c_value = c.value
                        if isinstance(param_value, bool):
                            if c.operator != "TRUE" and c.operator != "FALSE":
                                logging.warning(
                                    f"Invalid operator '{c.operator}' for boolean parameter '{c.parameter_name}'."
                                )
                                res = False
                                break

                            if c.operator == "TRUE" and not param_value:
                                res = False
                                break
                            elif c.operator == "FALSE" and param_value:
                                res = False
                                break

                        elif isinstance(param_value, (int, float)):
                            if not isinstance(c_value, (int, float)):
                                logging.warning(
                                    f"Condition value for numeric parameter '{c.parameter_name}' must be a number."
                                )
                                res = False
                                break

                            if c.operator == "<":
                                res = res and (param_value < c_value)
                            elif c.operator == "<=":
                                res = res and (param_value <= c_value)
                            elif c.operator == "==":
                                res = res and (param_value == c_value)
                            elif c.operator == "!=":
                                res = res and (param_value != c_value)
                            elif c.operator == ">=":
                                res = res and (param_value >= c_value)
                            elif c.operator == ">":
                                res = res and (param_value > c_value)
                        elif isinstance(param_value, str):
                            if not isinstance(c_value, str):
                                logging.warning(
                                    f"Condition value for string parameter '{c.parameter_name}' must be a string."
                                )
                                res = False
                                break

                            if c.operator == "==":
                                res = res and (param_value == c_value)
                            elif c.operator == "!=":
                                res = res and (param_value != c_value)
                            elif c.operator == "NON_EMPTY":
                                res = res and bool(param_value)
                            elif c.operator == "EMPTY":
                                res = res and not bool(param_value)
                            elif c.operator == "STARTS_WITH":
                                res = res and param_value.startswith(c_value)
                            elif c.operator == "ENDS_WITH":
                                res = res and param_value.endswith(c_value)
                            elif c.operator == "CONTAINS":
                                res = res and (c_value in param_value)
                            else:
                                logging.warning(
                                    f"Invalid operator '{c.operator}' for string parameter '{c.parameter_name}'."
                                )
                                res = False
                    else:
                        res = False

                if res:
                    next_state_id = transition.to_state

                    next_state = next(
                        (s for s in config.states if s.id == next_state_id),
                        None,
                    )

                    if not next_state:
                        logging.error(
                            f"Next state '{next_state_id}' not found in configuration."
                        )
                        continue

                    logging.info(
                        f"Transitioning from state '{current_state_name}' to '{next_state.name}'"
                    )

                    previous_state_pad.push_item(current_state_name, ctx)
                    current_state_pad.push_item(next_state.name, ctx)

        async def pad_task(idx: int):
            nonlocal original_trigger_ctx
            name_pad, value_pad = self._get_pads(idx)
            async for item in value_pad:
                name = cast(str, name_pad.get_value())
                if isinstance(item.value, runtime_types.Trigger):
                    if item.ctx.original_request != original_trigger_ctx:
                        triggers.clear()
                        original_trigger_ctx = item.ctx.original_request
                    triggers[name] = True

                current_state = get_current_state()
                check_transitions(
                    ctx=item.ctx,
                    from_id="__ANY__",
                    current_state_name=current_state.name,
                )
                check_transitions(
                    ctx=item.ctx,
                    from_id=current_state.id,
                    current_state_name=current_state.name,
                )

                item.ctx.complete()

        all_idxes = self._get_parameter_indices()
        tasks = [pad_task(idx) for idx in all_idxes if idx is not None and idx >= 0]

        await asyncio.gather(*tasks)

    def _fix_missing_pads(self):
        for i in self._get_parameter_indices():
            name_pad = self.get_pad(f"parameter_name_{i}")
            if not name_pad:
                logging.warning(
                    f"Missing name pad for parameter {i}. Creating default pad."
                )
                name_pad = pad.PropertySinkPad(
                    id=f"parameter_name_{i}",
                    owner_node=self,
                    type_constraints=[pad.types.String()],
                    group="parameters",
                    value=None,
                )
                self.pads.append(name_pad)
            value_pad = self.get_pad(f"parameter_value_{i}")
            if not value_pad:
                logging.warning(
                    f"Missing value pad for parameter {i}. Creating default pad."
                )
                value_pad = pad.PropertySinkPad(
                    id=f"parameter_value_{i}",
                    owner_node=self,
                    type_constraints=ALL_PARAMETER_TYPES,
                    group="parameter_values",
                    value=None,
                )
                self.pads.append(value_pad)

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
        for i in self._get_parameter_indices():
            _, value_pad = self._get_pads(i)
            prev_pad = value_pad.get_previous_pad()
            if prev_pad:
                tcs = value_pad.get_type_constraints()
                tcs = pad.types.INTERSECTION(tcs, prev_pad.get_type_constraints())
                value_pad.set_type_constraints(tcs)
            else:
                value_pad.set_type_constraints(ALL_PARAMETER_TYPES)

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
        configuration_pad = cast(pad.PropertySinkPad, self.get_pad("configuration"))
        config_dict = configuration_pad.get_value()

        if "transitions" not in config_dict or not isinstance(
            config_dict["transitions"], list
        ):
            return

        allowed_operators = {
            pad.types.Float: ["<", "<=", "==", "!=", ">=", ">"],
            pad.types.Integer: ["<", "<=", "==", "!=", ">=", ">"],
            pad.types.Boolean: ["TRUE", "FALSE"],
            pad.types.String: [
                "==",
                "!=",
                "NON_EMPTY",
                "EMPTY",
                "STARTS_WITH",
                "ENDS_WITH",
                "CONTAINS",
            ],
            pad.types.Trigger: [],
        }

        for trans in config_dict["transitions"]:
            if "conditions" in trans and isinstance(trans["conditions"], list):
                for cond in trans["conditions"]:
                    if not isinstance(cond, dict):
                        continue
                    param_name = cond.get("parameter_name")
                    if param_name is None:
                        if cond.get("operator") is not None:
                            logging.warning(
                                "Condition without parameter_name, setting operator to None."
                            )
                            cond["operator"] = None
                        continue

                    found = False
                    tcs = []
                    for idx in self._get_parameter_indices():
                        name_pad, value_pad = self._get_pads(idx)
                        if name_pad.get_value() == param_name:
                            tcs = value_pad.get_type_constraints()
                            found = True
                            break

                    if not found:
                        logging.warning(
                            f"Parameter '{param_name}' not found. Setting operator to None."
                        )
                        cond["operator"] = None
                        continue

                    if not tcs:
                        cond["operator"] = None
                        continue

                    allowed_sets = [
                        set(allowed_operators.get(type(type_), [])) for type_ in tcs
                    ]
                    allowed = set.intersection(*allowed_sets) if allowed_sets else set()

                    operator = cond.get("operator")
                    if operator is not None and operator not in allowed:
                        logging.warning(
                            f"Invalid operator '{operator}' for parameter '{param_name}' with types {[type_.__class__.__name__ for type_ in tcs]}. Setting to None."
                        )
                        cond["operator"] = None

                    if cond.get("operator") is None:
                        if isinstance(tcs[0], pad.types.Boolean):
                            cond["operator"] = "TRUE"
                        else:
                            cond["operator"] = "=="

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
        previous_state_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("previous_state")
        )

        indices = self._get_parameter_indices()

        parameter_pads: list[pad.Pad] = []

        pad_groups: list[tuple[pad.Pad, pad.Pad]] = []

        for order_idx, pad_name_idx in enumerate(indices):
            name_pad, value_pad = self._get_pads(pad_name_idx)
            pad_groups.append((name_pad, value_pad))

        for order_idx, (name_pad, value_pad) in enumerate(pad_groups):
            name_pad.set_id(f"parameter_name_{order_idx}")
            value_pad.set_id(f"parameter_value_{order_idx}")
            parameter_pads.append(name_pad)
            parameter_pads.append(value_pad)

        self.pads = [
            configuration_pad,
            num_parameters_pad,
            current_state_pad,
            previous_state_pad,
        ] + parameter_pads

    def _get_parameter_indices(self):
        p_names = [
            p.get_id().split("_")[-1]
            for p in self.pads
            if p.get_id().startswith("parameter_name_")
        ]

        indices = [int(name) for name in p_names if name.isdigit()]
        sorted_indices = sorted(indices)

        return sorted_indices

    def _get_pads(self, index: int) -> tuple[pad.PropertySinkPad, pad.SinkPad]:
        name_pad = cast(
            pad.PropertySinkPad, self.get_pad_required(f"parameter_name_{index}")
        )
        value_pad = cast(pad.SinkPad, self.get_pad_required(f"parameter_value_{index}"))
        return name_pad, value_pad
