import { type NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    const { messages, language = "en" } = await req.json()

    // Get the last user message
    const lastUserMessage = messages.filter((m: any) => m.role === "user").pop()

    if (!lastUserMessage) {
      return NextResponse.json({ error: "No user message found" }, { status: 400 })
    }

    // Use Groq API for chat completion
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.GROQ_API_KEY}`,
      },
      body: JSON.stringify({
        model: "llama3-70b-8192",
        messages: [
          {
            role: "system",
            content: `You are Pipey, an AI music companion from Pied Piper. 
            You're passionate and knowledgeable about all aspects of music - artists, genres, songs, albums, music history, instruments, etc.
            Be enthusiastic and show your love for music. Share interesting facts about songs, artists, and music history.
            Your responses should be conversational, engaging, and informative.
            Your goal is to help users discover and appreciate music in all its forms.
            Keep your responses relatively concise (1-3 paragraphs) as they will be converted to speech.
            Respond in ${language} language.`,
          },
          ...messages.map((m: any) => ({
            role: m.role,
            content: m.content,
          })),
        ],
        temperature: 0.7,
        max_tokens: 500,
      }),
    })

    if (!response.ok) {
      throw new Error(`Groq API error: ${response.status}`)
    }

    const data = await response.json()
    const assistantResponse = data.choices[0].message.content

    return NextResponse.json({ response: assistantResponse })
  } catch (error) {
    console.error("Error in chat API:", error)
    return NextResponse.json({ error: "Failed to generate response" }, { status: 500 })
  }
}
