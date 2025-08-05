# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import Any, cast

from core import pad

from .state_machine_member import StateMachineMember

ALL_INTEGER_OPERATORS: list[str] = ["<", "<=", "==", "!=", ">=", ">"]

ALL_BOOLEAN_OPERATORS: list[str] = ["==", "!="]

ALL_FLOAT_OPERATORS: list[str] = ["<", "<=", "==", "!=", ">=", ">"]

ALL_STRING_OPERATORS: list[str] = [
    "==",
    "!=",
    "CONTAINS",
    "STARTS_WITH",
    "ENDS_WITH",
    "NOT_EMPTY",
    "EMPTY",
]

ALL_TRIGGER_OPERATORS: list[str] = []


class StateTransition(StateMachineMember):
    def get_state_pad(self) -> pad.StatelessSourcePad:
        return cast(pad.StatelessSourcePad, self.get_pad_required("state"))

    def check_condition_met(self, ctx: pad.RequestContext) -> bool:
        all_conds = self.get_all_condition_pads()
        for c_group in all_conds:
            if self._check_single_condition(c_group):
                return True
        ctx.complete()
        return False

    def check_triggers(self, ctx: pad.RequestContext) -> bool:
        pass

    def _check_single_condition(self, cond_pads: list[pad.PropertySinkPad]) -> bool:
        name_pad = cond_pads[0]
        name = name_pad.get_value()
        if not self.state_machine:
            logging.error("StateMachine is not set for StateTransition.")
            return False
        input_value = self.state_machine.get_property_value_by_name(name)
        cond_len = len(cond_pads)
        if cond_len == 1:
            # Trigger case: condition met if input_value is truthy
            return bool(input_value)
        if cond_len < 2:
            logging.error(f"Invalid condition group size: {cond_len}")
            return False
        operator_pad = cond_pads[1]
        operator = operator_pad.get_value()
        if operator in ["NOT_EMPTY", "EMPTY"]:
            if cond_len != 2:
                logging.error(
                    f"Unary operator {operator} but condition group size is {cond_len}"
                )
                return False
            if operator == "NOT_EMPTY":
                return bool(input_value)
            elif operator == "EMPTY":
                return not bool(input_value)
        else:
            if cond_len != 3:
                logging.error(
                    f"Binary operator {operator} but condition group size is {cond_len}"
                )
                return False
            value_pad = cond_pads[2]
            value = value_pad.get_value()
            value_tcs = value_pad.get_type_constraints()
            if not value_tcs or len(value_tcs) != 1:
                logging.error(
                    f"Condition value pad {value_pad.get_id()} has invalid type constraints."
                )
                return False
            value_tc = value_tcs[0]
            if isinstance(value_tc, pad.types.String):
                if operator == "==":
                    return input_value == value
                elif operator == "!=":
                    return input_value != value
                elif operator == "CONTAINS":
                    return isinstance(input_value, str) and value in input_value
                elif operator == "STARTS_WITH":
                    return isinstance(input_value, str) and input_value.startswith(
                        value
                    )
                elif operator == "ENDS_WITH":
                    return isinstance(input_value, str) and input_value.endswith(value)
            elif isinstance(value_tc, pad.types.Integer):
                if operator == "<":
                    return input_value < value
                elif operator == "<=":
                    return input_value <= value
                elif operator == "==":
                    return input_value == value
                elif operator == "!=":
                    return input_value != value
                elif operator == ">=":
                    return input_value >= value
                elif operator == ">":
                    return input_value > value
            elif isinstance(value_tc, pad.types.Float):
                if operator == "<":
                    return input_value < value
                elif operator == "<=":
                    return input_value <= value
                elif operator == "==":
                    return input_value == value
                elif operator == "!=":
                    return input_value != value
                elif operator == ">=":
                    return input_value >= value
                elif operator == ">":
                    return input_value > value
            elif isinstance(value_tc, pad.types.Boolean):
                if operator == "==":
                    return input_value == value
                elif operator == "!=":
                    return input_value != value
            return False
        logging.error(f"Invalid condition group size: {cond_len}")
        return False

    async def resolve_pads(self):
        await super().resolve_pads()
        state_pad = cast(pad.StatelessSourcePad, self.get_pad("state"))
        if not state_pad:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="state",
                    owner_node=self,
                    type_constraints=[pad.types.Trigger()],
                    group="state",
                )
            )
            state_pad = cast(pad.StatelessSourcePad, self.get_pad("state"))
        condition_count = cast(pad.PropertySinkPad, self.get_pad("num_conditions"))
        if not condition_count:
            self.pads.append(
                pad.PropertySinkPad(
                    id="num_conditions",
                    owner_node=self,
                    type_constraints=[pad.types.Integer()],
                    group="num_conditions",
                    value=1,
                )
            )
            condition_count = cast(pad.PropertySinkPad, self.get_pad("num_conditions"))
        cond_pads = self.get_all_condition_pads()
        if len(cond_pads) != condition_count.get_value():
            delta = condition_count.get_value() - len(cond_pads)
            if delta > 0:
                for i in range(delta):
                    self.add_condition_pad(len(cond_pads) + i)
            elif delta < 0:
                while delta < 0 and len(cond_pads) > 0:
                    delta += 1
                    for p in cond_pads[-1]:
                        if isinstance(p, pad.PropertySinkPad):
                            p.disconnect()
                        self.pads.remove(p)
                    cond_pads.pop()

        self.resolve_condition_pads()

    def get_all_condition_pads(self) -> list[list[pad.PropertySinkPad]]:
        res: list[list[pad.PropertySinkPad]] = []
        i = 0
        while True:
            c_p = self.get_pad(f"condition_parameter_{i}")
            if c_p is None:
                break
            group = [cast(pad.PropertySinkPad, c_p)]
            c_o = cast(pad.PropertySinkPad, self.get_pad(f"condition_operator_{i}"))
            c_v = cast(pad.PropertySinkPad, self.get_pad(f"condition_value_{i}"))
            if c_o is not None:
                group.append(c_o)
                if c_v is not None:
                    group.append(c_v)
            else:
                if c_v is not None:
                    # Inconsistent, remove stray value pad
                    logging.warning(
                        f"Inconsistent condition pads for index {i}: stray value pad"
                    )
                    c_v.disconnect()
                    self.pads.remove(c_v)
            res.append(group)
            i += 1
        return res

    def get_condition_parameter(self, index: int) -> str:
        p = self.get_pad(f"condition_parameter_{index}")
        if not isinstance(p, pad.PropertySinkPad):
            raise ValueError(
                f"Pad condition_parameter_{index} is not a PropertySinkPad"
            )
        return p.get_value()

    def get_condition_operator(self, index: int) -> str:
        p = self.get_pad(f"condition_operator_{index}")
        if not isinstance(p, pad.PropertySinkPad):
            raise ValueError(f"Pad condition_operator_{index} is not a PropertySinkPad")
        return p.get_value()

    def get_condition_value(self, index: int) -> Any:
        p = self.get_pad(f"condition_value_{index}")
        if not isinstance(p, pad.PropertySinkPad):
            raise ValueError(f"Pad condition_value_{index} is not a PropertySinkPad")
        return p.get_value()

    def add_condition_pad(self, index: int):
        self.pads.extend(
            [
                pad.PropertySinkPad(
                    id=f"condition_parameter_{index}",
                    group="condition",
                    owner_node=self,
                    type_constraints=[pad.types.Enum(options=[])],
                ),
                pad.PropertySinkPad(
                    id=f"condition_operator_{index}",
                    group="condition",
                    owner_node=self,
                    type_constraints=[pad.types.Enum(options=["select parameter"])],
                ),
                pad.PropertySinkPad(
                    id=f"condition_value_{index}",
                    group="condition",
                    owner_node=self,
                    type_constraints=[
                        pad.types.String(),
                        pad.types.Integer(),
                        pad.types.Float(),
                        pad.types.Boolean(),
                    ],
                ),
            ]
        )

    def resolve_condition_pads(self):
        if not self.state_machine:
            return

        all_params = self.state_machine.get_all_parameters()
        name_index_lookup: dict[str, int] = {}
        for i in range(len(all_params)):
            name_pad = self.state_machine.get_name_pad(i)
            if name_pad and name_pad.get_value():
                name_index_lookup[name_pad.get_value()] = i

        all_names = list(name_index_lookup.keys())

        i = 0
        while True:
            c_p = cast(pad.PropertySinkPad, self.get_pad(f"condition_parameter_{i}"))
            if c_p is None:
                break
            c_p.set_type_constraints([pad.types.Enum(options=all_names)])
            param_name = c_p.get_value()
            if param_name not in name_index_lookup:
                c_p.set_value(None)
                c_o = cast(pad.PropertySinkPad, self.get_pad(f"condition_operator_{i}"))
                if c_o:
                    c_o.disconnect()
                    self.pads.remove(c_o)
                c_v = cast(pad.PropertySinkPad, self.get_pad(f"condition_value_{i}"))
                if c_v:
                    c_v.disconnect()
                    self.pads.remove(c_v)
                i += 1
                continue

            param_index = name_index_lookup[param_name]
            value_pad = self.state_machine.get_value_pad(param_index)

            if not value_pad:
                c_o = cast(pad.PropertySinkPad, self.get_pad(f"condition_operator_{i}"))
                if c_o:
                    c_o.disconnect()
                    self.pads.remove(c_o)
                c_v = cast(pad.PropertySinkPad, self.get_pad(f"condition_value_{i}"))
                if c_v:
                    c_v.disconnect()
                    self.pads.remove(c_v)
                i += 1
                continue

            value_tcs = value_pad.get_type_constraints()
            if not value_tcs or len(value_tcs) != 1:
                c_o = cast(pad.PropertySinkPad, self.get_pad(f"condition_operator_{i}"))
                if c_o:
                    c_o.disconnect()
                    self.pads.remove(c_o)
                c_v = cast(pad.PropertySinkPad, self.get_pad(f"condition_value_{i}"))
                if c_v:
                    c_v.disconnect()
                    self.pads.remove(c_v)
                i += 1
                continue

            value_tc = value_tcs[0]
            c_o = cast(pad.PropertySinkPad, self.get_pad(f"condition_operator_{i}"))
            c_v = cast(pad.PropertySinkPad, self.get_pad(f"condition_value_{i}"))
            is_trigger = isinstance(value_tc, pad.types.Trigger)

            if is_trigger:
                if c_o:
                    c_o.disconnect()
                    self.pads.remove(c_o)
                if c_v:
                    c_v.disconnect()
                    self.pads.remove(c_v)
            else:
                if c_o is None:
                    c_o = pad.PropertySinkPad(
                        id=f"condition_operator_{i}",
                        group="condition",
                        owner_node=self,
                        type_constraints=[pad.types.Enum(options=[])],
                    )
                    self.pads.append(c_o)
                # Set constraints and defaults
                if isinstance(value_tc, pad.types.String):
                    operators = ALL_STRING_OPERATORS
                    unary_operators = ["NOT_EMPTY", "EMPTY"]
                    value_type = pad.types.String()
                    default_value = ""
                    python_type_check = str
                elif isinstance(value_tc, pad.types.Integer):
                    operators = ALL_INTEGER_OPERATORS
                    unary_operators = []
                    value_type = pad.types.Integer()
                    default_value = 0
                    python_type_check = int
                elif isinstance(value_tc, pad.types.Float):
                    operators = ALL_FLOAT_OPERATORS
                    unary_operators = []
                    value_type = pad.types.Float()
                    default_value = 0.0
                    python_type_check = float
                elif isinstance(value_tc, pad.types.Boolean):
                    operators = ALL_BOOLEAN_OPERATORS
                    unary_operators = []
                    value_type = pad.types.Boolean()
                    default_value = False
                    python_type_check = bool
                else:
                    logging.warning(
                        f"Unsupported type constraint {value_tc} for condition value pad"
                    )
                    c_o.set_type_constraints(
                        [pad.types.Enum(options=["unsupported type"])]
                    )
                    if c_v:
                        c_v.disconnect()
                        self.pads.remove(c_v)
                    c_o.set_value(None)
                    i += 1
                    continue

                c_o.set_type_constraints([pad.types.Enum(options=operators)])
                if c_o.get_value() not in operators:
                    c_o.set_value(None)
                current_op = c_o.get_value()
                needs_value = current_op not in unary_operators if current_op else True
                if needs_value:
                    if c_v is None:
                        c_v = pad.PropertySinkPad(
                            id=f"condition_value_{i}",
                            group="condition",
                            owner_node=self,
                            type_constraints=[value_type],
                        )
                        self.pads.append(c_v)
                    c_v.set_type_constraints([value_type])
                    if not isinstance(c_v.get_value(), python_type_check):
                        c_v.set_value(default_value)
                else:
                    if c_v:
                        c_v.disconnect()
                        self.pads.remove(c_v)
            i += 1
