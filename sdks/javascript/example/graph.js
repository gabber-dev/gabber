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

var GRAPH = {
    "id": "9f8ff127-8962-4428-ae46-e834b46ce9c3 duplicate",
    "name": "Test",
    "created_at": "2025-09-01T15:52:14.809668",
    "updated_at": "2025-09-01T16:05:42.010420",
    "graph": {
        "nodes": [
            {
                "id": "publish_webcam",
                "type": "Publish",
                "editor_name": "Publish",
                "editor_position": [
                    -360.0,
                    -360.0
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
                        "next_pads": [
                            {
                                "node": "output_webcam",
                                "pad": "video"
                            }
                        ],
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
                "id": "publish_screen",
                "type": "Publish",
                "editor_name": "Publish",
                "editor_position": [
                    -360.0,
                    120.0
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
                        "next_pads": [
                            {
                                "node": "output_screen",
                                "pad": "video"
                            }
                        ],
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
                "id": "button_trigger",
                "type": "ButtonTrigger",
                "editor_name": "ButtonTrigger",
                "editor_position": [
                    -372.0,
                    708.0
                ],
                "editor_dimensions": [
                    256.0,
                    127.0
                ],
                "pads": [
                    {
                        "id": "trigger",
                        "group": "trigger",
                        "type": "StatelessSourcePad",
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
                        "next_pads": [
                            {
                                "node": "string_79eca3e1",
                                "pad": "emit"
                            }
                        ],
                        "previous_pad": null,
                        "pad_links": []
                    }
                ],
                "description": "Manually activate a trigger to run an action",
                "metadata": {
                    "primary": "core",
                    "secondary": "utility",
                    "tags": [
                        "trigger",
                        "debug"
                    ]
                }
            },
            {
                "id": "output_webcam",
                "type": "Output",
                "editor_name": "Output",
                "editor_position": [
                    132.0,
                    -264.0
                ],
                "editor_dimensions": [
                    256.0,
                    300.0
                ],
                "pads": [
                    {
                        "id": "audio",
                        "group": "audio",
                        "type": "StatelessSinkPad",
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
                        "type": "StatelessSinkPad",
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
                        "previous_pad": {
                            "node": "publish_webcam",
                            "pad": "video"
                        },
                        "pad_links": []
                    }
                ],
                "description": "Outputs audio and video to the end user",
                "metadata": {
                    "primary": "core",
                    "secondary": "media",
                    "tags": [
                        "output",
                        "display"
                    ]
                }
            },
            {
                "id": "output_screen",
                "type": "Output",
                "editor_name": "Output",
                "editor_position": [
                    132.0,
                    240.0
                ],
                "editor_dimensions": [
                    256.0,
                    300.0
                ],
                "pads": [
                    {
                        "id": "audio",
                        "group": "audio",
                        "type": "StatelessSinkPad",
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
                        "type": "StatelessSinkPad",
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
                        "previous_pad": {
                            "node": "publish_screen",
                            "pad": "video"
                        },
                        "pad_links": []
                    }
                ],
                "description": "Outputs audio and video to the end user",
                "metadata": {
                    "primary": "core",
                    "secondary": "media",
                    "tags": [
                        "output",
                        "display"
                    ]
                }
            },
            {
                "id": "string_79eca3e1",
                "type": "String",
                "editor_name": "String",
                "editor_position": [
                    24.0,
                    660.0
                ],
                "editor_dimensions": [
                    256.0,
                    223.0
                ],
                "pads": [
                    {
                        "id": "set",
                        "group": "set",
                        "type": "StatelessSinkPad",
                        "default_allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "emit",
                        "group": "emit",
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
                        "previous_pad": {
                            "node": "button_trigger",
                            "pad": "trigger"
                        },
                        "pad_links": []
                    },
                    {
                        "id": "value",
                        "group": "value",
                        "type": "PropertySourcePad",
                        "default_allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "value": "Second",
                        "next_pads": [
                            {
                                "node": "string_property",
                                "pad": "set"
                            }
                        ],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "changed",
                        "group": "changed",
                        "type": "StatelessSourcePad",
                        "default_allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    }
                ],
                "description": "Stores and manages string values",
                "metadata": {
                    "primary": "core",
                    "secondary": "primitive",
                    "tags": [
                        "storage",
                        "string"
                    ]
                }
            },
            {
                "id": "string_property",
                "type": "String",
                "editor_name": "String",
                "editor_position": [
                    456.0,
                    648.0
                ],
                "editor_dimensions": [
                    256.0,
                    223.0
                ],
                "pads": [
                    {
                        "id": "set",
                        "group": "set",
                        "type": "StatelessSinkPad",
                        "default_allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": {
                            "node": "string_79eca3e1",
                            "pad": "value"
                        },
                        "pad_links": []
                    },
                    {
                        "id": "emit",
                        "group": "emit",
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
                    },
                    {
                        "id": "value",
                        "group": "value",
                        "type": "PropertySourcePad",
                        "default_allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "value": "First",
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    },
                    {
                        "id": "changed",
                        "group": "changed",
                        "type": "StatelessSourcePad",
                        "default_allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "allowed_types": [
                            {
                                "type": "string",
                                "max_length": null,
                                "min_length": null
                            }
                        ],
                        "value": null,
                        "next_pads": [],
                        "previous_pad": null,
                        "pad_links": []
                    }
                ],
                "description": "Stores and manages string values",
                "metadata": {
                    "primary": "core",
                    "secondary": "primitive",
                    "tags": [
                        "storage",
                        "string"
                    ]
                }
            }
        ]
    }
}