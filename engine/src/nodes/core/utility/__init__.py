# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from .auto_convert import AutoConvert
from .entry import Entry
from .enum_switch import PropertyEnumSwitch
from .stateless_enum_switch import StatelessEnumSwitch
from .merge import Merge
from .type_constraint import TypeConstraint
from .unpack_object import UnpackObject
from .wait_for_request import WaitForRequest
from .noop import Noop

ALL_NODES = [
    Merge,
    WaitForRequest,
    Entry,
    TypeConstraint,
    AutoConvert,
    PropertyEnumSwitch,
    StatelessEnumSwitch,
    UnpackObject,
    Noop,
]
