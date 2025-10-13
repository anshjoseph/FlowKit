import { NextResponse } from "next/server";

const BASE_URL = process.env.NEXT_PUBLIC_SECRET_API;

// POST /api/kv -> set key-value
export async function POST(req) {
  try {
    const { key, value } = await req.json();

    const res = await fetch(`${BASE_URL}/set`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, value }),
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// GET /api/kv?key=example -> get value by key or list all keys
export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const key = searchParams.get("key");

  try {
    let res;
    if (key) {
      res = await fetch(`${BASE_URL}/get/${encodeURIComponent(key)}`);
    } else {
      res = await fetch(`${BASE_URL}/keys`);
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// DELETE /api/kv?key=example -> delete key
export async function DELETE(req) {
  const { searchParams } = new URL(req.url);
  const key = searchParams.get("key");

  if (!key) {
    return NextResponse.json({ error: "Missing key" }, { status: 400 });
  }

  try {
    const res = await fetch(`${BASE_URL}/delete/${encodeURIComponent(key)}`, {
      method: "DELETE",
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
