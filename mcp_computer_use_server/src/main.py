#!/usr/bin/env python3

import argparse
import asyncio
import logging
from typing import Literal, Union

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
import time


# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("computer-use-server")

# Initialize mouse and keyboard controllers
mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()


# Pydantic models for input validation
class ClickRequest(BaseModel):
    """Request model for mouse click operations."""

    x: int = Field(..., description="X coordinate for the click")
    y: int = Field(..., description="Y coordinate for the click")
    button: Literal["left", "right", "middle"] = Field(
        default="left", description="Mouse button to click"
    )
    clicks: int = Field(default=1, description="Number of clicks", ge=1, le=10)
    interval: float = Field(
        default=0.1, description="Interval between clicks in seconds", ge=0.0, le=2.0
    )


class ScrollRequest(BaseModel):
    """Request model for mouse scroll operations."""

    x: int = Field(..., description="X coordinate for the scroll")
    y: int = Field(..., description="Y coordinate for the scroll")
    dx: int = Field(default=0, description="Horizontal scroll amount")
    dy: int = Field(..., description="Vertical scroll amount")


class TypeRequest(BaseModel):
    """Request model for keyboard typing operations."""

    text: str = Field(..., description="Text to type")
    interval: float = Field(
        default=0.05,
        description="Interval between keystrokes in seconds",
        ge=0.0,
        le=1.0,
    )


class KeyRequest(BaseModel):
    """Request model for special key operations."""

    key: str = Field(
        ..., description="Special key to press (e.g., 'enter', 'tab', 'escape')"
    )
    hold_duration: float = Field(
        default=0.1, description="How long to hold the key in seconds", ge=0.0, le=5.0
    )


# Helper function to get mouse button
def get_mouse_button(button_name: str) -> Button:
    """Convert button name string to pynput Button enum."""
    button_map = {
        "left": Button.left,
        "right": Button.right,
        "middle": Button.middle,
    }
    return button_map.get(button_name.lower(), Button.left)


# Helper function to get special keys
def get_special_key(key_name: str) -> Union[Key, str]:
    """Convert key name string to pynput Key enum or return as string."""
    key_map = {
        "enter": Key.enter,
        "return": Key.enter,
        "tab": Key.tab,
        "space": Key.space,
        "escape": Key.esc,
        "esc": Key.esc,
        "shift": Key.shift,
        "ctrl": Key.ctrl,
        "control": Key.ctrl,
        "alt": Key.alt,
        "cmd": Key.cmd,
        "backspace": Key.backspace,
        "delete": Key.delete,
        "home": Key.home,
        "end": Key.end,
        "page_up": Key.page_up,
        "page_down": Key.page_down,
        "up": Key.up,
        "down": Key.down,
        "left": Key.left,
        "right": Key.right,
        "f1": Key.f1,
        "f2": Key.f2,
        "f3": Key.f3,
        "f4": Key.f4,
        "f5": Key.f5,
        "f6": Key.f6,
        "f7": Key.f7,
        "f8": Key.f8,
        "f9": Key.f9,
        "f10": Key.f10,
        "f11": Key.f11,
        "f12": Key.f12,
    }
    return key_map.get(key_name.lower(), key_name)


@mcp.tool()
def click(request: ClickRequest) -> str:
    """
    Perform a mouse click at the specified coordinates.

    Args:
        request: ClickRequest containing x, y coordinates, button type, clicks count, and interval

    Returns:
        Success message with click details
    """
    try:
        button = get_mouse_button(request.button)

        # Move to position
        mouse_controller.position = (request.x, request.y)
        time.sleep(0.05)  # Small delay to ensure position is set

        # Perform clicks
        for i in range(request.clicks):
            mouse_controller.click(button)
            if i < request.clicks - 1:  # Don't wait after the last click
                time.sleep(request.interval)

        logger.info(
            f"Clicked {request.button} button {request.clicks} time(s) at ({request.x}, {request.y})"
        )
        return f"Successfully clicked {request.button} button {request.clicks} time(s) at position ({request.x}, {request.y})"

    except Exception as e:
        error_msg = f"Failed to click: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def scroll(request: ScrollRequest) -> str:
    """
    Perform a mouse scroll at the specified coordinates.

    Args:
        request: ScrollRequest containing x, y coordinates and scroll amounts

    Returns:
        Success message with scroll details
    """
    try:
        # Move to position
        mouse_controller.position = (request.x, request.y)
        time.sleep(0.05)  # Small delay to ensure position is set

        # Perform scroll
        mouse_controller.scroll(request.dx, request.dy)

        logger.info(
            f"Scrolled dx={request.dx}, dy={request.dy} at ({request.x}, {request.y})"
        )
        return f"Successfully scrolled dx={request.dx}, dy={request.dy} at position ({request.x}, {request.y})"

    except Exception as e:
        error_msg = f"Failed to scroll: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def type_text(request: TypeRequest) -> str:
    """
    Type the specified text using the keyboard.

    Args:
        request: TypeRequest containing text to type and interval between keystrokes

    Returns:
        Success message with typing details
    """
    try:
        # Type each character with specified interval
        for char in request.text:
            keyboard_controller.type(char)
            if request.interval > 0:
                time.sleep(request.interval)

        logger.info(f"Typed text: '{request.text}' with interval {request.interval}s")
        return f"Successfully typed text: '{request.text}' ({len(request.text)} characters)"

    except Exception as e:
        error_msg = f"Failed to type text: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def press_key(request: KeyRequest) -> str:
    """
    Press a special key (e.g., Enter, Tab, Escape, etc.).

    Args:
        request: KeyRequest containing key name and hold duration

    Returns:
        Success message with key press details
    """
    try:
        key = get_special_key(request.key)

        # Press and hold the key
        keyboard_controller.press(key)
        time.sleep(request.hold_duration)
        keyboard_controller.release(key)

        logger.info(f"Pressed key '{request.key}' for {request.hold_duration}s")
        return f"Successfully pressed key '{request.key}' for {request.hold_duration} seconds"

    except Exception as e:
        error_msg = f"Failed to press key: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def get_mouse_position() -> str:
    """
    Get the current mouse cursor position.

    Returns:
        Current mouse position as string
    """
    try:
        position = mouse_controller.position
        logger.info(f"Current mouse position: {position}")
        return f"Current mouse position: ({position[0]}, {position[1]})"

    except Exception as e:
        error_msg = f"Failed to get mouse position: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def move_mouse(x: int, y: int) -> str:
    """
    Move the mouse cursor to the specified coordinates.

    Args:
        x: Target X coordinate
        y: Target Y coordinate

    Returns:
        Success message with new position
    """
    try:
        mouse_controller.position = (x, y)
        time.sleep(0.05)  # Small delay to ensure position is set

        logger.info(f"Moved mouse to ({x}, {y})")
        return f"Successfully moved mouse to position ({x}, {y})"

    except Exception as e:
        error_msg = f"Failed to move mouse: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def main():
    """Main function to run the MCP server."""
    parser = argparse.ArgumentParser(description="Computer Use MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    logger.info("Starting Computer Use MCP Server...")
    logger.info(
        "Available tools: click, scroll, type_text, press_key, get_mouse_position, move_mouse"
    )

    # Run the server
    await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
