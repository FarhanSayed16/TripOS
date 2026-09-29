"use client";

import dynamic from "next/dynamic";

// Dynamic imports with ssr: false — only runs in the browser
const Player = dynamic(
  () => import("@lottiefiles/react-lottie-player").then((m) => m.Player),
  { ssr: false }
);

export function LottieWorldMap() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-[45%] w-[160%] opacity-[0.12] mix-blend-screen">
        <Player
          src="/lottie/world_map.json"
          loop
          autoplay
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
}

export function LottieGlobe() {
  return (
    <div className="w-44 h-44 mx-auto drop-shadow-[0_0_30px_rgba(20,184,166,0.25)]">
      <Player
        src="/lottie/loading.json"
        loop
        autoplay
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}
