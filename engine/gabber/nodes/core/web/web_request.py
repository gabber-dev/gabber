# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from dataclasses import dataclass
from typing import Any, cast
import aiohttp
from gabber.core import pad
from gabber.core.node import Node


class WebRequest(Node):
    def resolve_pads(self):
        url = cast(pad.PropertySinkPad, self.get_pad("url"))
        if not url:
            url = pad.PropertySinkPad(
                id="url",
                group="url",
                owner_node=self,
                default_type_constraints=[pad.types.String()],
                value="https://example-url.test",
            )

        method = cast(pad.PropertySinkPad, self.get_pad("method"))
        if not method:
            method = pad.PropertySinkPad(
                id="method",
                group="method",
                owner_node=self,
                default_type_constraints=[
                    pad.types.Enum(options=["GET", "POST", "PUT", "PATCH", "DELETE"])
                ],
                value="GET",
            )

        max_retries = cast(pad.PropertySinkPad, self.get_pad("max_retries"))
        if not max_retries:
            max_retries = pad.PropertySinkPad(
                id="max_retries",
                group="max_retries",
                owner_node=self,
                default_type_constraints=[pad.types.Integer()],
                value=3,
            )

        authorization_type = cast(
            pad.PropertySinkPad, self.get_pad("authorization_type")
        )
        if not authorization_type:
            authorization_type = pad.PropertySinkPad(
                id="authorization_type",
                group="authorization_type",
                owner_node=self,
                default_type_constraints=[
                    pad.types.Enum(options=["None", "Bearer Token", "API Key"])
                ],
                value="None",
            )

        response_type = cast(pad.PropertySinkPad, self.get_pad("response_type"))
        if not response_type:
            response_type = pad.PropertySinkPad(
                id="response_type",
                group="response_type",
                owner_node=self,
                default_type_constraints=[
                    pad.types.Enum(
                        options=[
                            "application/json",
                            "text/plain",
                        ]
                    )
                ],
                value="application/json",
            )

        bearer_token = cast(pad.PropertySinkPad, self.get_pad("bearer_token"))
        if not bearer_token:
            bearer_token = pad.PropertySinkPad(
                id="bearer_token",
                group="bearer_token",
                owner_node=self,
                default_type_constraints=[pad.types.Secret(options=self.secrets)],
                value="",
            )

        api_header_key = cast(pad.PropertySinkPad, self.get_pad("api_header_key"))
        if not api_header_key:
            api_header_key = pad.PropertySinkPad(
                id="api_header_key",
                group="api_header_key",
                owner_node=self,
                default_type_constraints=[pad.types.String()],
                value="",
            )

        api_value = cast(pad.PropertySinkPad, self.get_pad("api_value"))
        if not api_value:
            api_value = pad.PropertySinkPad(
                id="api_value",
                group="api_value",
                owner_node=self,
                default_type_constraints=[pad.types.Secret(options=self.secrets)],
                value="",
            )

        response = cast(pad.StatelessSourcePad, self.get_pad("response"))
        if not response:
            response = pad.StatelessSourcePad(
                id="response",
                group="response",
                owner_node=self,
                default_type_constraints=None,
            )

        error_response = cast(pad.StatelessSourcePad, self.get_pad("error_response"))
        if not error_response:
            error_response = pad.StatelessSourcePad(
                id="error_response",
                group="error_response",
                owner_node=self,
                default_type_constraints=[pad.types.String()],
            )

        request_body = cast(pad.StatelessSinkPad, self.get_pad("request_body"))
        if not request_body:
            request_body = pad.StatelessSinkPad(
                id="request_body",
                group="request_body",
                owner_node=self,
                default_type_constraints=[pad.types.Object()],
            )

        query_params = cast(pad.StatelessSinkPad, self.get_pad("query_params"))
        if not query_params:
            query_params = pad.StatelessSinkPad(
                id="query_params",
                group="query_params",
                owner_node=self,
                default_type_constraints=[pad.types.Object()],
            )

        fixed_pads: list[pad.Pad] = [
            url,
            method,
            max_retries,
            authorization_type,
            response_type,
            request_body,
            response,
            error_response,
            query_params,
        ]

        output_tc: list[pad.types.BasePadType] = []
        if response_type.get_value() == "application/json":
            output_tc = [pad.types.Object()]
        elif response_type.get_value() == "text/plain":
            output_tc = [pad.types.String()]
        else:
            output_tc = [pad.types.Object()]

        response.set_default_type_constraints(output_tc)

        dynamic_pads: list[pad.Pad] = []

        if authorization_type.get_value() == "Bearer Token":
            dynamic_pads.append(bearer_token)
        elif authorization_type.get_value() == "API Key":
            dynamic_pads.append(api_header_key)
            dynamic_pads.append(api_value)
        self.pads = fixed_pads + dynamic_pads

    @classmethod
    def get_description(cls) -> str:
        return "Emits a single trigger when the run starts."

    async def run(self):
        response_type = cast(
            pad.PropertySinkPad, self.get_pad_required("response_type")
        )
        url_pad = cast(pad.PropertySinkPad, self.get_pad_required("url"))
        method_pad = cast(pad.PropertySinkPad, self.get_pad_required("method"))
        method = method_pad.get_value() or "GET"
        max_retries = cast(pad.PropertySinkPad, self.get_pad_required("max_retries"))
        authorization_type = cast(
            pad.PropertySinkPad, self.get_pad_required("authorization_type")
        )
        bearer_token = cast(pad.PropertySinkPad, self.get_pad("bearer_token"))
        api_header_key = cast(pad.PropertySinkPad, self.get_pad("api_header_key"))
        api_value = cast(pad.PropertySinkPad, self.get_pad("api_value"))
        request_body = cast(pad.StatelessSinkPad, self.get_pad_required("request_body"))
        # TODO: Handle query parameters if needed
        # query_params = cast(pad.StatelessSinkPad, self.get_pad("query_params"))
        response = cast(pad.StatelessSourcePad, self.get_pad_required("response"))
        error_response = cast(
            pad.StatelessSourcePad, self.get_pad_required("error_response")
        )

        async def handle_response(
            resp: aiohttp.ClientResponse, ctx: pad.RequestContext
        ):
            if response_type.get_value() == "application/json":
                json_response = await resp.json()
                response.push_item(json_response, ctx)
            elif response_type.get_value() == "text/plain":
                text_response = await resp.text()
                response.push_item(text_response, ctx)

        async def perform_request(req: dict[str, Any], ctx: pad.RequestContext):
            url = url_pad.get_value()
            try:
                if method == "GET":
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            await handle_response(resp, ctx)
                            return resp
                        else:
                            raise ErrorResponse(
                                message=await resp.text(),
                                status_code=resp.status,
                            )
                elif method == "POST":
                    async with session.post(url, json=req, headers=headers) as resp:
                        if resp.status == 200:
                            await handle_response(resp, ctx)
                        else:
                            raise ErrorResponse(
                                message=await resp.text(),
                                status_code=resp.status,
                            )
                elif method == "PUT":
                    async with session.put(url, json=req, headers=headers) as resp:
                        if resp.status == 200:
                            await handle_response(resp, ctx)
                        else:
                            raise ErrorResponse(
                                message=await resp.text(),
                                status_code=resp.status,
                            )
                elif method == "PATCH":
                    async with session.patch(url, json=req, headers=headers) as resp:
                        if resp.status == 200:
                            await handle_response(resp, ctx)
                        else:
                            raise ErrorResponse(
                                message=await resp.text(),
                                status_code=resp.status,
                            )
                elif method == "DELETE":
                    async with session.delete(url, headers=headers) as resp:
                        if resp.status == 200:
                            await handle_response(resp, ctx)
                        else:
                            raise ErrorResponse(
                                message=await resp.text(),
                                status_code=resp.status,
                            )
                else:
                    raise ErrorResponse(
                        message=f"Unsupported HTTP method: {method_pad}",
                        status_code=400,
                    )
            except Exception as e:
                raise ErrorResponse(
                    message=str(e),
                    status_code=500,
                )

        async for req in request_body:
            last_error: str | None = None
            last_error_code: int | None = None
            async with aiohttp.ClientSession() as session:
                method_pad = method_pad.get_value()
                headers = {}

                # Resolve and set headers based on authorization type
                if authorization_type.get_value() == "API Key":
                    api_key_name = api_value.get_value()
                    api_key_value = await self.secret_provider.resolve_secret(
                        api_key_name
                    )
                    headers = {
                        api_header_key.get_value(): api_key_value,
                    }
                elif authorization_type.get_value() == "Bearer Token":
                    bearer_token_name = bearer_token.get_value()
                    bearer_token_value = await self.secret_provider.resolve_secret(
                        bearer_token_name
                    )
                    headers = {
                        "Authorization": f"Bearer {bearer_token_value}",
                    }
                retries = 0

                while retries < max_retries.get_value():
                    try:
                        await perform_request(req.value, req.ctx)
                        break
                    except ErrorResponse as e:
                        last_error = e.message
                        last_error_code = e.status_code
                    retries += 1

            if last_error is not None:
                error_response.push_item(
                    {
                        "error": last_error,
                        "status_code": last_error_code,
                    },
                    req.ctx,
                )
            req.ctx.complete()


@dataclass
class ErrorResponse(Exception):
    message: str
    status_code: int
