// src/components/pages/GameFrontPage.tsx
/**
 * Game Front Page - Main menu for AI Blocks game
 * Allows players to select levels and start playing
 */

"use client";

interface GameFrontPageProps {
  onStartLevel: (levelId: number) => void;
  onStartSandbox: () => void;
}

export default function GameFrontPage({ onStartLevel, onStartSandbox }: GameFrontPageProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#151519' }}>
      <div className="max-w-4xl w-full text-center">
        {/* Game Logo/Title */}
        <div className="mb-12 mt-16">
          <h1 className="text-6xl font-medium text-white mb-4 drop-shadow-2xl font-inter">
            Keywords AI Blocks
          </h1>
          <p className="text-xl text-gray-300 mb-2 font-medium">
                            Build Workflows with Visual Programming
          </p>
          <p className="text-md text-gray-400">
                            Connect all blocks to create complete workflows
          </p>
        </div>

        {/* Levels Row */}
        <div className="rounded-2xl p-8 border shadow-2xl mb-8" style={{ backgroundColor: '#1a1a1e', borderColor: '#2a2a2e' }}>
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Choose Your Level</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Level 1 */}
            <div 
              onClick={() => onStartLevel(1)}
              className="text-white p-6 rounded-xl cursor-pointer transform hover:scale-105 transition-all duration-200 
                         shadow-xl hover:shadow-2xl border hover:border-gray-400"
              style={{ 
                background: 'linear-gradient(to right, #2a2a2e, #232327)',
                borderColor: '#2a2a2e'
              }}
            >
              <div className="text-center">
                <h3 className="text-xl font-bold mb-3 text-white">
                  📅 Level 1
                </h3>
                <h4 className="text-lg font-semibold mb-2 text-gray-200">
                  Meeting Scheduler
                </h4>
                <p className="text-gray-300 text-sm mb-4">
                  Build a workflow that schedules meetings automatically
                </p>
                <div className="flex justify-center space-x-2 mb-4 text-xs">
                  <span className="bg-green-600 bg-opacity-80 px-2 py-1 rounded-full text-white">
                    🎯 Beginner
                  </span>
                  <span className="bg-blue-600 bg-opacity-80 px-2 py-1 rounded-full text-white">
                    ⏱️ 2-5min
                  </span>
                </div>
                <div className="text-3xl mb-2">▶️</div>
                <div className="text-sm text-gray-300 font-medium">PLAY NOW</div>
              </div>
            </div>

            {/* Level 2 */}
            <div 
              className="p-6 rounded-xl border-2 border-dashed hover:border-gray-400 transition-colors"
              style={{ 
                backgroundColor: '#1e1e22', 
                borderColor: '#2a2a2e' 
              }}
            >
              <div className="text-center">
                <h3 className="text-xl font-bold mb-3 text-gray-200">
                  💬 Level 2
                </h3>
                <h4 className="text-lg font-semibold mb-2 text-gray-300">
                  LLM Poker Fight
                </h4>
                <p className="text-gray-300 text-sm mb-4">
                  Build three LLMs that fight each other to win the game
                </p>
                <div className="flex justify-center space-x-2 mb-4 text-xs">
                  <span className="bg-gray-600 px-2 py-1 rounded-full text-gray-300">
                    🎯 Medium
                  </span>
                  <span className="bg-gray-600 px-2 py-1 rounded-full text-gray-300">
                    ⏱️ 10min
                  </span>
                </div>
                <div className="text-3xl mb-2 text-gray-500">🔒</div>
                <span className="text-gray-400 text-sm font-medium">Coming Soon</span>
              </div>
            </div>

            {/* Level 3 */}
            <div 
              className="p-6 rounded-xl border-2 border-dashed hover:border-gray-400 transition-colors"
              style={{ 
                backgroundColor: '#1e1e22', 
                borderColor: '#2a2a2e' 
              }}
            >
              <div className="text-center">
                <h3 className="text-xl font-bold mb-3 text-gray-200">
                  📊 Level 3
                </h3>
                <h4 className="text-lg font-semibold mb-2 text-gray-300">
                  Crypto Trader
                </h4>
                <p className="text-gray-300 text-sm mb-4">
                  Create a workflow that can analyze and trade crypto
                </p>
                <div className="flex justify-center space-x-2 mb-4 text-xs">
                  <span className="bg-gray-600 px-2 py-1 rounded-full text-gray-300">
                    🎯 Advanced
                  </span>
                  <span className="bg-gray-600 px-2 py-1 rounded-full text-gray-300">
                    ⏱️ 15min
                  </span>
                </div>
                <div className="text-3xl mb-2 text-gray-500">🔒</div>
                <span className="text-gray-400 text-sm font-medium">Coming Soon</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sandbox Mode */}
        <div className="rounded-2xl p-8 border shadow-2xl" style={{ backgroundColor: '#1a1a1e', borderColor: '#2a2a2e' }}>
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Sandbox Mode</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Sandbox Card */}
            <div 
              onClick={onStartSandbox}
              className="text-white p-6 rounded-xl cursor-pointer transform hover:scale-105 transition-all duration-200 
                         shadow-xl hover:shadow-2xl border hover:border-gray-400"
              style={{ 
                background: 'linear-gradient(to right, #2a2a2e, #232327)',
                borderColor: '#2a2a2e'
              }}
            >
              <div className="text-center">
                <h3 className="text-xl font-bold mb-3 text-white">
                  🔧 Sandbox
                </h3>
                <h4 className="text-lg font-semibold mb-2 text-gray-200">
                  Free Play Mode
                </h4>
                <p className="text-gray-300 text-sm mb-4">
                  Experiment with all blocks and create your own workflows without restrictions
                </p>
                <div className="flex justify-center space-x-2 mb-4 text-xs">
                  <span className="bg-gray-600 bg-opacity-80 px-2 py-1 rounded-full text-white">
                    🎨 Creative
                  </span>
                  <span className="bg-gray-600 bg-opacity-80 px-2 py-1 rounded-full text-white">
                    🔓 Unlimited
                  </span>
                </div>
                <div className="text-3xl mb-2">🚀</div>
                <div className="text-sm text-gray-300 font-medium">START BUILDING</div>
              </div>
            </div>

            {/* Real Deploying Card */}
            <div 
              onClick={() => window.open('https://www.keywordsai.co/', '_blank')}
              className="text-white p-6 rounded-xl cursor-pointer transform hover:scale-105 transition-all duration-200 
                         shadow-xl hover:shadow-2xl border hover:border-blue-400"
              style={{ 
                background: 'linear-gradient(to right, #1e40af, #2563eb)',
                borderColor: '#2563eb'
              }}
            >
              <div className="text-center">
                <h3 className="text-xl font-bold mb-3 text-white">
                  🚀 Real Deploying
                </h3>
                <h4 className="text-lg font-semibold mb-2 text-blue-100">
                  Keywords AI Platform
                </h4>
                <p className="text-blue-100 text-sm mb-4">
                  Trace your AI workflows to production with our professional platform
                </p>
                <div className="flex justify-center space-x-2 mb-4 text-xs">
                  <span className="bg-blue-800 bg-opacity-80 px-2 py-1 rounded-full text-white">
                    🏭 Production
                  </span>
                  <span className="bg-blue-800 bg-opacity-80 px-2 py-1 rounded-full text-white">
                    ⚡ Scale
                  </span>
                </div>
                <div className="text-3xl mb-2">🌐</div>
                <div className="text-sm text-blue-200 font-medium">VISIT PLATFORM</div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <a 
            href="https://www.keywordsai.co/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-white text-sm flex items-center justify-center space-x-2 transition-colors"
          >
            <span>Powered by</span>
            <span className="font-semibold">Keywords AI</span>
          </a>
        </div>
      </div>
    </div>
  );
} 