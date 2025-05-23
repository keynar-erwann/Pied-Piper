import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { VoiceInterface } from "@/components/voice-interface";
import piedPiperLogo from "@assets/piedpiperlogo.jpg";
import { 
  Mic, 
  Search, 
  Music, 
  Globe, 
  Heart, 
  Brain,
  Code,
  ArrowRight,
  Github,
  Twitter
} from "lucide-react";

export default function Home() {
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);

  const features = [
    {
      icon: Search,
      title: "Web Search",
      description: "Search the entire web for song information, artist details, and music facts in real-time.",
      color: "from-emerald-600 to-emerald-500"
    },
    {
      icon: Music,
      title: "Find Lyrics",
      description: "Discover song lyrics, meanings, and background stories for any track you're curious about.",
      color: "from-emerald-500 to-blue-500"
    },
    {
      icon: Globe,
      title: "Multi-Language",
      description: "Communicate in English, Spanish, French, German, Italian, and Hindi.",
      color: "from-blue-500 to-purple-500"
    },
    {
      icon: Mic,
      title: "Voice Chat",
      description: "Have natural voice conversations about music, artists, and your favorite songs.",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: Heart,
      title: "Smart Recommendations",
      description: "Get personalized music suggestions based on your taste and current mood.",
      color: "from-green-400 to-blue-500"
    },
    {
      icon: Brain,
      title: "Music Knowledge",
      description: "Explore music history, genres, instruments, and fascinating musical facts.",
      color: "from-yellow-400 to-orange-500"
    }
  ];

  return (
    <div className="min-h-screen bg-slate-900 text-white overflow-x-hidden">
      {/* Background Animation */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900"></div>
        {/* Floating particles */}
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-emerald-600 rounded-full animate-bounce opacity-60"></div>
        <div className="absolute top-3/4 right-1/4 w-3 h-3 bg-blue-500 rounded-full animate-bounce opacity-40 animation-delay-1000"></div>
        <div className="absolute top-1/2 left-1/3 w-1 h-1 bg-emerald-500 rounded-full animate-bounce opacity-80 animation-delay-2000"></div>
        <div className="absolute bottom-1/4 right-1/3 w-2 h-2 bg-emerald-600 rounded-full animate-bounce opacity-50 animation-delay-500"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 p-6">
        <nav className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <img 
                src={piedPiperLogo} 
                alt="Pied Piper Logo" 
                className="w-10 h-10 rounded-lg shadow-lg"
              />
              {/* Sound wave animation around logo */}
              <div className="absolute -inset-2 opacity-30">
                <div className="w-1 h-8 bg-emerald-600 rounded-full absolute -left-4 top-1 animate-pulse"></div>
                <div className="w-1 h-6 bg-emerald-500 rounded-full absolute -left-6 top-2 animate-pulse animation-delay-300"></div>
                <div className="w-1 h-4 bg-blue-500 rounded-full absolute -left-8 top-3 animate-pulse animation-delay-600"></div>
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-600 to-emerald-500 bg-clip-text text-transparent">
                Pied Piper
              </h1>
              <p className="text-xs text-slate-400 font-mono">AI Music Companion</p>
            </div>
          </div>
          
          {/* Language Selector */}
          <div className="relative">
            <select className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all duration-200">
              <option value="en">🇺🇸 English</option>
              <option value="es">🇪🇸 Español</option>
              <option value="fr">🇫🇷 Français</option>
              <option value="de">🇩🇪 Deutsch</option>
              <option value="it">🇮🇹 Italiano</option>
              <option value="hi">🇮🇳 हिंदी</option>
            </select>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="relative z-10">
        {/* Hero Section */}
        <section className="min-h-screen flex items-center justify-center px-6">
          <div className="text-center max-w-4xl mx-auto">
            {/* Main Logo Display */}
            <div className="mb-8 flex justify-center">
              <div className="relative">
                <img 
                  src={piedPiperLogo} 
                  alt="Pied Piper" 
                  className="w-24 h-24 md:w-32 md:h-32 rounded-2xl shadow-2xl animate-bounce"
                />
                {/* Animated rings around logo */}
                <div className="absolute inset-0 rounded-2xl border-2 border-emerald-600 opacity-20 animate-ping"></div>
                <div className="absolute inset-0 rounded-2xl border border-emerald-500 opacity-40 animate-pulse"></div>
              </div>
            </div>

            {/* Tagline */}
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-emerald-600 via-emerald-500 to-blue-500 bg-clip-text text-transparent animate-pulse">
                Pied Piper
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-slate-400 mb-4 font-light">
              making the world a better place...
            </p>
            <p className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-emerald-500 to-blue-500 bg-clip-text text-transparent mb-12">
              through sound
            </p>

            {/* CTA Button */}
            <Button 
              onClick={() => setIsVoiceModalOpen(true)}
              className="group relative bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-blue-500 text-white font-semibold text-lg px-8 py-4 rounded-full shadow-2xl transform transition-all duration-300 hover:scale-105 hover:shadow-3xl focus:outline-none focus:ring-4 focus:ring-emerald-600 focus:ring-opacity-50 h-auto"
            >
              <span className="flex items-center space-x-3">
                <Mic className="text-xl group-hover:animate-pulse" />
                <span>Talk with Pied Piper</span>
                <ArrowRight className="text-sm transform group-hover:translate-x-1 transition-transform" />
              </span>
              {/* Glow effect */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-emerald-600 to-emerald-500 opacity-20 blur-xl group-hover:opacity-40 transition-opacity"></div>
            </Button>

            {/* Hackathon badge */}
            <div className="mt-8">
              <Badge variant="secondary" className="inline-flex items-center space-x-2 bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-full px-4 py-2">
                <Code className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-mono text-slate-400">Built with ❤️ for music lovers</span>
              </Badge>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-6">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold text-center mb-16">
              <span className="bg-gradient-to-r from-emerald-600 to-emerald-500 bg-clip-text text-transparent">
                What Pied Piper Can Do
              </span>
            </h2>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <Card key={index} className="group relative bg-slate-800/30 backdrop-blur-sm border border-slate-700 rounded-2xl hover:border-emerald-600 transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-600/20">
                  <CardContent className="p-6">
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-600/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="relative z-10">
                      <div className={`w-12 h-12 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                        <feature.icon className="text-white text-lg" />
                      </div>
                      <h3 className="text-xl font-semibold mb-3 text-white">{feature.title}</h3>
                      <p className="text-slate-400 leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Tech Stack Section */}
        <section className="py-20 px-6 border-t border-slate-800">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-2xl md:text-3xl font-bold mb-8">
              <span className="bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                Built with Modern Tech
              </span>
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="flex flex-col items-center space-y-2 group">
                <div className="w-16 h-16 bg-slate-800 rounded-xl flex items-center justify-center group-hover:bg-slate-700 transition-colors">
                  <span className="text-2xl">🐍</span>
                </div>
                <span className="text-sm font-mono text-slate-400">Python</span>
              </div>
              
              <div className="flex flex-col items-center space-y-2 group">
                <div className="w-16 h-16 bg-slate-800 rounded-xl flex items-center justify-center group-hover:bg-slate-700 transition-colors">
                  <Mic className="text-2xl text-blue-500" />
                </div>
                <span className="text-sm font-mono text-slate-400">LiveKit</span>
              </div>
              
              <div className="flex flex-col items-center space-y-2 group">
                <div className="w-16 h-16 bg-slate-800 rounded-xl flex items-center justify-center group-hover:bg-slate-700 transition-colors">
                  <span className="text-2xl">🤖</span>
                </div>
                <span className="text-sm font-mono text-slate-400">AI/ML</span>
              </div>
              
              <div className="flex flex-col items-center space-y-2 group">
                <div className="w-16 h-16 bg-slate-800 rounded-xl flex items-center justify-center group-hover:bg-slate-700 transition-colors">
                  <span className="text-2xl">☁️</span>
                </div>
                <span className="text-sm font-mono text-slate-400">Cloud APIs</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800 py-8 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <img src={piedPiperLogo} alt="Pied Piper" className="w-6 h-6 rounded" />
            <span className="font-bold text-emerald-600">Pied Piper</span>
          </div>
          <p className="text-slate-400 text-sm font-mono">
            Making the world a better place through sound • Built with ❤️ for music lovers
          </p>
          <div className="flex justify-center space-x-4 mt-4">
            <Github className="text-slate-400 hover:text-emerald-600 cursor-pointer transition-colors" />
            <Twitter className="text-slate-400 hover:text-blue-500 cursor-pointer transition-colors" />
            <Music className="text-slate-400 hover:text-emerald-500 cursor-pointer transition-colors" />
          </div>
        </div>
      </footer>

      {/* Voice Interface Modal */}
      <VoiceInterface 
        isOpen={isVoiceModalOpen} 
        onClose={() => setIsVoiceModalOpen(false)} 
      />
    </div>
  );
}
