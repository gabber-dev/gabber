# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
import asyncio
from typing import cast

from gabber.core import pad
from gabber.core.node import Node, NodeMetadata
from gabber.core.types import pad_constraints

STRING_COMPARISON_OPERATORS = [
    "==",
    "!=",
    "CONTAINS",
    "NOT_CONTAINS",
    "STARTS_WITH",
    "ENDS_WITH",
]

INTEGER_COMPARISON_OPERATORS = [
    "==",
    "!=",
    "<",
    ">",
    "<=",
    ">=",
]

ENUM_COMPARISON_OPERATORS = [
    "==",
    "!=",
]

FLOAT_COMPARISON_OPERATORS = [
    "==",
    "!=",
    "<",
    ">",
    "<=",
    ">=",
]

BOOL_COMPARISON_OPERATORS = [
    "==",
    "!=",
]

ALL_ALLOWED_TYPES: list[pad_constraints.BasePadType] = [
    pad_constraints.String(),
    pad_constraints.Integer(),
    pad_constraints.Float(),
    pad_constraints.Boolean(),
    pad_constraints.Enum(),
]


class Compare(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="logic", tags=["compare"])

    def resolve_pads(self):
        num_conditions = cast(pad.PropertySinkPad, self.get_pad("num_conditions"))
        if not num_conditions:
            num_conditions = pad.PropertySinkPad(
                id="num_conditions",
                group="num_conditions",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer()],
                value=1,
            )

        mode_pad = cast(pad.PropertySinkPad, self.get_pad("mode"))
        if not mode_pad:
            mode_pad = pad.PropertySinkPad(
                id="mode",
                group="mode",
                owner_node=self,
                default_type_constraints=[pad_constraints.Enum(options=["AND", "OR"])],
                value="AND",
            )

        value = cast(pad.PropertySourcePad, self.get_pad("value"))
        if not value:
            value = pad.PropertySourcePad(
                id="value",
                group="value",
                owner_node=self,
                default_type_constraints=[pad_constraints.Boolean()],
                value=False,
            )

        self._rename_conditions()
        condition_pads = self._get_condition_pads()
        self.pads = [num_conditions, mode_pad, value] + [
            p for cps in condition_pads for p in cps if p is not None
        ]

        self._add_or_remove_condition_pads()
        condition_pads = self._get_condition_pads()
        for cps in condition_pads:
            a, b, op = cps
            self._resolve_operators(a, b, op)

        self.pads = [num_conditions, mode_pad, value] + [
            p for cps in condition_pads for p in cps
        ]

        mode = mode_pad.get_value()
        if mode not in ["AND", "OR"]:
            mode_pad.set_value("AND")

        val = self.resolve_value(condition_pads=condition_pads, mode_pad=mode_pad)
        value.set_value(val)

    def _get_indices(self) -> list[int]:
        indices = set[int]()
        for p in self.pads:
            if not p:
                logging.error("Found None pad in self.pads")
                continue
            if p.get_id().startswith("condition_"):
                try:
                    index = int(p.get_id().split("_")[1])
                    indices.add(index)
                except (ValueError, IndexError):
                    logging.error(f"Invalid pad ID format: {p.get_id()}")

        indices = sorted(indices)
        return indices

    def _rename_conditions(self):
        indices = self._get_indices()
        for order, index in enumerate(indices):
            pad_a = cast(pad.PropertySinkPad, self.get_pad(f"condition_{index}_A"))
            pad_b = cast(pad.PropertySinkPad, self.get_pad(f"condition_{index}_B"))
            operator_pad = cast(
                pad.PropertySinkPad, self.get_pad(f"condition_{index}_operator")
            )
            if pad_a:
                pad_a.set_id(f"condition_{order}_A")
            if pad_b:
                pad_b.set_id(f"condition_{order}_B")
            if operator_pad:
                operator_pad.set_id(f"condition_{order}_operator")

    def _add_or_remove_condition_pads(self):
        indices = self._get_indices()
        num_conditions_pad = cast(
            pad.PropertySinkPad, self.get_pad_required("num_conditions")
        )

        if not num_conditions_pad.get_value():
            num_conditions_pad.set_value(1)

        num_conditions: int = num_conditions_pad.get_value()

        current_count = len(indices)

        if current_count < num_conditions:
            for i in range(current_count, num_conditions):
                pad_a = pad.PropertySinkPad(
                    id=f"condition_{i}_A",
                    group="condition_A",
                    owner_node=self,
                    default_type_constraints=ALL_ALLOWED_TYPES,
                )
                pad_b = pad.PropertySinkPad(
                    id=f"condition_{i}_B",
                    group="condition_B",
                    owner_node=self,
                    default_type_constraints=ALL_ALLOWED_TYPES,
                )
                operator_pad = pad.PropertySinkPad(
                    id=f"condition_{i}_operator",
                    group="condition_operator",
                    owner_node=self,
                    default_type_constraints=[pad_constraints.Enum(options=[])],
                )
                self.pads.extend([pad_a, pad_b, operator_pad])
        elif current_count > num_conditions:
            for i in range(num_conditions, current_count):
                pad_a = cast(pad.SinkPad, self.get_pad(f"condition_{i}_A"))
                pad_b = cast(pad.SinkPad, self.get_pad(f"condition_{i}_B"))
                operator_pad = cast(
                    pad.SinkPad, self.get_pad(f"condition_{i}_operator")
                )
                if pad_a:
                    self.pads.remove(pad_a)
                    pad_a.disconnect()
                if pad_b:
                    self.pads.remove(pad_b)
                    pad_b.disconnect()
                if operator_pad:
                    self.pads.remove(operator_pad)
                    operator_pad.disconnect()

    def _get_condition_pads(
        self,
    ) -> list[tuple[pad.PropertySinkPad, pad.PropertySinkPad, pad.PropertySinkPad]]:
        condition_pads = []
        for i in self._get_indices():
            pad_a = cast(pad.PropertySinkPad, self.get_pad(f"condition_{i}_A"))
            pad_b = cast(pad.PropertySinkPad, self.get_pad(f"condition_{i}_B"))
            operator_pad = cast(
                pad.PropertySinkPad, self.get_pad(f"condition_{i}_operator")
            )
            pad_a.link_types_to_pad(pad_b)
            condition_pads.append((pad_a, pad_b, operator_pad))
            if not pad_a or not pad_b or not operator_pad:
                logging.error(
                    f"Missing condition pads for index {i}: {pad_a}, {pad_b}, {operator_pad}"
                )
                continue
        return condition_pads

    def _resolve_operators(
        self,
        pad_a: pad.PropertySinkPad,
        pad_b: pad.PropertySinkPad,
        operator_pad: pad.PropertySinkPad,
    ):
        tcs = pad_a.get_type_constraints()
        if tcs is not None and len(tcs) == 1:
            tc = tcs[0]
            if isinstance(tc, pad_constraints.String):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=STRING_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in STRING_COMPARISON_OPERATORS:
                    operator_pad.set_value(STRING_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad_constraints.Integer):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=INTEGER_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in INTEGER_COMPARISON_OPERATORS:
                    operator_pad.set_value(INTEGER_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad_constraints.Float):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=FLOAT_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in FLOAT_COMPARISON_OPERATORS:
                    operator_pad.set_value(FLOAT_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad_constraints.Boolean):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=BOOL_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in BOOL_COMPARISON_OPERATORS:
                    operator_pad.set_value(BOOL_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad_constraints.Enum):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=ENUM_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in ENUM_COMPARISON_OPERATORS:
                    operator_pad.set_value(ENUM_COMPARISON_OPERATORS[0])
            else:
                logging.error(
                    f"Unsupported type for comparison: {tc}. No operator pad will be created."
                )
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=[])]
                )
                operator_pad.set_value(None)

    async def run(self):
        condition_pads = self._get_condition_pads()
        mode_pad = cast(pad.PropertySinkPad, self.get_pad_required("mode"))
        value_pad = cast(pad.PropertySourcePad, self.get_pad_required("value"))

        async def pad_task(pad: pad.PropertySinkPad):
            async for item in pad:
                res = self.resolve_value(
                    condition_pads=condition_pads,
                    mode_pad=mode_pad,
                )
                if value_pad.get_value() != res:
                    value_pad.push_item(res, item.ctx)
                item.ctx.complete()

        await asyncio.gather(
            *[
                pad_task(p)
                for p in [mode_pad] + [p for cps in condition_pads for p in cps]
            ]
        )

    def resolve_value(
        self,
        *,
        condition_pads: list[
            tuple[pad.PropertySinkPad, pad.PropertySinkPad, pad.PropertySinkPad]
        ],
        mode_pad: pad.PropertySinkPad,
    ):
        mode = mode_pad.get_value()
        if mode not in ["AND", "OR"]:
            mode_pad.set_value("AND")
            mode = "AND"

        res = False
        if mode == "AND":
            res = True
        for cps in condition_pads:
            a, b, op = cps
            if a and b and op and op.get_value() is not None:
                result = self.compare_values(a, b, op.get_value())
                if mode == "AND":
                    res = res and result
                    if not res:
                        break
                elif mode == "OR":
                    res = res or result
                    if res:
                        break
        return res

    def compare_values(
        self, pad_a: pad.PropertySinkPad, pad_b: pad.PropertySinkPad, op: str
    ) -> bool:
        a = pad_a.get_value()
        b = pad_b.get_value()
        tcs_a = pad_a.get_type_constraints()
        tcs_b = pad_b.get_type_constraints()
        if not tcs_a or len(tcs_a) != 1 or not tcs_b or len(tcs_b) != 1:
            return False

        tc_a = tcs_a[0]
        tc_b = tcs_b[0]

        if isinstance(tc_a, pad_constraints.String) and isinstance(
            tc_b, pad_constraints.String
        ):
            if not isinstance(a, str) or not isinstance(b, str):
                logging.error(
                    f"Type mismatch for string comparison: {type(a)} vs {type(b)}"
                )
                return False
            if op == "==":
                return a == b
            elif op == "!=":
                return a != b
            elif op == "CONTAINS":
                return a in b
            elif op == "NOT_CONTAINS":
                return a not in b
            elif op == "STARTS_WITH":
                return a.startswith(b)
            elif op == "ENDS_WITH":
                return a.endswith(b)
            else:
                logging.error(f"Unsupported operator for string comparison: {op}")
                return False
        elif isinstance(tc_a, pad_constraints.Integer) and isinstance(
            tc_b, pad_constraints.Integer
        ):
            if not isinstance(a, int) or not isinstance(b, int):
                logging.error(
                    f"Type mismatch for integer comparison: {type(a)} vs {type(b)}"
                )
                return False
            if op == "==":
                return a == b
            elif op == "!=":
                return a != b
            elif op == "<":
                return a < b
            elif op == ">":
                return a > b
            elif op == "<=":
                return a <= b
            elif op == ">=":
                return a >= b
            else:
                logging.error(f"Unsupported operator for integer comparison: {op}")
                return False
        elif isinstance(tc_a, pad_constraints.Float) and isinstance(
            tc_b, pad_constraints.Float
        ):
            if not isinstance(a, float) or not isinstance(b, float):
                logging.error(
                    f"Type mismatch for float comparison: {type(a)} vs {type(b)}"
                )
                return False
            if op == "==":
                return a == b
            elif op == "!=":
                return a != b
            elif op == "<":
                return a < b
            elif op == ">":
                return a > b
            elif op == "<=":
                return a <= b
            elif op == ">=":
                return a >= b
            else:
                logging.error(f"Unsupported operator for float comparison: {op}")
                return False
        elif isinstance(tc_a, pad_constraints.Boolean) and isinstance(
            tc_b, pad_constraints.Boolean
        ):
            if op == "==":
                return a == b
            elif op == "!=":
                return a != b
            else:
                logging.error(f"Unsupported operator for boolean comparison: {op}")
                return False
        elif isinstance(tc_a, pad_constraints.Enum) and isinstance(
            tc_b, pad_constraints.Enum
        ):
            if not isinstance(a, str) or not isinstance(b, str):
                logging.error(
                    f"Type mismatch for enum comparison: {type(a)} vs {type(b)}"
                )
                return False
            if op == "==":
                return a == b
            elif op == "!=":
                return a != b
            else:
                logging.error(f"Unsupported operator for enum comparison: {op}")
                return False

        logging.error(f"Unsupported type for comparison: {tc_a} vs {tc_b}")
        return False
