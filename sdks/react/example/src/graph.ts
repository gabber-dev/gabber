/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

export const GRAPH = {
        "nodes": [
            {
                "id": "publish_0",
                "type": "Publish",
                "editor_name": "Publish 0",
                "editor_position": [
                    -36.0,
                    312.0
                ],
                "editor_dimensions": [
                    256.0,
                    422.0
                ],
                "pads": [
                    {
                        "id": "audio",
                        "group": "audio",
                        "type": "StatelessSourcePad",
                        "default_allowed_types": [
                            {
                                "type": "audio"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "audio"
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "video",
                        "group": "video",
                        "type": "StatelessSourcePad",
                        "default_allowed_types": [
                            {
                                "type": "video"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "video"
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "audio_enabled",
                        "group": "audio_enabled",
                        "type": "PropertySourcePad",
                        "default_allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "value": false,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "video_enabled",
                        "group": "video_enabled",
                        "type": "PropertySourcePad",
                        "default_allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "value": false,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    }
                ],
                "description": "Stream audio and video into your Gabber flow",
                "metadata": {
                    "primary": "core",
                    "secondary": "media",
                    "tags": [
                        "input",
                        "stream"
                    ]
                }
            },
            {
                "id": "publish_1",
                "type": "Publish",
                "editor_name": "Publish 1",
                "editor_position": [
                    -36.0,
                    780.0
                ],
                "editor_dimensions": [
                    256.0,
                    422.0
                ],
                "pads": [
                    {
                        "id": "audio",
                        "group": "audio",
                        "type": "StatelessSourcePad",
                        "default_allowed_types": [
                            {
                                "type": "audio"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "audio"
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "video",
                        "group": "video",
                        "type": "StatelessSourcePad",
                        "default_allowed_types": [
                            {
                                "type": "video"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "video"
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "audio_enabled",
                        "group": "audio_enabled",
                        "type": "PropertySourcePad",
                        "default_allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "value": false,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "video_enabled",
                        "group": "video_enabled",
                        "type": "PropertySourcePad",
                        "default_allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "value": false,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    }
                ],
                "description": "Stream audio and video into your Gabber flow",
                "metadata": {
                    "primary": "core",
                    "secondary": "media",
                    "tags": [
                        "input",
                        "stream"
                    ]
                }
            },
            {
                "id": "ticker_0",
                "type": "Ticker",
                "editor_name": "Ticker",
                "editor_position": [
                    -36.0,
                    1260.0
                ],
                "editor_dimensions": [
                    256.0,
                    245.0
                ],
                "pads": [
                    {
                        "id": "tick",
                        "group": "tick",
                        "type": "PropertySourcePad",
                        "default_allowed_types": [
                            {
                                "type": "integer",
                                "maximum": null,
                                "minimum": 0
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "integer",
                                "maximum": null,
                                "minimum": 0
                            }
                        ],
                        "value": 0,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "interval_ms",
                        "group": "interval_ms",
                        "type": "PropertySinkPad",
                        "default_allowed_types": [
                            {
                                "type": "integer",
                                "maximum": null,
                                "minimum": 0
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "integer",
                                "maximum": null,
                                "minimum": 0
                            }
                        ],
                        "value": 2000,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "active",
                        "group": "active",
                        "type": "PropertySinkPad",
                        "default_allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "boolean"
                            }
                        ],
                        "value": true,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "reset",
                        "group": "reset",
                        "type": "StatelessSinkPad",
                        "default_allowed_types": [
                            {
                                "type": "trigger"
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "trigger"
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    }
                ],
                "description": "Increments a counter at a specified interval",
                "metadata": {
                    "primary": "core",
                    "secondary": "timing",
                    "tags": [
                        "ticker"
                    ]
                }
            }
        ]
    }