# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Annotated, Literal
from ..generated import runtime
from pydantic import Field


@dataclass
class ConnectionDetails:
    token: str
    url: str


@dataclass
class SubscribeParams:
    output_or_publish_node: str


ConnectionState = Literal[
    "disconnected", "connecting", "waiting_for_engine", "connected"
]


RuntimeRequestPayload = Annotated[
    runtime.RuntimeRequestPayloadGetValue
    | runtime.RuntimeRequestPayloadLockPublisher
    | runtime.RuntimeRequestPayloadPushValue,
    Field(discriminator="type"),
]

RuntimeResponsePayload = Annotated[
    runtime.RuntimeResponsePayloadGetValue
    | runtime.RuntimeResponsePayloadLockPublisher
    | runtime.RuntimeResponsePayloadPushValue,
    Field(discriminator="type"),
]

PadValue = Annotated[
    runtime.PadValueString
    | runtime.PadValueInteger
    | runtime.PadValueFloat
    | runtime.PadValueBoolean
    | runtime.PadValueTrigger
    | runtime.PadValueAudioClip
    | runtime.PadValueVideoClip,
    Field(discriminator="type"),
]
