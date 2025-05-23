import { useState, useEffect, useRef, useCallback } from "react";
import { 
  Room, 
  RoomEvent, 
  LocalAudioTrack,
  RemoteAudioTrack,
  AudioCaptureOptions,
  RoomOptions,
  RoomConnectOptions
} from "livekit-client";

export function useLiveKit() {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<string>("disconnected");
  const roomRef = useRef<Room | null>(null);
  const localAudioTrackRef = useRef<LocalAudioTrack | null>(null);

  const connect = useCallback(async () => {
    try {
      setConnectionStatus("connecting");
      
      // Get LiveKit configuration from backend
      const configResponse = await fetch('/api/livekit/config');
      const config = await configResponse.json();
      
      // Get access token from backend
      const tokenResponse = await fetch('/api/livekit/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!tokenResponse.ok) {
        throw new Error('Failed to get access token from server');
      }
      
      const { token, identity, roomName } = await tokenResponse.json();
      
      // Create room instance
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      } as RoomOptions);

      roomRef.current = room;

      // Set up event listeners
      room.on(RoomEvent.Connected, () => {
        console.log("Connected to LiveKit room:", roomName);
        setIsConnected(true);
        setConnectionStatus("connected");
      });

      room.on(RoomEvent.Disconnected, () => {
        console.log("Disconnected from LiveKit room");
        setIsConnected(false);
        setConnectionStatus("disconnected");
      });

      room.on(RoomEvent.AudioPlaybackStatusChanged, () => {
        setIsListening(room.canPlaybackAudio);
      });

      room.on(RoomEvent.TrackPublished, (publication, participant) => {
        console.log("Track published:", publication.trackSid, participant.identity);
      });

      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        console.log("Track subscribed:", track.kind, participant.identity);
        if (track.kind === "audio") {
          const audioElement = track.attach();
          document.body.appendChild(audioElement);
        }
      });

      room.on(RoomEvent.DataReceived, (payload, participant) => {
        console.log("Data received from agent:", new TextDecoder().decode(payload));
      });
      
      // Connect to room with proper token
      await room.connect(config.url, token, {
        autoSubscribe: true,
      } as RoomConnectOptions);

      console.log("LiveKit connection established with identity:", identity);
      
    } catch (error) {
      console.error("Failed to connect to LiveKit:", error);
      setConnectionStatus("error");
      setIsConnected(false);
    }
  }, []);

  const disconnect = useCallback(async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    if (localAudioTrackRef.current) {
      localAudioTrackRef.current.stop();
      localAudioTrackRef.current = null;
    }
    setIsConnected(false);
    setIsListening(false);
    setConnectionStatus("disconnected");
  }, []);

  const startRecording = useCallback(async (): Promise<boolean> => {
    try {
      if (!roomRef.current || !isConnected) {
        console.warn("Room not connected");
        return false;
      }

      // Create local audio track
      const audioTrack = await LocalAudioTrack.create({
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      } as AudioCaptureOptions);

      localAudioTrackRef.current = audioTrack;

      // Publish audio track to room
      await roomRef.current.localParticipant.publishTrack(audioTrack);
      
      setIsListening(true);
      console.log("Started audio recording and publishing");
      return true;
      
    } catch (error) {
      console.error("Failed to start recording:", error);
      return false;
    }
  }, [isConnected]);

  const stopRecording = useCallback(async () => {
    try {
      if (localAudioTrackRef.current) {
        // Unpublish and stop the track
        if (roomRef.current) {
          await roomRef.current.localParticipant.unpublishTrack(localAudioTrackRef.current);
        }
        localAudioTrackRef.current.stop();
        localAudioTrackRef.current = null;
      }
      
      setIsListening(false);
      console.log("Stopped audio recording");
      
    } catch (error) {
      console.error("Failed to stop recording:", error);
    }
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    try {
      if (!roomRef.current || !isConnected) {
        console.warn("Room not connected");
        return;
      }

      // Send data message to room participants
      const encoder = new TextEncoder();
      const data = encoder.encode(message);
      
      await roomRef.current.localParticipant.publishData(data, { reliable: true });
      console.log("Sent message:", message);
      
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  }, [isConnected]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isListening,
    connectionStatus,
    connect,
    disconnect,
    startRecording,
    stopRecording,
    sendMessage,
  };
}


