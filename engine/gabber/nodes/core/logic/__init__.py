# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from . import state_machine
from .enum_switch_trigger import EnumSwitchTrigger
from .enum_switch_property import EnumSwitchProperty
from .gate import Gate
from .filter import Filter
from .compare import Compare
from .and_node import And
from .or_node import Or


ALL_NODES = [
    EnumSwitchTrigger,
    EnumSwitchProperty,
    Gate,
    Compare,
    And,
    Or,
    Filter,
] + state_machine.ALL_NODES
