import { type NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    const { text, language = "en" } = await req.json()

    // ElevenLabs API endpoint for text-to-speech
    const url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" // Default voice ID

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "xi-api-key": process.env.ELEVEN_API_KEY || "",
      },
      body: JSON.stringify({
        text: text,
        model_id: "eleven_monolingual_v1",
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
        },
      }),
    })

    if (!response.ok) {
      throw new Error(`ElevenLabs API error: ${response.status}`)
    }

    // Get the audio data as an ArrayBuffer
    const audioData = await response.arrayBuffer()

    // Convert to base64 for sending to the client
    const base64Audio = Buffer.from(audioData).toString("base64")

    return NextResponse.json({
      success: true,
      audioContent: base64Audio,
    })
  } catch (error) {
    console.error("Error in speech API:", error)
    return NextResponse.json(
      {
        success: false,
        error: "Failed to generate speech",
      },
      {
        status: 500,
      },
    )
  }
}
