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

var GRAPH = {"id":"9d9d03a0-ceb1-4a86-8adb-db8c6dac721e","name":"Test","created_at":"2025-07-29T10:41:27.850348","updated_at":"2025-07-31T13:33:55.057908","graph":{"nodes":[{"id":"webcam_publish","type":"Publish","editor_name":"Publish","editor_position":[164.41386010362697,456.5556994818653],"editor_dimensions":[256.0,352.0],"pads":[{"id":"audio","group":"audio","type":"StatelessSourcePad","value":null,"next_pads":[{"node":"output_webcam","pad":"audio_sink"}],"previous_pad":null,"allowed_types":[{"type":"audio"}]},{"id":"video","group":"video","type":"StatelessSourcePad","value":null,"next_pads":[{"node":"output_webcam","pad":"video_sink"}],"previous_pad":null,"allowed_types":[{"type":"video"}]}],"description":"Stream audio and video into your Gabber flow","metadata":{"primary":"core","secondary":"media","tags":["input","stream"]}},{"id":"output_webcam","type":"Output","editor_name":"Output","editor_position":[479.9251808402332,504.51789285312304],"editor_dimensions":[256.0,304.0],"pads":[{"id":"audio_sink","group":"audio_sink","type":"StatelessSinkPad","value":null,"next_pads":[],"previous_pad":{"node":"webcam_publish","pad":"audio"},"allowed_types":[{"type":"audio"}]},{"id":"video_sink","group":"video_sink","type":"StatelessSinkPad","value":null,"next_pads":[],"previous_pad":{"node":"webcam_publish","pad":"video"},"allowed_types":[{"type":"video"}]}],"description":"Outputs audio and video to the end user","metadata":{"primary":"core","secondary":"debug","tags":["output","display"]}},{"id":"screen_publish","type":"Publish","editor_name":"Publish","editor_position":[165.87767701763948,838.3615248978276],"editor_dimensions":[256.0,352.0],"pads":[{"id":"audio","group":"audio","type":"StatelessSourcePad","value":null,"next_pads":[],"previous_pad":null,"allowed_types":[{"type":"audio"}]},{"id":"video","group":"video","type":"StatelessSourcePad","value":null,"next_pads":[{"node":"output_screen","pad":"video_sink"}],"previous_pad":null,"allowed_types":[{"type":"video"}]}],"description":"Stream audio and video into your Gabber flow","metadata":{"primary":"core","secondary":"media","tags":["input","stream"]}},{"id":"output_screen","type":"Output","editor_name":"Output","editor_position":[559.4648296115879,895.3300664456306],"editor_dimensions":[256.0,304.0],"pads":[{"id":"audio_sink","group":"audio_sink","type":"StatelessSinkPad","value":null,"next_pads":[],"previous_pad":null,"allowed_types":[{"type":"audio"}]},{"id":"video_sink","group":"video_sink","type":"StatelessSinkPad","value":null,"next_pads":[],"previous_pad":{"node":"screen_publish","pad":"video"},"allowed_types":[{"type":"video"}]}],"description":"Outputs audio and video to the end user","metadata":{"primary":"core","secondary":"debug","tags":["output","display"]}}]}}