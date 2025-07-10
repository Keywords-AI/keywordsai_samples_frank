// src/app/page.tsx
/**
 * Main landing page - shows the game front page with level selection
 */

"use client";
import GameFrontPage from "@/components/pages/GameFrontPage";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  const handleStartLevel = (levelId: number) => {
    // Navigate to level 1
    router.push('/level1');
  };

  const handleStartSandbox = () => {
    // Navigate to sandbox mode
    router.push('/sandbox');
  };

  return <GameFrontPage onStartLevel={handleStartLevel} onStartSandbox={handleStartSandbox} />;
}
