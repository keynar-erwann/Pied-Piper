import { useState, useEffect, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AudioVisualizer } from "./audio-visualizer";
import { useLiveKit } from "@/hooks/use-livekit";
import piedPiperLogo from "@assets/piedpiperlogo.jpg";
import { 
  Mic, 
  MicOff, 
  Keyboard, 
  Settings, 
  Send, 
  X,
  User
} from "lucide-react";

interface Message {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface VoiceInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
}

export function VoiceInterface({ isOpen, onClose }: VoiceInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [textInput, setTextInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  
  const {
    isConnected,
    isListening,
    connectionStatus,
    startRecording,
    stopRecording,
    sendMessage,
    connect,
    disconnect
  } = useLiveKit();

  // Initialize LiveKit connection when modal opens
  useEffect(() => {
    if (isOpen) {
      connect();
      // Add welcome message and speak it
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        sender: 'ai',
        content: "Hi there! I'm Pied Piper, your AI music companion. I can help you discover new songs, discuss your favorite artists, or tell you about music trends. What's on your musical mind today?",
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
      
      // Use Text-to-Speech to speak the welcome message
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(welcomeMessage.content);
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
        utterance.volume = 0.8;
        
        // Set a friendly voice if available
        const voices = speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
          voice.name.includes('Google') || 
          voice.name.includes('Enhanced') ||
          voice.lang.startsWith('en')
        );
        if (preferredVoice) {
          utterance.voice = preferredVoice;
        }
        
        setTimeout(() => {
          speechSynthesis.speak(utterance);
        }, 500); // Small delay to ensure modal is fully opened
      }
    } else {
      disconnect();
      setMessages([]);
      setShowTextInput(false);
      
      // Stop any ongoing speech
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
      }
    }
  }, [isOpen]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleVoiceToggle = async () => {
    if (isRecording) {
      await stopRecording();
      setIsRecording(false);
    } else {
      const success = await startRecording();
      if (success) {
        setIsRecording(true);
      }
    }
  };

  const handleSendTextMessage = async () => {
    if (!textInput.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content: textInput,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Send to LiveKit
    await sendMessage(textInput);
    setTextInput("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendTextMessage();
    }
  };

  const getStatusText = () => {
    if (!isConnected) return "Connecting...";
    if (isRecording) return "Listening...";
    if (isListening) return "Processing...";
    return "Ready to listen";
  };

  const getStatusColor = () => {
    if (!isConnected) return "bg-yellow-500";
    if (isRecording) return "bg-red-500";
    if (isListening) return "bg-blue-500";
    return "bg-green-500";
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-slate-900 border-slate-700 w-full max-w-2xl max-h-[90vh] p-0">
        {/* Modal Header */}
        <DialogHeader className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <img src={piedPiperLogo} alt="Pied Piper" className="w-8 h-8 rounded-lg" />
            <DialogTitle className="text-lg font-bold text-white">
              Pied Piper Voice Chat
            </DialogTitle>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X className="h-5 w-5" />
          </Button>
        </DialogHeader>

        {/* Chat Area */}
        <ScrollArea className="h-96 p-6" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start space-x-3 ${
                  message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                {message.sender === 'ai' ? (
                  <img
                    src={piedPiperLogo}
                    alt="Pied Piper"
                    className="w-8 h-8 rounded-full mt-1"
                  />
                ) : (
                  <div className="w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center mt-1">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
                <div
                  className={`rounded-2xl p-4 max-w-xs ${
                    message.sender === 'ai'
                      ? 'bg-slate-800 rounded-tl-sm'
                      : 'bg-emerald-600 rounded-tr-sm'
                  }`}
                >
                  <p className="text-white text-sm">{message.content}</p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* Voice Controls */}
        <div className="p-6 border-t border-slate-700">
          {/* Audio Visualizer */}
          <div className="flex justify-center items-center mb-4 h-16">
            <AudioVisualizer isActive={isRecording || isListening} />
          </div>

          {/* Input Options */}
          <div className="space-y-4">
            {/* Text Input - Always visible */}
            <div className="flex space-x-2">
              <Input
                type="text"
                placeholder="Type your message or use voice..."
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyPress={handleKeyPress}
                className="flex-1 bg-slate-800 border-slate-600 text-white placeholder-gray-400 focus:ring-emerald-600 focus:border-emerald-600"
                autoFocus
              />
              <Button
                onClick={handleSendTextMessage}
                disabled={!textInput.trim()}
                className="bg-emerald-600 hover:bg-emerald-500 px-4"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>

            {/* Voice and Settings Controls */}
            <div className="flex items-center justify-center space-x-4">
              {/* Voice Button */}
              <Button
                onClick={handleVoiceToggle}
                disabled={!isConnected}
                className={`relative w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 hover:scale-105 focus:outline-none focus:ring-4 focus:ring-opacity-50 ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 focus:ring-red-500'
                    : 'bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-blue-500 focus:ring-emerald-600'
                }`}
              >
                {isRecording ? (
                  <MicOff className="text-white text-xl" />
                ) : (
                  <Mic className="text-white text-xl" />
                )}
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-emerald-600 to-emerald-500 opacity-20 blur-xl animate-pulse"></div>
              </Button>

              {/* Instructions */}
              <div className="text-center">
                <p className="text-xs text-slate-400">
                  {isRecording ? "🎤 Listening..." : "Click mic or type to chat"}
                </p>
              </div>

              {/* Settings */}
              <Button
                variant="outline"
                size="icon"
                className="w-12 h-12 bg-slate-700 hover:bg-slate-600 border-slate-600"
              >
                <Settings className="h-4 w-4 text-gray-300" />
              </Button>
            </div>

            {/* Status Display */}
            <div className="text-center">
              <Badge className="inline-flex items-center space-x-2 bg-slate-800 border-slate-700">
                <div className={`w-2 h-2 rounded-full animate-pulse ${getStatusColor()}`} />
                <span className="text-sm text-gray-300">{getStatusText()}</span>
              </Badge>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
