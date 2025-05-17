import { type NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    const { query } = await req.json()

    // Construct the SerpAPI URL with your key
    const url = `https://serpapi.com/search.json?q=${encodeURIComponent(query)}&engine=google&api_key=${process.env.SERPAPI_KEY}`

    const response = await fetch(url)

    if (!response.ok) {
      throw new Error(`SerpAPI error: ${response.status}`)
    }

    const data = await response.json()

    return NextResponse.json({
      success: true,
      results: data,
    })
  } catch (error) {
    console.error("Error in search API:", error)
    return NextResponse.json(
      {
        success: false,
        error: "Failed to search for information",
      },
      {
        status: 500,
      },
    )
  }
}
