import asyncio
import colorsys
import json

import aiofiles
import aiohttp
import numpy as np
from time import perf_counter

from gabber import ConnectionDetails, Engine, VirtualCamera, VideoFrame, VideoFormat


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


async def get_connection_details():
    async with aiofiles.open("graph.json", mode="r") as graph_json:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/app/run",
                json={
                    "graph": json.loads(await graph_json.read()),
                    "run_id": "test-run",
                },
            ) as resp:
                if resp.status != 200:
                    raise ValueError("Failed to get connection details")

                print("NEIL", await resp.text())

                resp_json = await resp.json()
                res = ConnectionDetails(
                    token=resp_json["connection_details"]["token"],
                    url=resp_json["connection_details"]["url"],
                )
                return res


async def main():
    def on_connection_state_change(state: str):
        print(f"Connection state changed to: {state}")

    engine = Engine(on_connection_state_change=on_connection_state_change)

    await engine.connect(connection_details=await get_connection_details())
    tick_pad = engine.get_property_pad("ticker_0", "tick")
    tick_pad.on("data", lambda data: print(f"Tick: {data}"))

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
