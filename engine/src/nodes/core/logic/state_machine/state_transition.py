# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import Any, cast

from core import pad

from .state_machine_member import StateMachineMember

ALL_INTEGER_OPERATORS: list[str] = ["<", "<=", "==", "!=", ">=", ">"]

ALL_BOOLEAN_OPERATORS: list[str] = ["==", "!="]

ALL_FLOAT_OPERATORS: list[str] = ["<", ">"]

ALL_STRING_OPERATORS: list[str] = [
    "==",
    "!=",
    "CONTAINS",
    "STARTS_WITH",
    "ENDS_WITH",
    "NOT_EMPTY",
    "EMPTY",
]


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

    def _check_single_condition(self, cond_pads: list[pad.PropertySinkPad]) -> bool:
        name = cond_pads[0].get_value()
        operator = cond_pads[1].get_value()
        value = cond_pads[2].get_value()
        if not self.state_machine:
            logging.error("StateMachine is not set for StateTransition.")
            return False
        input_value = self.state_machine.get_property_value_by_name(name)

        value_tcs = cond_pads[2].get_type_constraints()
        if not value_tcs or len(value_tcs) != 1:
            logging.error(
                f"Condition value pad {cond_pads[2].get_id()} has invalid type constraints."
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
                return isinstance(input_value, str) and input_value.startswith(value)
            elif operator == "ENDS_WITH":
                return isinstance(input_value, str) and input_value.endswith(value)
            elif operator == "NOT_EMPTY":
                return bool(input_value)
            elif operator == "EMPTY":
                return not bool(input_value)
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
        condition_count = cast(pad.PropertySourcePad, self.get_pad("num_conditions"))
        if not condition_count:
            self.pads.append(
                pad.PropertySourcePad(
                    id="num_conditions",
                    owner_node=self,
                    type_constraints=[pad.types.Integer()],
                    group="num_conditions",
                    value=1,
                )
            )
            condition_count = cast(
                pad.PropertySourcePad, self.get_pad("num_conditions")
            )
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
        biggest_index = -1
        for p in self.pads:
            if p.get_id().startswith("condition"):
                index = int(p.get_id().split("_")[-1])
                if index > biggest_index:
                    biggest_index = index

        res: list[list[pad.PropertySinkPad]] = []
        for i in range(biggest_index + 1):
            c_pads: list[pad.Pad | None] = [
                self.get_pad(f"condition_parameter_{i}"),
                self.get_pad(f"condition_operator_{i}"),
                self.get_pad(f"condition_value_{i}"),
            ]
            has_none = all(p is None for p in c_pads)
            if has_none:
                for p in c_pads:
                    if not isinstance(p, pad.PropertySinkPad):
                        continue
                    p.disconnect()
            else:
                res.append(cast(list[pad.PropertySinkPad], c_pads))

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
        all_conds = self.get_all_condition_pads()
        if not self.state_machine:
            return

        all_params = self.state_machine.get_all_parameters()
        name_index_lookup: dict[str, int] = {}
        for i in range(len(all_params)):
            name = self.state_machine.get_name_pad(i)
            if name and name.get_value():
                name_index_lookup[name.get_value()] = i

        all_names = list(name_index_lookup.keys())

        for idx, c_group in enumerate(all_conds):
            c_p = c_group[0]
            c_o = c_group[1]
            c_v = c_group[2]
            c_p.set_type_constraints([pad.types.Enum(options=all_names)])
            if c_p.get_value() not in name_index_lookup:
                c_p.set_value(None)
                c_o.set_value("select parameter")
                c_v.set_value("")
                continue

            value_pad = self.state_machine.get_value_pad(idx)

            if not value_pad:
                c_o.set_value("select operator")
                c_v.set_value("")
                c_v.set_type_constraints([pad.types.String()])
                continue

            value_tcs = value_pad.get_type_constraints()
            if not value_tcs or len(value_tcs) != 1:
                c_o.set_value("select operator")
                c_o.set_type_constraints([pad.types.Enum(options=["select operator"])])
                c_v.set_value("")
                c_v.set_type_constraints([pad.types.String()])
                continue

            value_tc = value_tcs[0]
            if isinstance(value_tc, pad.types.String):
                if c_o.get_value() not in ALL_STRING_OPERATORS:
                    c_o.set_value(None)
                if c_o.get_value() is not None and not isinstance(c_v.get_value(), str):
                    c_v.set_value("")
                c_o.set_type_constraints([pad.types.Enum(options=ALL_STRING_OPERATORS)])
                c_v.set_type_constraints([pad.types.String()])
            elif isinstance(value_tc, pad.types.Integer):
                if c_o.get_value() not in ALL_INTEGER_OPERATORS:
                    c_o.set_value(None)
                if c_o.get_value() is not None and not isinstance(c_v.get_value(), int):
                    c_v.set_value(0)
                c_o.set_type_constraints(
                    [pad.types.Enum(options=ALL_INTEGER_OPERATORS)]
                )
                c_v.set_type_constraints([pad.types.Integer()])
            elif isinstance(value_tc, pad.types.Float):
                if c_o.get_value() not in ALL_FLOAT_OPERATORS:
                    c_o.set_value(None)

                if c_o.get_value() is not None and not isinstance(
                    c_v.get_value(), float
                ):
                    c_v.set_value(0.0)
                c_o.set_type_constraints([pad.types.Enum(options=ALL_FLOAT_OPERATORS)])
                c_v.set_type_constraints([pad.types.Float()])
            elif isinstance(value_tc, pad.types.Boolean):
                if c_o.get_value() not in ALL_STRING_OPERATORS:
                    c_o.set_value(None)
                if c_v.get_value() is not None and not isinstance(
                    c_v.get_value(), bool
                ):
                    c_v.set_value(False)
                c_o.set_type_constraints(
                    [pad.types.Enum(options=ALL_BOOLEAN_OPERATORS)]
                )
                c_v.set_type_constraints([pad.types.Boolean()])
            else:
                logging.warning(
                    f"Unsupported type constraint {value_tc} for condition value pad"
                )
                c_o.set_value("select operator")
                c_o.set_type_constraints([pad.types.Enum(options=["select operator"])])
                c_v.set_value("select value")
                c_v.set_type_constraints([pad.types.String()])
