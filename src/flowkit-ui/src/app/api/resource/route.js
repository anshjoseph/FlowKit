// app/api/resource/route.js
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_NODE_RUNNER;
    const response = await fetch(`${baseUrl}/npu/all`, {
      method: "GET",
      headers: {
        accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching from Node Runner:", error);
    return NextResponse.json(
      { error: "Failed to fetch resources", details: error.message },
      { status: 500 }
    );
  }
}
