# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
import asyncio
from typing import cast

from core import pad
from core.node import Node, NodeMetadata

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

ALL_ALLOWED_TYPES: list[pad.types.BasePadType] = [
    pad.types.String(),
    pad.types.Integer(),
    pad.types.Float(),
    pad.types.Boolean(),
    pad.types.Enum(),
]


class Compare(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="logic", tags=["compare"])

    async def resolve_pads(self):
        num_conditions = cast(pad.PropertySinkPad, self.get_pad("num_conditions"))
        if not num_conditions:
            num_conditions = pad.PropertySinkPad(
                id="num_conditions",
                group="num_conditions",
                owner_node=self,
                type_constraints=[pad.types.Integer()],
                value=1,
            )

        mode = cast(pad.PropertySinkPad, self.get_pad("mode"))
        if not mode:
            mode = pad.PropertySinkPad(
                id="mode",
                group="mode",
                owner_node=self,
                type_constraints=[pad.types.Enum(options=["AND", "OR"])],
                value="AND",
            )

        value = cast(pad.PropertySourcePad, self.get_pad("value"))
        if not value:
            value = pad.PropertySourcePad(
                id="value",
                group="value",
                owner_node=self,
                type_constraints=[pad.types.Boolean()],
                value=False,
            )

        condition_pads = self._get_condition_pads()

        self.pads = [num_conditions, mode, value] + [
            p for cps in condition_pads for p in cps
        ]

        self._rename_conditions()
        self._add_or_remove_condition_pads()
        condition_pads = self._get_condition_pads()
        for cps in condition_pads:
            a, b, op = cps
            self._resolve_condition_types(a, b, op)

        self.pads = [num_conditions, mode, value] + [
            p for cps in condition_pads for p in cps
        ]

    def _get_indices(self) -> list[int]:
        indices = set[int]()
        for p in self.pads:
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
                    type_constraints=None,
                )
                pad_b = pad.PropertySinkPad(
                    id=f"condition_{i}_B",
                    group="condition_B",
                    owner_node=self,
                    type_constraints=None,
                )
                operator_pad = pad.PropertySinkPad(
                    id=f"condition_{i}_operator",
                    group="condition_operator",
                    owner_node=self,
                    type_constraints=[pad.types.Enum(options=[])],
                )
                self.pads.extend([pad_a, pad_b, operator_pad])
        elif current_count > num_conditions:
            for i in range(num_conditions, current_count):
                pad_a = self.get_pad(f"condition_{i}_A")
                pad_b = self.get_pad(f"condition_{i}_B")
                operator_pad = self.get_pad(f"condition_{i}_operator")
                if pad_a:
                    self.pads.remove(pad_a)
                if pad_b:
                    self.pads.remove(pad_b)
                if operator_pad:
                    self.pads.remove(operator_pad)

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
            condition_pads.append((pad_a, pad_b, operator_pad))
        return condition_pads

    def _resolve_condition_types(
        self,
        pad_a: pad.PropertySinkPad,
        pad_b: pad.PropertySinkPad,
        operator_pad: pad.PropertySinkPad,
    ):
        prev_a = pad_a.get_previous_pad()
        prev_b = pad_b.get_previous_pad()

        tcs_a: list[pad.types.BasePadType] | None = ALL_ALLOWED_TYPES
        if prev_a:
            tcs_a = pad.types.INTERSECTION(
                prev_a.get_type_constraints(), pad_a.get_type_constraints()
            )
            if tcs_a is None:
                tcs_a = ALL_ALLOWED_TYPES
            pad_a.set_type_constraints(tcs_a)

        tcs_b: list[pad.types.BasePadType] | None = None
        if prev_b:
            tcs_b = pad.types.INTERSECTION(
                prev_b.get_type_constraints(), pad_b.get_type_constraints()
            )
            if tcs_b is None:
                tcs_b = ALL_ALLOWED_TYPES
            pad_b.set_type_constraints(tcs_b)

        tcs = pad.types.INTERSECTION(
            tcs_a if tcs_a else pad_a.get_type_constraints(),
            tcs_b if tcs_b else pad_b.get_type_constraints(),
        )

        pad_a.set_type_constraints(tcs)
        pad_b.set_type_constraints(tcs)

        if tcs is not None and len(tcs) == 1:
            tc = tcs[0]
            if isinstance(tc, pad.types.String):
                operator_pad.set_type_constraints(
                    [pad.types.Enum(options=STRING_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in STRING_COMPARISON_OPERATORS:
                    operator_pad.set_value(STRING_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad.types.Integer):
                operator_pad.set_type_constraints(
                    [pad.types.Enum(options=INTEGER_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in INTEGER_COMPARISON_OPERATORS:
                    operator_pad.set_value(INTEGER_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad.types.Float):
                operator_pad.set_type_constraints(
                    [pad.types.Enum(options=FLOAT_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in FLOAT_COMPARISON_OPERATORS:
                    operator_pad.set_value(FLOAT_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad.types.Boolean):
                operator_pad.set_type_constraints(
                    [pad.types.Enum(options=BOOL_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in BOOL_COMPARISON_OPERATORS:
                    operator_pad.set_value(BOOL_COMPARISON_OPERATORS[0])
            elif isinstance(tc, pad.types.Enum):
                operator_pad.set_type_constraints(
                    [pad.types.Enum(options=ENUM_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value() not in ENUM_COMPARISON_OPERATORS:
                    operator_pad.set_value(ENUM_COMPARISON_OPERATORS[0])
            else:
                logging.error(
                    f"Unsupported type for comparison: {tc}. No operator pad will be created."
                )
                operator_pad.set_type_constraints([pad.types.Enum(options=[])])
                operator_pad.set_value(None)
        else:
            operator_pad.set_type_constraints([pad.types.Enum(options=[])])
            operator_pad.set_value(None)

    async def run(self):
        pad_a = cast(pad.PropertySinkPad, self.get_pad_required("A"))
        pad_b = cast(pad.PropertySinkPad, self.get_pad_required("B"))
        operator = cast(pad.PropertySinkPad, self.get_pad_required("operator"))
        value = cast(pad.PropertySourcePad, self.get_pad_required("value"))

        async def pad_task(pad: pad.PropertySinkPad):
            async for item in pad:
                if operator.get_value() is not None:
                    result = self.compare_values(pad_a, pad_b, operator.get_value())
                    value.push_item(result, item.ctx)
                else:
                    value.push_item(False, item.ctx)
                item.ctx.complete()

        await asyncio.gather(
            pad_task(pad_a),
            pad_task(pad_b),
            pad_task(operator),
        )

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

        if isinstance(tc_a, pad.types.String) and isinstance(tc_b, pad.types.String):
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
        elif isinstance(tc_a, pad.types.Integer) and isinstance(
            tc_b, pad.types.Integer
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
        elif isinstance(tc_a, pad.types.Float) and isinstance(tc_b, pad.types.Float):
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
        elif isinstance(tc_a, pad.types.Boolean) and isinstance(
            tc_b, pad.types.Boolean
        ):
            if op == "==":
                return a == b
            elif op == "!=":
                return a != b
            else:
                logging.error(f"Unsupported operator for boolean comparison: {op}")
                return False
        elif isinstance(tc_a, pad.types.Enum) and isinstance(tc_b, pad.types.Enum):
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
