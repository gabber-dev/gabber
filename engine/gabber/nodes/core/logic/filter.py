# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast, Any

from gabber.core import pad
from gabber.core.node import Node, NodeMetadata
from gabber.core.types import pad_constraints, runtime

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

ALL_PAD_TYPES = [
    pad_constraints.String(),
    pad_constraints.Integer(),
    pad_constraints.Float(),
    pad_constraints.Boolean(),
    pad_constraints.Enum(),
]

ALL_RUNTIME_TYPES = str | int | float | bool | runtime.Enum


class Filter(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="logic", tags=["gate"])

    def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad[ALL_RUNTIME_TYPES], self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                default_type_constraints=ALL_PAD_TYPES,
            )

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=ALL_PAD_TYPES,
            )

        operator = cast(pad.PropertySinkPad[runtime.Enum], self.get_pad("operator"))
        if not operator:
            operator = pad.PropertySinkPad[runtime.Enum](
                id="operator",
                group="operator",
                owner_node=self,
                default_type_constraints=[pad_constraints.Enum()],
                value=runtime.Enum(value="=="),
            )

        compare_value = cast(pad.PropertySinkPad, self.get_pad("compare_value"))
        if not compare_value:
            compare_value = pad.PropertySinkPad(
                id="compare_value",
                group="compare_value",
                owner_node=self,
                default_type_constraints=ALL_PAD_TYPES,
                value="",
            )

        sink.link_types_to_pad(source)
        sink.link_types_to_pad(compare_value)
        self._resolve_operators(sink, operator)
        self.pads = [sink, source, operator, compare_value]

    def _resolve_operators(
        self,
        pad_a: pad.SinkPad[ALL_RUNTIME_TYPES],
        operator_pad: pad.PropertySinkPad[runtime.Enum],
    ):
        tcs = pad_a.get_type_constraints()
        if tcs is not None and len(tcs) == 1:
            tc = tcs[0]
            if isinstance(tc, pad_constraints.String):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=STRING_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value().value not in STRING_COMPARISON_OPERATORS:
                    operator_pad.set_value(
                        runtime.Enum(value=STRING_COMPARISON_OPERATORS[0])
                    )
            elif isinstance(tc, pad_constraints.Integer):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=INTEGER_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value().value not in INTEGER_COMPARISON_OPERATORS:
                    operator_pad.set_value(
                        runtime.Enum(value=INTEGER_COMPARISON_OPERATORS[0])
                    )
            elif isinstance(tc, pad_constraints.Float):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=FLOAT_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value().value not in FLOAT_COMPARISON_OPERATORS:
                    operator_pad.set_value(
                        runtime.Enum(value=FLOAT_COMPARISON_OPERATORS[0])
                    )
            elif isinstance(tc, pad_constraints.Boolean):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=BOOL_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value().value not in BOOL_COMPARISON_OPERATORS:
                    operator_pad.set_value(
                        runtime.Enum(value=BOOL_COMPARISON_OPERATORS[0])
                    )
            elif isinstance(tc, pad_constraints.Enum):
                operator_pad.set_default_type_constraints(
                    [pad_constraints.Enum(options=ENUM_COMPARISON_OPERATORS)]
                )
                if operator_pad.get_value().value not in ENUM_COMPARISON_OPERATORS:
                    operator_pad.set_value(
                        runtime.Enum(value=ENUM_COMPARISON_OPERATORS[0])
                    )

    async def run(self):
        sink = cast(
            pad.StatelessSinkPad[ALL_RUNTIME_TYPES], self.get_pad_required("sink")
        )
        source = cast(
            pad.StatelessSourcePad[ALL_RUNTIME_TYPES], self.get_pad_required("source")
        )
        operator_pad = cast(
            pad.PropertySinkPad[runtime.Enum], self.get_pad_required("operator")
        )
        compare_pad = cast(
            pad.PropertySinkPad[ALL_RUNTIME_TYPES],
            self.get_pad_required("compare_value"),
        )

        async def process_sink():
            async for item in sink:
                tcs_a = sink.get_type_constraints()
                tcs_b = compare_pad.get_type_constraints()
                if tcs_a and len(tcs_a) == 1 and tcs_b and len(tcs_b) == 1:
                    if self.compare_values(
                        item.value,
                        tcs_a[0],
                        compare_pad.get_value(),
                        tcs_b[0],
                        operator_pad.get_value().value,
                    ):
                        source.push_item(item.value, item.ctx)
                item.ctx.complete()

        async def pad_task(pad: pad.PropertySinkPad):
            async for item in pad:
                item.ctx.complete()

        await asyncio.gather(
            process_sink(),
            pad_task(operator_pad),
            pad_task(compare_pad),
        )

    def compare_values(
        self,
        a: Any,
        tc_a: pad_constraints.BasePadType,
        b: Any,
        tc_b: pad_constraints.BasePadType,
        op: str,
    ) -> bool:
        if not isinstance(tc_a, type(tc_b)):
            logging.error(f"Type mismatch between tc_a and tc_b: {tc_a} vs {tc_b}")
            return False

        if isinstance(tc_a, pad_constraints.String):
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
        elif isinstance(tc_a, pad_constraints.Integer):
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
        elif isinstance(tc_a, pad_constraints.Float):
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
        elif isinstance(tc_a, pad_constraints.Boolean):
            if not isinstance(a, bool) or not isinstance(b, bool):
                logging.error(
                    f"Type mismatch for boolean comparison: {type(a)} vs {type(b)}"
                )
                return False
            if op == "==":
                return a == b
            elif op == "!=":
                return a != b
            else:
                logging.error(f"Unsupported operator for boolean comparison: {op}")
                return False
        elif isinstance(tc_a, pad_constraints.Enum):
            if not isinstance(a, runtime.Enum) or not isinstance(b, runtime.Enum):
                logging.error(
                    f"Type mismatch for enum comparison: {type(a)} vs {type(b)}"
                )
                return False
            if op == "==":
                return a.value == b.value
            elif op == "!=":
                return a.value != b.value
            else:
                logging.error(f"Unsupported operator for enum comparison: {op}")
                return False

        logging.error(f"Unsupported type for comparison: {tc_a} vs {tc_b}")
        return False
