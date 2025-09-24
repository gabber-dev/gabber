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

import asyncio
import colorsys
import json
import logging
import uuid
from time import perf_counter

import aiofiles
import aiohttp
import numpy as np

from gabber import (
    ConnectionDetails,
    Engine,
    VideoFormat,
    VideoFrame,
    VirtualCamera,
    Subscription,
)


async def draw_color_cycle(
    width: int, height: int, cam: VirtualCamera
) -> np.typing.NDArray[np.uint8]:
    rgba_frame = bytearray(width * height * 4)
    arr = np.frombuffer(rgba_frame, dtype=np.uint8)

    hue = 0.0
    next_frame_time = asyncio.get_event_loop().time() + 1 / 30

    while True:
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        rgb = [(x * 255) for x in rgb]  # type: ignore

        rgba_color = np.array(rgb + [255], dtype=np.uint8)
        arr.flat[::4] = rgba_color[0]
        arr.flat[1::4] = rgba_color[1]
        arr.flat[2::4] = rgba_color[2]
        arr.flat[3::4] = rgba_color[3]

        hue = (hue + 1 / 30) % 1.0

        frame = VideoFrame(arr, width=width, height=height, format=VideoFormat.RGBA)
        cam.push(frame)

        await asyncio.sleep(next_frame_time - perf_counter())
        # await asyncio.sleep(1 / FPS - code_duration)


async def get_connection_details(run_id: str):
    async with aiofiles.open("graph.json", mode="r") as graph_json:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/app/run",
                json={
                    "graph": json.loads(await graph_json.read()),
                    "run_id": run_id,
                },
            ) as resp:
                if resp.status != 200:
                    raise ValueError("Failed to get connection details")

                resp_json = await resp.json()
                res = ConnectionDetails(
                    token=resp_json["connection_details"]["token"],
                    url=resp_json["connection_details"]["url"],
                )
                return res


async def sub_video(sub: Subscription):
    video_it = await sub.iterate_video()
    async for frame in video_it:
        print(f"Received video frame: {frame}")


async def main():
    def on_connection_state_change(state: str):
        print(f"Connection state changed to: {state}")

    run_id = str(uuid.uuid4())
    engine = Engine(on_connection_state_change=on_connection_state_change)

    await engine.connect(connection_details=await get_connection_details(run_id))
    tick_pad = engine.get_property_pad("ticker_0", "tick")
    tick_pad.on("value", lambda data: print(f"Tick: {data}"))

    print(f"Debug Link: http://localhost:3000/debug/{run_id}")

    virtual_cam = VirtualCamera(width=640, height=480, format=VideoFormat.RGBA)

    pub = await engine.publish_to_node(publish_node="publish_0", device=virtual_cam)
    sub = await engine.subscribe_to_node(output_or_publish_node="output_0")

    sub_video_task = asyncio.create_task(sub_video(sub))
    await draw_color_cycle(640, 480, virtual_cam)
    sub_video_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
