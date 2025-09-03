import React, { useCallback, useMemo, useRef, useState } from 'react';
import { createOrJoinApp } from './lib';
import {
  EngineProvider,
  LocalAudioTrack,
  LocalVideoTrack,
  RemoteAudioTrack,
  RemoteVideoTrack,
  useEngine,
  usePropertyPad,
} from '@gabber/client-react';
import { Subscription } from '@gabber/client';

const BTN_CLASS = 'bg-blue-500 text-white px-4 py-2 rounded cursor-pointer m-2';

function App() {
  return (
    <EngineProvider>
      <ConnectButton />
      <div className='flex gap-2'>
        <PublishNode nodeId="publish_0" />
        <PublishNode nodeId="publish_1" />
      </div>
      <div className='flex flex-col'>
        <DebugLink runId='test-run' />
        <TickerNode />
      </div>
    </EngineProvider>
  );
}

function ConnectButton() {
  const { connect, disconnect, connectionState } = useEngine();

  return (
    <button
      className={BTN_CLASS}
      onClick={async () => {
        if (connectionState === 'connected') {
          disconnect();
        } else {
          const dets = await createOrJoinApp({ runId: 'test-run' });
          connect(dets);
        }
      }}
    >
      {connectionState === 'connected' ? 'Disconnect' : 'Connect'}
    </button>
  );
}

function DebugLink({runId}: {runId: string}) {
  const { connectionState } = useEngine();

  return (
    <div className='flex gap-2'>
      <span className='text-gray-500'>Debug Link:</span>
      <a
        className='text-blue-500 underline'
        href={`http://localhost:3000/debug/${runId}`}
      >
        {`https://gabber.dev/debug/${runId}`}
      </a>
      <span className='text-gray-500'>{`Connection State: ${connectionState}`}</span>
    </div>
  );
}

function TickerNode() {
  const { currentValue } = usePropertyPad("ticker_0", "tick")

  const renderValue = useMemo(() => {
    if (currentValue === "loading") {
      return currentValue;
    }
    if(currentValue.type !== "integer") {
      return "N/A";
    }
    return currentValue.value;
  }, [currentValue])

  return (
    <div className='flex gap-2'>
      <span className='text-gray-500'>Tick: {renderValue}</span>
    </div>
  );
}

function PublishNode({ nodeId }: { nodeId: string }) {
  const { publishToNode, getLocalTrack, subscribeToNode, connectionState } = useEngine();
  const [localVideoTrack, setLocalVideoTrack] = useState<LocalVideoTrack | null>(null);
  const [remoteVideoTrack, setRemoteVideoTrack] = useState<RemoteVideoTrack | null>(null);
  const [remoteAudioTrack, setRemoteAudioTrack] = useState<RemoteAudioTrack | null>(null);
  const [videoPublication, setVideoPublication] = useState<any>(null);
  const [audioPublication, setAudioPublication] = useState<any>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const videoEl = useRef<HTMLVideoElement>(null);
  const audioEl = useRef<HTMLAudioElement>(null);

  const publishVideoTrack = useCallback(async () => {
    if (videoPublication) {
      videoPublication.unpublish();
      localVideoTrack?.detachAll();
      setLocalVideoTrack(null);
      setVideoPublication(null);
    } else {
      const lvt = (await getLocalTrack({ type: 'webcam' })) as LocalVideoTrack;
      const pub = await publishToNode({ localTrack: lvt, publishNodeId: nodeId });
      setLocalVideoTrack(lvt);
      setVideoPublication(pub);
      lvt.attachToElement(videoEl.current!);
      if (videoEl.current) {
        videoEl.current.muted = true;
        videoEl.current.playsInline = true;
        videoEl.current.autoplay = true;
      }
    }
  }, [getLocalTrack, publishToNode, nodeId, videoPublication, localVideoTrack]);

  const publishAudioTrack = useCallback(async () => {
    if (audioPublication) {
      audioPublication.unpublish();
      setAudioPublication(null);
    } else {
      const lat = (await getLocalTrack({ type: 'microphone' })) as LocalAudioTrack;
      const pub = await publishToNode({ localTrack: lat, publishNodeId: nodeId });
      setAudioPublication(pub);
    }
  }, [getLocalTrack, publishToNode, nodeId, audioPublication]);

  const subscribe = useCallback(async () => {
    if (subscription) {
      subscription.cleanup();
      remoteVideoTrack?.detachFromElement(videoEl.current!);
      remoteAudioTrack?.detachFromElement(audioEl.current!);
      setRemoteVideoTrack(null);
      setRemoteAudioTrack(null);
      setSubscription(null);
    } else {
      const sub = await subscribeToNode({ outputOrPublishNodeId: nodeId });
      sub.waitForVideoTrack().then((rvt) => {
        setRemoteVideoTrack(rvt);
        rvt.attachToElement(videoEl.current!);
      });
      sub.waitForAudioTrack().then((rat) => {
        setRemoteAudioTrack(rat);
        rat.attachToElement(audioEl.current!);
      });
      setSubscription(sub);
    }
  }, [subscribeToNode, nodeId, subscription, remoteVideoTrack, remoteAudioTrack]);

  return (
    <div className=''>
      <video className='bg-black w-full aspect-video' ref={videoEl} />
      <audio ref={audioEl} />
      {connectionState === 'connected' && (
        <div className='flex gap-2'>
          <button className={BTN_CLASS} onClick={publishVideoTrack}>
            {videoPublication ? 'Unpublish Video' : 'Publish Video'}
          </button>
          <button className={BTN_CLASS} onClick={publishAudioTrack}>
            {audioPublication ? 'Unpublish Audio' : 'Publish Audio'}
          </button>
          <button className={BTN_CLASS} onClick={subscribe}>{subscription ? 'Unsubscribe' : 'Subscribe'}</button>
        </div>
      )}
    </div>
  );
}

export default App;