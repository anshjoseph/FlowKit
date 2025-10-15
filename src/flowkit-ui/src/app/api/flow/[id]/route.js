import { NextResponse } from "next/server";

export async function GET(request, context) {
  const { id } = await context.params;;

  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_FCU}/flow/${id}`, {
      method: "GET",
      headers: {
        accept: "application/json",
      },
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: `Request failed with status ${res.status}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
