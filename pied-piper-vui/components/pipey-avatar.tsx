import { Avatar } from "@/components/ui/avatar"
import { Music } from "lucide-react"

export default function PipeyAvatar() {
  return (
    <Avatar className="h-8 w-8 bg-green-600 text-white">
      <Music className="h-5 w-5" />
    </Avatar>
  )
}
