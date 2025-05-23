import { useState, useEffect, useRef, useCallback } from "react";
import { 
  Room, 
  RoomEvent, 
  LocalAudioTrack,
  RemoteAudioTrack,
  AudioCaptureOptions,
  RoomOptions,
  ConnectOptions
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
      
      // Get LiveKit configuration from environment variables
      const livekitUrl = import.meta.env.VITE_LIVEKIT_URL || "wss://pied-piper-93l7cg2j.livekit.cloud";
      const apiKey = import.meta.env.VITE_LIVEKIT_API_KEY || "API97HnKaUuDx6m";
      const roomName = import.meta.env.VITE_LIVEKIT_ROOM_NAME || "pipey-room";
      
      // Create room instance
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      } as RoomOptions);

      roomRef.current = room;

      // Set up event listeners
      room.on(RoomEvent.Connected, () => {
        console.log("Connected to LiveKit room");
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
        if (track.kind === "audio") {
          const audioElement = track.attach();
          document.body.appendChild(audioElement);
        }
      });

      // Generate access token (in production, this should come from your backend)
      const token = await generateAccessToken(apiKey, roomName);
      
      // Connect to room
      await room.connect(livekitUrl, token, {
        autoSubscribe: true,
      } as ConnectOptions);

      console.log("LiveKit connection established");
      
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
      const audioTrack = await LocalAudioTrack.createAudioTrack({
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
      
      await roomRef.current.localParticipant.publishData(data, "reliable");
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

// Helper function to generate access token (simplified version)
async function generateAccessToken(apiKey: string, roomName: string): Promise<string> {
  // In production, this should be done on your backend server
  // For now, we'll create a simple token structure
  // This is a simplified approach - use proper JWT signing in production
  
  const payload = {
    iss: apiKey,
    sub: `user_${Date.now()}`,
    aud: "livekit",
    exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour
    room: roomName,
    grants: {
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    }
  };

  // Note: This is a mock token. In production, implement proper JWT signing
  // on your backend server using the LiveKit server SDK
  return btoa(JSON.stringify(payload));
}
