#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0


set -e
echo "Starting unmute STT worker..."

export RUST_LOG=trace
export CUDA_LAUNCH_BLOCKING=1
export CUDA_LOG_LEVEL=5
moshi-server worker --config ~/delayed-streams-modeling/configs/config-stt-en_fr-hf.toml