# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from gabber.core import pad
from gabber.core.node import Node, NodeMetadata
from jinja2 import Template
from gabber.core.types import pad_constraints


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
                default_type_constraints=[pad_constraints.Integer()],
                value=1,
            )

        jinja_template_pad = cast(pad.PropertySinkPad, self.get_pad("jinja_template"))
        if not jinja_template_pad:
            jinja_template_pad = pad.PropertySinkPad(
                id="jinja_template",
                owner_node=self,
                group="jinja_template",
                default_type_constraints=[pad_constraints.String()],
                value="Hello, {{ property_0 }}!",
            )

        rendered_output = cast(pad.PropertySourcePad, self.get_pad("rendered_output"))
        if not rendered_output:
            rendered_output = pad.PropertySourcePad(
                id="rendered_output",
                owner_node=self,
                group="rendered_output",
                default_type_constraints=[pad_constraints.String()],
                value="",
            )

        property_names: list[pad.PropertySinkPad] = []
        property_values: list[pad.PropertySinkPad] = []
        property_values_sources: list[pad.PropertySourcePad] = []

        num_properties = num_properties_pad.get_value()
        assert isinstance(num_properties, int)
        for i in range(num_properties):
            name_pad = cast(pad.PropertySinkPad, self.get_pad(f"property_name_{i}"))
            if not name_pad:
                name_pad = pad.PropertySinkPad(
                    id=f"property_name_{i}",
                    owner_node=self,
                    group="property_name",
                    default_type_constraints=[pad_constraints.String()],
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
                        pad_constraints.String(),
                        pad_constraints.Integer(),
                        pad_constraints.Float(),
                        pad_constraints.Boolean(),
                        pad_constraints.Enum(),
                    ],
                    value="",
                )
            property_values.append(value_pad)

            value_source = cast(
                pad.PropertySourcePad, self.get_pad(f"property_value_{i}_source")
            )
            if not value_source:
                value_source = pad.PropertySourcePad(
                    id=f"property_value_{i}_source",
                    owner_node=self,
                    group="property_value_source",
                    default_type_constraints=[
                        pad_constraints.String(),
                        pad_constraints.Integer(),
                        pad_constraints.Float(),
                        pad_constraints.Boolean(),
                        pad_constraints.Enum(),
                    ],
                    value="",
                )
                value_pad.link_types_to_pad(value_source)
            property_values_sources.append(value_source)

        # Rebuild the pads list with only the pads we need
        self.pads = cast(
            list[pad.Pad],
            [num_properties_pad, jinja_template_pad]
            + property_names
            + property_values
            + property_values_sources
            + [rendered_output],
        )

        # Do an initial render to set the output value
        # This ensures connected nodes get the proper initial value
        property_pads = list(
            zip(property_names, property_values, property_values_sources)
        )
        jinja_template = jinja_template_pad.get_value()
        assert isinstance(jinja_template, str)
        rendered = self.render_jinja(property_pads, jinja_template)
        rendered_output.set_value(rendered)

    def render_jinja(
        self,
        property_pads: list[
            tuple[pad.PropertySinkPad, pad.PropertySinkPad, pad.PropertySourcePad]
        ],
        template: str,
    ) -> str:
        context: dict[str, object] = {}
        for name_pad, value_pad, _ in property_pads:
            name = name_pad.get_value()
            assert isinstance(name, str)
            if name and value_pad.get_value():
                context[name] = value_pad.get_value()
        jinja_template = Template(template)
        return jinja_template.render(**context)

    async def run(self):
        num_properties_pad = cast(
            pad.PropertySinkPad, self.get_pad_required("num_properties")
        )
        jinja_template_pad = cast(
            pad.PropertySinkPad, self.get_pad_required("jinja_template")
        )
        rendered_output = cast(
            pad.PropertySourcePad, self.get_pad_required("rendered_output")
        )
        num_properties = num_properties_pad.get_value() if num_properties_pad else 1
        num_properties = num_properties if isinstance(num_properties, int) else 1

        property_pads = []
        for i in range(num_properties):
            name_pad = self.get_pad(f"property_name_{i}")
            value_pad = self.get_pad(f"property_value_{i}")
            value_source_pad = self.get_pad(f"property_value_{i}_source")
            if name_pad and value_pad and value_source_pad:
                property_pads.append((name_pad, value_pad, value_source_pad))

        template = (
            jinja_template_pad.get_value()
            if jinja_template_pad
            else "Hello, {{ property_0 }}!"
        )
        assert isinstance(template, str)

        # Do an initial render with current property values
        # This ensures the output is computed even if nothing has been emitted yet
        initial_rendered = self.render_jinja(property_pads, template)
        rendered_output.set_value(initial_rendered)

        async def pad_task(
            value_pad: pad.PropertySinkPad, value_source_pad: pad.PropertySourcePad
        ):
            async for item in value_pad:
                rendered = self.render_jinja(property_pads, template)
                rendered_output.push_item(rendered, item.ctx)
                value_source_pad.push_item(item.value, item.ctx)
                item.ctx.complete()

        tasks: list[asyncio.Task] = []
        for _, value_pad, value_source_pad in property_pads:
            tasks.append(asyncio.create_task(pad_task(value_pad, value_source_pad)))

        await asyncio.gather(*tasks)
