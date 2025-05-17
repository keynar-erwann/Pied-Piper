"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Volume2, VolumeX, AudioWaveformIcon, ArrowLeft, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

// Mock responses for demo purposes
const mockResponses = [
  "I love that song! It was released in 2019 and reached the top of the charts in several countries. The artist spent over six months perfecting the melody before recording.",
  "That artist has a fascinating background in classical music before transitioning to pop. Their early influences include Bach and Mozart, which you can hear in their complex chord progressions. Would you like to hear some similar artists?",
  "This genre emerged in the late 70s and has influenced countless musicians since. The rhythmic patterns are particularly distinctive, often featuring syncopated beats and layered harmonies that create a rich sonic landscape.",
  "I found some information about that song! It was written during a particularly challenging time in the artist's life, which explains the emotional depth in the lyrics. The producer used innovative recording techniques to capture that unique sound.",
  "That's an interesting question about music theory! The chord progression you're asking about is commonly found in jazz standards. It creates that sense of tension and resolution that makes the music so compelling.",
  "Have you listened to their latest album? It represents a significant evolution in their sound, incorporating elements of electronic music while maintaining their signature vocal style. Critics have been particularly impressed with tracks 3 and 7.",
]

export default function ChatPage() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    {
      role: "assistant",
      content:
        "Hi there! I'm Pipey, your AI music companion. I can help you discover new songs, discuss your favorite artists, or tell you about music trends. What's on your musical mind today?",
    },
  ])
  const [input, setInput] = useState("")
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [language, setLanguage] = useState("en")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showWelcome, setShowWelcome] = useState(true)

  const languages = {
    en: "English",
    es: "Spanish",
    fr: "French",
    de: "German",
    it: "Italian",
    hi: "Hindi",
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    // Hide welcome message after 5 seconds
    const timer = setTimeout(() => {
      setShowWelcome(false)
    }, 5000)

    // Simulate initial voice response
    simulateSpeaking(5000)

    return () => {
      clearTimeout(timer)
    }
  }, [])

  const handleSend = async () => {
    if (input.trim() === "") return

    const userMessage = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // Simulate API call with a delay
    setTimeout(() => {
      const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)]
      const assistantMessage = { role: "assistant", content: randomResponse }

      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)

      // Simulate speaking
      simulateSpeaking(randomResponse.length * 50)
    }, 1500)
  }

  const simulateSpeaking = (duration: number) => {
    setIsSpeaking(true)
    setTimeout(() => {
      setIsSpeaking(false)
    }, duration)
  }

  const toggleSpeaking = () => {
    if (isSpeaking) {
      setIsSpeaking(false)
    } else if (messages.length > 0) {
      // Simulate speaking the last assistant message
      const lastAssistantMessage = [...messages].reverse().find((m) => m.role === "assistant")
      if (lastAssistantMessage) {
        simulateSpeaking(lastAssistantMessage.content.length * 50)
      }
    }
  }

  const changeLanguage = (lang: string) => {
    setLanguage(lang)
    // Add a message about language change
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: `I've switched to ${languages[lang as keyof typeof languages]}. How can I help you with music today?`,
      },
    ])
    // Simulate speaking
    simulateSpeaking(3000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white flex flex-col">
      <header className="sticky top-0 z-10 bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center">
              <ArrowLeft className="h-5 w-5 mr-2 text-gray-600" />
              <div className="h-10 w-10">
                <img src="/piedpiperlogo.jpg" alt="Pied Piper Logo" className="h-full w-full object-contain rounded" />
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-bold text-gray-800">Pipey</h1>
                <p className="text-xs text-gray-500">Your AI Music Companion</p>
              </div>
            </Link>
          </div>
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon" className="rounded-full">
                  <Globe className="h-5 w-5 text-green-600" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => changeLanguage("en")}>English</DropdownMenuItem>
                <DropdownMenuItem onClick={() => changeLanguage("es")}>Spanish</DropdownMenuItem>
                <DropdownMenuItem onClick={() => changeLanguage("fr")}>French</DropdownMenuItem>
                <DropdownMenuItem onClick={() => changeLanguage("de")}>German</DropdownMenuItem>
                <DropdownMenuItem onClick={() => changeLanguage("it")}>Italian</DropdownMenuItem>
                <DropdownMenuItem onClick={() => changeLanguage("hi")}>Hindi</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button variant="outline" size="icon" onClick={toggleSpeaking} className={isSpeaking ? "bg-green-100" : ""}>
              {isSpeaking ? (
                <VolumeX className="h-5 w-5 text-green-600" />
              ) : (
                <Volume2 className="h-5 w-5 text-green-600" />
              )}
            </Button>
          </div>
        </div>
      </header>

      <AnimatePresence>
        {showWelcome && (
          <motion.div
            className="fixed top-20 left-1/2 transform -translate-x-1/2 z-20 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <p className="text-sm">Pipey responds with voice! Make sure your sound is on.</p>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 container mx-auto px-4 py-6 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto pb-4 space-y-4">
          {messages.map((message, index) => (
            <motion.div
              key={index}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex items-start gap-3 max-w-[80%]">
                {message.role === "assistant" && (
                  <div className="h-10 w-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <AudioWaveformIcon className="h-5 w-5 text-white" />
                  </div>
                )}
                <Card
                  className={`p-4 ${
                    message.role === "user" ? "bg-white border border-gray-200" : "bg-green-600 text-white"
                  } rounded-xl shadow-sm`}
                >
                  <p>{message.content}</p>
                  {message.role === "assistant" && (
                    <div className="mt-2 flex items-center text-xs text-green-100">
                      <Volume2 className="h-3 w-3 mr-1" />
                      <span>Voice response available</span>
                    </div>
                  )}
                </Card>
                {message.role === "user" && (
                  <div className="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-medium text-gray-600">You</span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start gap-3 max-w-[80%]">
                <div className="h-10 w-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <AudioWaveformIcon className="h-5 w-5 text-white" />
                </div>
                <Card className="p-4 bg-green-600 text-white rounded-xl shadow-sm">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-white rounded-full animate-pulse"></div>
                    <div className="h-2 w-2 bg-white rounded-full animate-pulse delay-150"></div>
                    <div className="h-2 w-2 bg-white rounded-full animate-pulse delay-300"></div>
                  </div>
                </Card>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="sticky bottom-0 pt-2 pb-4 bg-gradient-to-t from-white to-transparent">
          <div className="flex gap-2 items-center">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Pipey about music..."
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              className="flex-1 border-gray-300 focus:border-green-500 focus:ring-green-500 rounded-full py-6 px-6 shadow-sm"
            />
            <Button
              onClick={handleSend}
              className="bg-green-600 hover:bg-green-700 rounded-full h-12 w-12 flex items-center justify-center shadow-md"
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>

      {isSpeaking && (
        <motion.div
          className="fixed bottom-24 right-4 bg-green-600 text-white p-4 rounded-full shadow-lg"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.8, opacity: 0 }}
        >
          <div className="flex items-center justify-center h-6 w-16">
            <div className="w-1 h-5 bg-white rounded-full mx-0.5 animate-sound-wave"></div>
            <div className="w-1 h-3 bg-white rounded-full mx-0.5 animate-sound-wave animation-delay-200"></div>
            <div className="w-1 h-6 bg-white rounded-full mx-0.5 animate-sound-wave animation-delay-400"></div>
            <div className="w-1 h-4 bg-white rounded-full mx-0.5 animate-sound-wave animation-delay-300"></div>
            <div className="w-1 h-2 bg-white rounded-full mx-0.5 animate-sound-wave animation-delay-100"></div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
