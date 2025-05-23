import { Room, RoomOptions, RoomEvent } from "livekit-client";

export class LiveKitClient {
  private room: Room | null = null;
  private isConnected = false;

  constructor() {
    this.room = new Room({
      adaptiveStream: true,
      dynacast: true,
    } as RoomOptions);

    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.room) return;

    this.room.on(RoomEvent.Connected, () => {
      console.log("LiveKit room connected");
      this.isConnected = true;
    });

    this.room.on(RoomEvent.Disconnected, (reason) => {
      console.log("LiveKit room disconnected:", reason);
      this.isConnected = false;
    });

    this.room.on(RoomEvent.ParticipantConnected, (participant) => {
      console.log("Participant connected:", participant.identity);
    });

    this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log("Track subscribed:", track.kind, participant.identity);
      
      if (track.kind === "audio") {
        const audioElement = track.attach();
        document.body.appendChild(audioElement);
      }
    });

    this.room.on(RoomEvent.DataReceived, (payload, participant) => {
      const decoder = new TextDecoder();
      const message = decoder.decode(payload);
      console.log("Data received from", participant?.identity, ":", message);
    });
  }

  async connect(serverUrl: string, token: string) {
    if (!this.room) {
      throw new Error("Room not initialized");
    }

    try {
      await this.room.connect(serverUrl, token);
      return true;
    } catch (error) {
      console.error("Failed to connect to LiveKit room:", error);
      return false;
    }
  }

  async disconnect() {
    if (this.room && this.isConnected) {
      await this.room.disconnect();
    }
  }

  getRoom() {
    return this.room;
  }

  getIsConnected() {
    return this.isConnected;
  }
}

export const livekitClient = new LiveKitClient();
