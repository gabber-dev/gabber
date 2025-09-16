# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from gabber.core import node
from typing import Type
from . import core, llm, stt, tts, local

ALL_NODES: list[Type[node.Node]] = (
    core.ALL_NODES + llm.ALL_NODES + stt.ALL_NODES + tts.ALL_NODES + local.ALL_NODES
)
