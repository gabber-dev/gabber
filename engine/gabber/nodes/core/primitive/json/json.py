# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
from typing import cast

from gabber.core import node, pad
from gabber.core.node import NodeMetadata


class Json(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Stores and manages Json object values"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="primitive", tags=["json"])

    def resolve_pads(self):
        emit = cast(pad.StatelessSinkPad | None, self.get_pad("emit"))
        if not emit:
            emit = pad.StatelessSinkPad(
                id="emit",
                owner_node=self,
                group="emit",
                default_type_constraints=[pad.types.Trigger()],
            )

        value = cast(pad.PropertySourcePad | None, self.get_pad("value"))
        if not value:
            value = pad.PropertySourcePad(
                id="value",
                group="value",
                owner_node=self,
                default_type_constraints=[pad.types.Object()],
                value="",
            )

        # Add optional string input pad for JSON strings
        string_input = cast(pad.StatelessSinkPad | None, self.get_pad("string_input"))
        if not string_input:
            string_input = pad.StatelessSinkPad(
                id="string_input",
                group="string_input",
                owner_node=self,
                default_type_constraints=[pad.types.String()],
            )

        # Only set pads if they don't already exist to preserve values from editor
        if not self.pads:
            self.pads = [emit, value, string_input]
        else:
            # Update existing pads list if needed
            existing_emit = self.get_pad("emit")
            existing_value = self.get_pad("value")
            existing_string_input = self.get_pad("string_input")
            if not existing_emit:
                self.pads.append(emit)
            if not existing_value:
                self.pads.append(value)
            if not existing_string_input:
                self.pads.append(string_input)

    async def run(self):
        emit = cast(pad.StatelessSinkPad, self.get_pad_required("emit"))
        value = cast(pad.PropertySourcePad, self.get_pad_required("value"))
        string_input = cast(pad.StatelessSinkPad | None, self.get_pad("string_input"))

        # Auto-trigger: Check if we have a connected string source and process it on startup
        if string_input and string_input.get_previous_pad():
            string_source = string_input.get_previous_pad()
            if hasattr(string_source, 'get_value'):
                try:
                    import json
                    json_string = string_source.get_value()
                    parsed_json = json.loads(json_string)
                    
                    # Update the value pad with parsed JSON
                    value.set_value(parsed_json)
                except json.JSONDecodeError:
                    pass
                except Exception:
                    pass

        async def string_input_task():
            if string_input:
                async for item in string_input:
                    try:
                        json_string = item.value
                        parsed_json = json.loads(json_string)
                        
                        # Update the value pad with parsed JSON
                        value.set_value(parsed_json)
                        
                        # Emit the parsed JSON
                        value.push_item(parsed_json, item.ctx)
                        item.ctx.complete()
                    except json.JSONDecodeError:
                        item.ctx.complete()

        async def emit_task():
            async for item in emit:
                current_val = value.get_value()
                value.push_item(current_val, item.ctx)
                item.ctx.complete()

        # Run both tasks concurrently
        tasks = [emit_task()]
        if string_input:
            tasks.append(string_input_task())
        
        await asyncio.gather(*tasks)
