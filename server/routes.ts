import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  // Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // LiveKit configuration endpoint
  app.get("/api/livekit/config", (req, res) => {
    res.json({
      url: process.env.LIVEKIT_URL || "wss://pied-piper-93l7cg2j.livekit.cloud",
      apiKey: process.env.LIVEKIT_API_KEY || "API97HnKaUuDx6m",
      roomName: process.env.LIVEKIT_ROOM_NAME || "pipey-room"
    });
  });

  // Create HTTP server
  const httpServer = createServer(app);

  // Add WebSocket server for real-time communication
  const wss = new WebSocketServer({ 
    server: httpServer, 
    path: '/ws'
  });

  wss.on('connection', (ws: WebSocket, req) => {
    console.log('WebSocket client connected from:', req.socket.remoteAddress);

    // Send welcome message
    ws.send(JSON.stringify({
      type: 'welcome',
      message: 'Connected to Pied Piper WebSocket server',
      timestamp: new Date().toISOString()
    }));

    // Handle incoming messages
    ws.on('message', (data: Buffer) => {
      try {
        const message = JSON.parse(data.toString());
        console.log('Received WebSocket message:', message);

        // Echo the message back for now
        // In production, this would interface with the LiveKit agent
        ws.send(JSON.stringify({
          type: 'response',
          originalMessage: message,
          response: 'Message received by Pied Piper server',
          timestamp: new Date().toISOString()
        }));

        // Broadcast to other clients if needed
        wss.clients.forEach((client) => {
          if (client !== ws && client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({
              type: 'broadcast',
              message: message,
              timestamp: new Date().toISOString()
            }));
          }
        });

      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Invalid message format',
          timestamp: new Date().toISOString()
        }));
      }
    });

    // Handle connection close
    ws.on('close', (code, reason) => {
      console.log(`WebSocket client disconnected: ${code} ${reason}`);
    });

    // Handle errors
    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

  console.log('WebSocket server initialized on path /ws');

  return httpServer;
}
