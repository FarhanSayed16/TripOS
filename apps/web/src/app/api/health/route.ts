import { NextResponse } from "next/server";

export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const isProd = process.env.NODE_ENV === "production";

  if (!apiUrl) {
    return NextResponse.json(
      {
        status: "error",
        message: isProd
          ? "NEXT_PUBLIC_API_URL is not configured"
          : "NEXT_PUBLIC_API_URL missing; set it in .env.local (dev fallback not used for health)",
      },
      { status: isProd ? 503 : 500 }
    );
  }

  try {
    const response = await fetch(`${apiUrl.replace(/\/$/, "")}/health`, {
      cache: "no-store",
    });

    if (response.ok) {
      const data = await response.json();
      return NextResponse.json({ status: "ok", backend: data }, { status: 200 });
    }
    return NextResponse.json(
      { status: "error", message: "Backend unhealthy", upstream_status: response.status },
      { status: 502 }
    );
  } catch (error: unknown) {
    const details = error instanceof Error ? error.message : "unknown";
    return NextResponse.json(
      { status: "error", message: "Backend unreachable", details },
      { status: 503 }
    );
  }
}
