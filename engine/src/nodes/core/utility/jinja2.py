# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import pad
from core.node import Node, NodeMetadata


class Jinja2(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Template strings using Jinja2"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="utility", tags=[])

    def resolve_pads(self):
        num_properties_pad = cast(pad.PropertySinkPad, self.get_pad("num_properties"))
        if not num_properties_pad:
            num_properties_pad = pad.PropertySinkPad(
                id="num_properties",
                owner_node=self,
                group="num_properties",
                default_type_constraints=[pad.types.Integer()],
                value=1,
            )

        jinja_template_pad = cast(pad.PropertySinkPad, self.get_pad("jinja_template"))
        if not jinja_template_pad:
            jinja_template_pad = pad.PropertySinkPad(
                id="jinja_template",
                owner_node=self,
                group="jinja_template",
                default_type_constraints=[pad.types.String()],
                value="Hello, {{ property_0 }}!",
            )

        rendered_output = cast(pad.PropertySourcePad, self.get_pad("rendered_output"))
        if not rendered_output:
            rendered_output = pad.PropertySourcePad(
                id="rendered_output",
                owner_node=self,
                group="rendered_output",
                default_type_constraints=[pad.types.String()],
                value="",
            )

        property_names: list[pad.PropertySinkPad] = []
        property_values: list[pad.PropertySinkPad] = []

        for i in range(num_properties_pad.get_value()):
            name_pad = cast(pad.PropertySinkPad, self.get_pad(f"property_name_{i}"))
            if not name_pad:
                name_pad = pad.PropertySinkPad(
                    id=f"property_name_{i}",
                    owner_node=self,
                    group="property_name",
                    default_type_constraints=[pad.types.String()],
                    value=f"property_{i}",
                )
            property_names.append(name_pad)

            value_pad = cast(pad.PropertySinkPad, self.get_pad(f"property_value_{i}"))
            if not value_pad:
                value_pad = pad.PropertySinkPad(
                    id=f"property_value_{i}",
                    owner_node=self,
                    group="property_value",
                    default_type_constraints=[
                        pad.types.String(),
                        pad.types.Integer(),
                        pad.types.Float(),
                    ],
                    value="",
                )
            property_values.append(value_pad)

        for p in self.pads:
            if p.get_group() == "property_name" and p not in property_names:
                self.pads.remove(p)

            if p.get_group() == "property_value" and p not in property_values:
                self.pads.remove(p)

        self.pads = cast(
            list[pad.Pad],
            [num_properties_pad, jinja_template_pad]
            + property_names
            + property_values
            + [rendered_output],
        )

    async def run(self):
        pass
