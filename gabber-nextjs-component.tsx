/**
 * Gabber NextJS Component
 *
 * A self-contained React component that can be dropped into any NextJS project
 * to integrate with the Gabber streaming platform.
 *
 * Features:
 * - Uses React SDK for real-time audio/video streaming
 * - Configurable with either a graph definition or app ID
 * - Echo functionality for testing
 * - Clean, modern UI with Tailwind CSS
 */

'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  EngineProvider,
  useEngine,
  usePropertyPad,
  LocalAudioTrack,
  LocalVideoTrack,
  RemoteAudioTrack,
  RemoteVideoTrack,
  type ConnectionDetails,
  type Subscription,
} from '@gabber/client-react';

// Echo graph for testing - echoes audio and video back
const ECHO_GRAPH = {
  "nodes": [
    {
      "id": "publish_0",
      "type": "Publish",
      "editor_name": "Publish",
      "editor_position": [288.0, 576.0],
      "editor_dimensions": [256.0, 424.0],
      "pads": [
        {
          "id": "audio",
          "group": "audio",
          "type": "StatelessSourcePad",
          "default_allowed_types": [{"type": "audio"}],
          "allowed_types": [{"type": "audio"}],
          "value": null,
          "next_pads": [{"node": "output_0", "pad": "audio"}],
          "previous_pad": null,
          "pad_links": []
        },
        {
          "id": "video",
          "group": "video",
          "type": "StatelessSourcePad",
          "default_allowed_types": [{"type": "video"}],
          "allowed_types": [{"type": "video"}],
          "value": null,
          "next_pads": [{"node": "output_0", "pad": "video"}],
          "previous_pad": null,
          "pad_links": []
        },
        {
          "id": "audio_enabled",
          "group": "audio_enabled",
          "type": "PropertySourcePad",
          "default_allowed_types": [{"type": "boolean"}],
          "allowed_types": [{"type": "boolean"}],
          "value": false,
          "next_pads": [],
          "previous_pad": null,
          "pad_links": []
        },
        {
          "id": "video_enabled",
          "group": "video_enabled",
          "type": "PropertySourcePad",
          "default_allowed_types": [{"type": "boolean"}],
          "allowed_types": [{"type": "boolean"}],
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
        "tags": ["input", "stream"]
      }
    },
    {
      "id": "output_0",
      "type": "Output",
      "editor_name": "Output",
      "editor_position": [696.0, 660.0],
      "editor_dimensions": [256.0, 300.0],
      "pads": [
        {
          "id": "audio",
          "group": "audio",
          "type": "StatelessSinkPad",
          "default_allowed_types": [{"type": "audio"}],
          "allowed_types": [{"type": "audio"}],
          "value": null,
          "next_pads": [],
          "previous_pad": {"node": "publish_0", "pad": "audio"},
          "pad_links": []
        },
        {
          "id": "video",
          "group": "video",
          "type": "StatelessSinkPad",
          "default_allowed_types": [{"type": "video"}],
          "allowed_types": [{"type": "video"}],
          "value": null,
          "next_pads": [],
          "previous_pad": {"node": "publish_0", "pad": "video"},
          "pad_links": []
        }
      ],
      "description": "Outputs audio and video to the end user",
      "metadata": {
        "primary": "core",
        "secondary": "media",
        "tags": ["output", "display"]
      }
    }
  ]
};

interface GabberComponentProps {
  /** Your Gabber API URL (default: http://localhost:8001) */
  apiUrl?: string;
  /** Run ID for this session */
  runId?: string;
  /** App ID to use instead of graph (if provided, graph will be ignored) */
  appId?: string;
  /** Custom graph definition (ignored if appId is provided) */
  graph?: any;
  /** Whether to show debug information */
  showDebug?: boolean;
  /** Custom CSS class for the component */
  className?: string;
}

const BTN_CLASS = 'bg-blue-500 text-white px-4 py-2 rounded cursor-pointer m-2 disabled:opacity-50 disabled:cursor-not-allowed';

export default function GabberComponent({
  apiUrl = 'http://localhost:8001',
  runId = 'demo-run',
  appId,
  graph,
  showDebug = false,
  className = ''
}: GabberComponentProps) {
  return (
    <div className={`gabber-component ${className}`}>
      <EngineProvider>
        <GabberContent
          apiUrl={apiUrl}
          runId={runId}
          appId={appId}
          graph={graph}
          showDebug={showDebug}
        />
      </EngineProvider>
    </div>
  );
}

function GabberContent({ apiUrl, runId, appId, graph, showDebug }: GabberComponentProps) {
  const { connect, disconnect, connectionState, publishToNode, getLocalTrack, subscribeToNode } = useEngine();
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refs for media elements
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Track states
  const [localVideoTrack, setLocalVideoTrack] = useState<LocalVideoTrack | null>(null);
  const [remoteVideoTrack, setRemoteVideoTrack] = useState<RemoteVideoTrack | null>(null);
  const [remoteAudioTrack, setRemoteAudioTrack] = useState<RemoteAudioTrack | null>(null);
  const [videoPublication, setVideoPublication] = useState<any>(null);
  const [audioPublication, setAudioPublication] = useState<any>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const subscribed = useRef(false);

  // Use echo graph if no custom graph or app ID provided
  const activeGraph = graph || ECHO_GRAPH;

  // Extract node IDs from the graph
  const publishNodeId = activeGraph.nodes.find((node: any) => node.type === 'Publish')?.id;
  const outputNodeId = activeGraph.nodes.find((node: any) => node.type === 'Output')?.id;

  // Error checking for missing node IDs
  if (!publishNodeId || !outputNodeId) {
    console.error('❌ Graph missing required nodes:', { publishNodeId, outputNodeId });
  }

  // Debug connection state changes
  useEffect(() => {
    console.log('🔄 Engine connection state changed to:', engineConnectionState);
  }, [engineConnectionState]);

  // Clean up media tracks when connection state changes
  useEffect(() => {
    if (engineConnectionState === 'disconnected') {
      console.log('🔌 Cleaning up media tracks due to disconnection...');

      // Clean up local video
      if (videoPublication) {
        videoPublication.unpublish();
        localVideoTrack?.detachAll();
        setLocalVideoTrack(null);
        setVideoPublication(null);
      }

      // Clean up local audio
      if (audioPublication) {
        audioPublication.unpublish();
        setAudioPublication(null);
      }

      // Clean up remote media
      if (subscription) {
        subscription.cleanup();
        remoteVideoTrack?.detachFromElement(remoteVideoRef.current!);
        remoteAudioTrack?.detachFromElement(audioRef.current!);
        setRemoteVideoTrack(null);
        setRemoteAudioTrack(null);
        setSubscription(null);
      }

      setIsConnected(false);
      console.log('✅ Media cleanup completed');
    }
  }, [engineConnectionState, videoPublication, localVideoTrack, audioPublication, subscription, remoteVideoTrack, remoteAudioTrack]);

  const handleConnect = useCallback(async () => {
    if (isConnected) {
      disconnect();
      setIsConnected(false);
      return;
    }

    try {
      setError(null);

      let connectionDetails: ConnectionDetails;

      if (appId) {
        // Use app ID - but we still need a graph for this to work
        // For now, fall back to using the default graph with app ID
        console.warn('App ID provided but no graph support yet - using default graph');
      }
        // Use graph
        const response = await fetch(`${apiUrl}/app/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ run_id: runId, graph: activeGraph }),
        });

        if (!response.ok) {
          throw new Error(`Failed to create app: ${response.statusText}`);
        }

        const data = await response.json();
        connectionDetails = data.connection_details;
      }

      await connect(connectionDetails);
      setIsConnected(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      console.error('Gabber connection error:', err);
    }
  }, [isConnected, disconnect, connect, apiUrl, runId, appId, activeGraph]);

  const publishVideo = useCallback(async () => {
    if (videoPublication) {
      // Unpublish
      videoPublication.unpublish();
      localVideoTrack?.detachAll();
      setLocalVideoTrack(null);
      setVideoPublication(null);
    } else {
      // Publish
      try {
        const track = await getLocalTrack({ type: 'webcam' }) as LocalVideoTrack;
        const pub = await publishToNode({ localTrack: track, publishNodeId: publishNodeId! });
        setLocalVideoTrack(track);
        setVideoPublication(pub);

        track.attachToElement(localVideoRef.current!);
        if (localVideoRef.current) {
          localVideoRef.current.muted = true;
          localVideoRef.current.playsInline = true;
          localVideoRef.current.autoplay = true;
        }
      } catch (err) {
        console.error('❌ Video publish error:', err);
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';

        if (err instanceof Error && (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError')) {
          setError('Camera permission was denied. Please allow camera access to publish video.');
        } else {
          setError('Failed to publish video: ' + errorMessage);
        }
      }
    }
  }, [videoPublication, localVideoTrack, getLocalTrack, publishToNode, publishNodeId]);

  const publishAudio = useCallback(async () => {
    if (audioPublication) {
      // Unpublish
      audioPublication.unpublish();
      setAudioPublication(null);
    } else {
      // Publish
      try {
        const track = await getLocalTrack({ type: 'microphone' }) as LocalAudioTrack;
        const pub = await publishToNode({ localTrack: track, publishNodeId: publishNodeId! });
        setAudioPublication(pub);
      } catch (err) {
        console.error('❌ Audio publish error:', err);
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';

        if (err instanceof Error && (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError')) {
          setError('Microphone permission was denied. Please allow microphone access to publish audio.');
        } else {
          setError('Failed to publish audio: ' + errorMessage);
        }
      }
    }
  }, [audioPublication, getLocalTrack, publishToNode, publishNodeId]);

  const handleSubscribe = useCallback(async () => {
    if (subscription) {
      // Unsubscribe
      subscription.cleanup();
      remoteVideoTrack?.detachFromElement(remoteVideoRef.current!);
      remoteAudioTrack?.detachFromElement(audioRef.current!);
      setRemoteVideoTrack(null);
      setRemoteAudioTrack(null);
      setSubscription(null);
    } else {
      // Subscribe
      if (subscribed.current) {
        console.warn('📡 Already subscribed to node:', outputNodeId);
        return;
      }
      subscribed.current = true;

      try {
        const sub = await subscribeToNode({ outputOrPublishNodeId: outputNodeId! });

        sub.waitForVideoTrack().then((track) => {
          setRemoteVideoTrack(track);
          track.attachToElement(remoteVideoRef.current!);
        });

        sub.waitForAudioTrack().then((track) => {
          setRemoteAudioTrack(track);
          track.attachToElement(audioRef.current!);
          if (audioRef.current) {
            audioRef.current.play();
          }
        });

        setSubscription(sub);
        console.log('✅ Subscription setup complete');
      } catch (err) {
        console.error('❌ Subscribe error:', err);
        setError('Failed to subscribe');
        console.error('Subscribe error:', err);
        subscribed.current = false;
      }
    }
  }, [subscription, remoteVideoTrack, remoteAudioTrack, subscribeToNode, outputNodeId]);

  return (
    <div className="gabber-container p-4 border rounded-lg bg-white shadow-sm">
      <h2 className="text-xl font-bold mb-4">Gabber Stream</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Connection Controls */}
      <div className="mb-4">
        <button
          className={`${BTN_CLASS} ${isConnected ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}`}
          onClick={handleConnect}
          disabled={connectionState === 'connecting'}
        >
          {connectionState === 'connecting' ? 'Connecting...' :
           isConnected ? 'Disconnect' : 'Connect'}
        </button>
      </div>

      {/* Status */}
      <div className="mb-4 text-sm text-gray-600">
        Status: <span className="font-medium">{connectionState}</span>
        {showDebug && (
          <div className="mt-2">
            <strong>Debug Info:</strong>
            <div>Run ID: {runId}</div>
            <div>API URL: {apiUrl}</div>
            <div>App ID: {appId || 'Using custom graph'}</div>
          </div>
        )}
      </div>

      {/* Media Streams */}
      {isConnected && (
        <div className="space-y-4">
          {/* Local Video */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Your Video</h3>
            <video
              ref={localVideoRef}
              className="w-full max-w-md bg-black rounded"
              style={{ aspectRatio: '16/9' }}
            />
          </div>

          {/* Remote Video */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Stream Output</h3>
            <video
              ref={remoteVideoRef}
              className="w-full max-w-md bg-black rounded"
              style={{ aspectRatio: '16/9' }}
              autoPlay
              playsInline
            />
            <audio ref={audioRef} autoPlay />
          </div>

          {/* Controls */}
          <div className="flex flex-wrap gap-2">
            <button className={BTN_CLASS} onClick={publishVideo}>
              {videoPublication ? 'Stop Video' : 'Start Video'}
            </button>
            <button className={BTN_CLASS} onClick={publishAudio}>
              {audioPublication ? 'Stop Audio' : 'Start Audio'}
            </button>
            <button className={BTN_CLASS} onClick={handleSubscribe}>
              {subscription ? 'Stop Echo' : 'Start Echo'}
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      {!isConnected && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
          <h3 className="font-semibold text-blue-800 mb-2">How to use:</h3>
          <ol className="text-sm text-blue-700 list-decimal list-inside space-y-1">
            <li>Click "Connect" to start the session</li>
            <li>Click "Start Video" to publish your webcam</li>
            <li>Click "Start Audio" to publish your microphone</li>
            <li>Click "Start Echo" to receive the stream back</li>
          </ol>
        </div>
      )}
    </div>
  );
}
