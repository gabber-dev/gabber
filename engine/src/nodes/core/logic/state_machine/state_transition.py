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

    def check_condition_met(
        self,
        ctx: pad.RequestContext,
        property_values: dict[str, Any],
        triggers: dict[str, bool],
    ) -> bool:
        for name, value in property_values.items():
            if not self._check_single_condition(name, value):
                return False

        for name, value in triggers.items():
            if self.get_index_for_name(name) < 0:
                continue

            if not value:
                return False

        ctx.complete()
        return True

    def _check_single_condition(self, name: str, value: Any) -> bool:
        idx = self.get_index_for_name(name)
        if idx < 0:
            return True
        operator = self.get_condition_operator(idx)
        if not self.state_machine:
            logging.error("StateMachine is not set for StateTransition.")
            return False
        if isinstance(value, str):
            if operator == "==":
                check_value = self.get_condition_value(idx)
                return value == check_value
            elif operator == "!=":
                check_value = self.get_condition_value(idx)
                return value != check_value
            elif operator == "CONTAINS":
                check_value = self.get_condition_value(idx)
                return isinstance(value, str) and check_value in value
            elif operator == "STARTS_WITH":
                check_value = self.get_condition_value(idx)
                return isinstance(value, str) and value.startswith(check_value)
            elif operator == "ENDS_WITH":
                check_value = self.get_condition_value(idx)
                return isinstance(value, str) and value.endswith(check_value)
            elif operator == "NOT_EMPTY":
                return bool(value)
            elif operator == "EMPTY":
                return not bool(value)
        elif isinstance(value, int):
            if operator == "==":
                check_value = self.get_condition_value(idx)
                return value == check_value
            elif operator == "!=":
                check_value = self.get_condition_value(idx)
                return value != check_value
            elif operator == "<":
                check_value = self.get_condition_value(idx)
                return value < check_value
            elif operator == "<=":
                check_value = self.get_condition_value(idx)
                return value <= check_value
            elif operator == ">":
                check_value = self.get_condition_value(idx)
                return value > check_value
            elif operator == ">=":
                check_value = self.get_condition_value(idx)
                return value >= check_value
        elif isinstance(value, float):
            if operator == "==":
                check_value = self.get_condition_value(idx)
                return value == check_value
            elif operator == "!=":
                check_value = self.get_condition_value(idx)
                return value != check_value
            elif operator == "<":
                check_value = self.get_condition_value(idx)
                return value < check_value
            elif operator == "<=":
                check_value = self.get_condition_value(idx)
                return value <= check_value
            elif operator == ">":
                check_value = self.get_condition_value(idx)
                return value > check_value
            elif operator == ">=":
                check_value = self.get_condition_value(idx)
                return value >= check_value
        elif isinstance(value, bool):
            if operator == "==":
                check_value = self.get_condition_value(idx)
                return value == check_value
            elif operator == "!=":
                check_value = self.get_condition_value(idx)
                return value != check_value
            return False
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

    def get_index_for_name(self, name: str) -> int:
        for i, p in enumerate(self.get_all_condition_pads()):
            if p[0].get_value() == name:
                return i
        return -1

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
