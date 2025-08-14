# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from . import debug, logic, media, primitive, sub_graph, timing, tool, utility, web

ALL_NODES = (
    debug.ALL_NODES
    + media.ALL_NODES
    + primitive.ALL_NODES
    + tool.ALL_NODES
    + logic.ALL_NODES
    + utility.ALL_NODES
    + sub_graph.ALL_NODES
    + web.ALL_NODES
    + timing.ALL_NODES
)
