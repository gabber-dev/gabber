# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from .kitten_tts import KittenTTS
from .local_llm import LocalLLM
from .local_stt import LocalSTT
from .local_viseme import LocalViseme

ALL_NODES = [
    # KittenTTS,
    LocalLLM,
    LocalSTT,
    LocalViseme,
]
