import React, { useCallback, useRef, useState } from 'react';
import { createOrJoinApp } from "./lib"
import { ConnectionDetails, EngineProvider, LocalAudioTrack, LocalVideoTrack, RemoteAudioTrack, RemoteVideoTrack, useEngine } from "@gabber/client-react"

function App() {
  return (
    <EngineProvider>
      <button onClick={async () => {
        await createOrJoinApp({ runId: "test-run" })
      }}>Connect</button>
    </EngineProvider>
  );
}

function AppInner() {
  const {publishToNode, subscribeToNode, connect, getLocalTrack} = useEngine();
}

function PublishNode({nodeId}: {nodeId: string}) {
  const { publishToNode, getLocalTrack, subscribeToNode } = useEngine();
  const [localVideoTrack, setLocalVideoTrack] = useState<LocalVideoTrack | null>(null);
  const [localAudioTrack, setLocalAudioTrack] = useState<LocalAudioTrack | null>(null);
  const [remoteVideoTrack, setRemoteVideoTrack] = useState<RemoteVideoTrack | null>(null);
  const [remoteAudioTrack, setRemoteAudioTrack] = useState<RemoteAudioTrack | null>(null);
  const [videoPublication, setVideoPublication] = useState<any>(null);
  const [audioPublication, setAudioPublication] = useState<any>(null);
  const [subscription, setSubscription] = useState<any>(null);
  const localVideoEl = useRef<HTMLVideoElement>(null);
  const localAudioEl = useRef<HTMLAudioElement>(null);
  const remoteVideoEl = useRef<HTMLVideoElement>(null);
  const remoteAudioEl = useRef<HTMLAudioElement>(null);

  const publishVideoTrack = useCallback(async () => {
    if (videoPublication) {
      videoPublication.unpublish();
      localVideoTrack?.detachAll();
      setLocalVideoTrack(null);
      setVideoPublication(null);
    } else {
      const lvt = (await getLocalTrack({ type: "webcam" })) as LocalVideoTrack;
      const pub = await publishToNode({ localTrack: lvt, publishNodeId: nodeId });
      setLocalVideoTrack(lvt);
      setVideoPublication(pub);
      lvt.attachToElement(localVideoEl.current!);
      if (localVideoEl.current) {
        localVideoEl.current.muted = true;
        localVideoEl.current.playsInline = true;
        localVideoEl.current.autoplay = true;
      }
    }
  }, [getLocalTrack, publishToNode, nodeId, videoPublication, localVideoTrack]);

  const publishAudioTrack = useCallback(async () => {
    if (audioPublication) {
      audioPublication.unpublish();
      localAudioTrack?.detachAll();
      setLocalAudioTrack(null);
      setAudioPublication(null);
    } else {
      const lat = (await getLocalTrack({ type: "mic" })) as LocalAudioTrack;
      const pub = await publishToNode({ localTrack: lat, publishNodeId: nodeId });
      setLocalAudioTrack(lat);
      setAudioPublication(pub);
      lat.attachToElement(localAudioEl.current!);
      if (localAudioEl.current) {
        localAudioEl.current.muted = true;
        localAudioEl.current.autoplay = true;
      }
    }
  }, [getLocalTrack, publishToNode, nodeId, audioPublication, localAudioTrack]);

  const subscribe = useCallback(async () => {
    if (subscription) {
      subscription.unsubscribe();
      remoteVideoTrack?.detachAll();
      setRemoteVideoTrack(null);
      setSubscription(null);
    } else {
      const sub = await subscribeToNode({ outputOrPublishNodeId: nodeId });
      const rvt = await sub.waitForVideoTrack()
      const rat = await sub.waitForAudioTrack()
      setRemoteVideoTrack(rvt);
      setRemoteAudioTrack(rat);
      setSubscription(sub);
      rvt.attachToElement(remoteVideoEl.current!);
      if (remoteVideoEl.current) {
        remoteVideoEl.current.playsInline = true;
        remoteVideoEl.current.autoplay = true;
      }
    }
  }, [subscribeToNode, nodeId, subscription, remoteVideoTrack]);

  return (
    <div>
      <h3>Publish Node</h3>
      <h4>Local</h4>
      <video ref={localVideoEl} />
      <audio ref={localAudioEl} />
      <button onClick={publishVideoTrack}>{videoPublication ? 'Unpublish Video' : 'Publish Video'}</button>
      <button onClick={publishAudioTrack}>{audioPublication ? 'Unpublish Audio' : 'Publish Audio'}</button>
      <h4>Remote</h4>
      <video ref={remoteVideoEl} />
      <audio ref={remoteAudioEl} />
      <button onClick={subscribeVideoTrack}>{subscription ? 'Unsubscribe Video' : 'Subscribe to Video'}</button>
    </div>
  );
}

export default App;