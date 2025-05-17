import type React from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Music, Globe, Headphones, TrendingUp } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/sound-wave-pattern.png')] opacity-5 bg-repeat"></div>
        <div className="container mx-auto px-4 py-20 md:py-32 relative z-10">
          <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
            <div className="mb-8 flex items-center justify-center">
              <div className="h-20 w-20 md:h-28 md:w-28 relative">
                <img
                  src="/piedpiperlogo.jpg"
                  alt="Pied Piper Logo"
                  className="h-full w-full object-contain rounded-xl shadow-lg"
                />
              </div>
              <h1 className="text-4xl md:text-6xl font-bold ml-4 bg-gradient-to-r from-green-700 to-green-500 bg-clip-text text-transparent">
                Pied Piper
              </h1>
            </div>
            <p className="text-xl md:text-2xl text-gray-600 italic mb-8">
              making the world a better place...through sound
            </p>
            <h2 className="text-3xl md:text-5xl font-bold text-gray-800 mb-6">
              Meet <span className="text-green-600">Pipey</span>, Your AI Music Companion
            </h2>
            <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-3xl">
              Discover new music, explore your favorite artists, and dive deep into the world of sound with an AI
              companion that understands your musical taste.
            </p>
            <Link href="/chat">
              <Button className="bg-green-600 hover:bg-green-700 text-white px-8 py-6 rounded-full text-lg font-medium transition-all hover:scale-105 shadow-lg flex items-center gap-2">
                Talk to Pipey <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-20">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 text-gray-800">What Makes Pipey Special?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          <FeatureCard
            icon={<TrendingUp className="h-10 w-10 text-green-600" />}
            title="Latest Music Trends"
            description="Pipey stays up-to-date with the latest music trends, chart-toppers, and emerging artists so you're always in the know."
          />
          <FeatureCard
            icon={<Music className="h-10 w-10 text-green-600" />}
            title="Deep Music Knowledge"
            description="From classical to hip-hop, Pipey can discuss music theory, history, artists, albums, and help you discover new sounds."
          />
          <FeatureCard
            icon={<Globe className="h-10 w-10 text-green-600" />}
            title="Multilingual Support"
            description="Pipey speaks multiple languages, making music discussions accessible to everyone around the world."
          />
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-green-50 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 text-gray-800">How Pipey Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
            <div>
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="bg-green-600 p-4 flex items-center">
                  <div className="h-10 w-10 bg-white rounded-full flex items-center justify-center">
                    <img src="/piedpiperlogo.jpg" alt="Pied Piper Logo" className="h-6 w-6 object-contain rounded" />
                  </div>
                  <h3 className="text-white font-medium ml-3">Pipey</h3>
                </div>
                <div className="p-6">
                  <div className="flex items-start mb-6">
                    <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Headphones className="h-5 w-5 text-green-600" />
                    </div>
                    <div className="ml-4 bg-green-100 rounded-lg p-3 rounded-tl-none">
                      <p className="text-gray-700">Hi there! I'm Pipey. What kind of music are you into?</p>
                    </div>
                  </div>
                  <div className="flex items-start justify-end">
                    <div className="mr-4 bg-white border border-gray-200 rounded-lg p-3 rounded-tr-none">
                      <p className="text-gray-700">I love indie rock. Any recommendations?</p>
                    </div>
                    <div className="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-medium text-gray-600">You</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800 mb-6">Text In, Voice Out</h3>
              <p className="text-lg text-gray-600 mb-6">
                Pipey creates a unique experience where you type your questions and thoughts about music, and Pipey
                responds with a natural voice.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start">
                  <div className="h-6 w-6 rounded-full bg-green-600 text-white flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-sm font-bold">1</span>
                  </div>
                  <p className="ml-4 text-gray-700">Type your music questions or topics you want to discuss</p>
                </li>
                <li className="flex items-start">
                  <div className="h-6 w-6 rounded-full bg-green-600 text-white flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-sm font-bold">2</span>
                  </div>
                  <p className="ml-4 text-gray-700">Pipey processes your request using advanced AI</p>
                </li>
                <li className="flex items-start">
                  <div className="h-6 w-6 rounded-full bg-green-600 text-white flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-sm font-bold">3</span>
                  </div>
                  <p className="ml-4 text-gray-700">Listen to Pipey's voice response with rich musical insights</p>
                </li>
              </ul>
              <div className="mt-10">
                <Link href="/chat">
                  <Button className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-full font-medium transition-all hover:scale-105 shadow-md flex items-center gap-2">
                    Try It Now <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-6 md:mb-0">
              <div className="h-10 w-10 relative">
                <img src="/piedpiperlogo.jpg" alt="Pied Piper Logo" className="h-full w-full object-contain rounded" />
              </div>
              <p className="ml-3 text-sm">© {new Date().getFullYear()} Pied Piper. All rights reserved.</p>
            </div>
            <p className="text-sm text-gray-400 italic">making the world a better place...through sound</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-8 transition-all hover:shadow-xl hover:-translate-y-1">
      <div className="bg-green-50 w-20 h-20 rounded-full flex items-center justify-center mb-6 mx-auto">{icon}</div>
      <h3 className="text-xl font-bold text-gray-800 mb-4 text-center">{title}</h3>
      <p className="text-gray-600 text-center">{description}</p>
    </div>
  )
}
