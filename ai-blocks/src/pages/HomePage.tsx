// src/pages/HomePage.tsx
/**
 * Home Page - Main landing page with level selection and sandbox access
 * Unified page component that replaces GameFrontPage
 */

"use client";
import { useRouter } from "next/navigation";
import { APP_CONFIG } from "@/config";
import { levelManager } from "@/features/levels";

export default function HomePage() {
  const router = useRouter();

  const handleStartLevel = (levelId: string) => {
    // Map level IDs to their actual route paths
    const levelRoutes: Record<string, string> = {
      'level-1': '/level1',
      'level-2': '/level2',
      'level-3': '/level3',
    };
    
    const route = levelRoutes[levelId] || `/level${levelId.replace('level-', '')}`;
    router.push(route);
  };



  const availableLevels = Object.values(APP_CONFIG.levels).filter(level => 
    levelManager.isLevelUnlocked(level.id)
  );
  const comingSoonLevels = Object.values(APP_CONFIG.levels).filter(level => 
    !levelManager.isLevelUnlocked(level.id)
  );

  return (
    <div className="min-h-screen bg-gray-200 text-slate-900">
      <div className="max-w-6xl mx-auto px-6 py-40">
        {/* Hero Section */}
        <div className="text-center mb-24 mt-8">
          <h1 className="text-6xl font-bold text-slate-700 mb-6 tracking-tight">
            {APP_CONFIG.app.name}
          </h1>
          <p className="text-2xl text-slate-600 mb-6 font-medium">
            {APP_CONFIG.app.tagline}
          </p>
          <p className="text-lg text-slate-500 mb-8 max-w-3xl mx-auto leading-relaxed">
            {APP_CONFIG.app.description}
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <span className="bg-gray-100 border border-gray-300 px-4 py-2 rounded-lg text-slate-600 font-medium">
              Agent Design
            </span>
            <span className="bg-gray-100 border border-gray-300 px-4 py-2 rounded-lg text-slate-800 font-medium">
              State Machines
            </span>
            <span className="bg-gray-100 border border-gray-300 px-4 py-2 rounded-lg text-gray-800 font-medium">
              Rapid Prototyping
            </span>
          </div>
        </div>

        {/* Workflow Builder Section */}
        <div className="bg-gray-200 rounded-xl p-8 mb-20">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-semibold text-slate-700 mb-4">Workflow Builder</h2>
            <p className="text-slate-600 max-w-2xl mx-auto text-lg">
              Create sophisticated AI agent behaviors with our drag-and-drop interface.
            </p>
          </div>
          
          {/* Visual Workflow Builder */}
          <div 
            onClick={() => router.push('/sandbox')}
            className="cursor-pointer transform hover:scale-[1.01] transition-all duration-200 mx-auto w-full relative group"
          >
            {/* Workflow Image */}
            <div className="relative w-full">
              <img 
                src="/build_ui.png" 
                alt="Workflow Builder Interface" 
                className="w-full h-auto rounded-lg"
              />
              <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-20 transition-all duration-200 rounded-lg flex items-center justify-center opacity-0 hover:opacity-100">
                <div className="text-center text-white">
                  <p className="text-lg font-medium mb-2">Visual Workflow Designer</p>
                  <p className="text-sm">Click to start building</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Tutorials Section */}
        <div className="bg-gray-200 p-8 py-12 mb-20">
          <h2 className="text-4xl font-semibold text-slate-700 mb-4 text-center">Learn with Interactive Tutorials</h2>
          <p className="text-slate-600 text-center mb-8 max-w-2xl mx-auto">
            Master agent workflow design through hands-on tutorials and examples.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Available Levels */}
            {availableLevels.map((level) => (
              <div 
                key={level.id}
                onClick={() => handleStartLevel(level.id)}
                className="bg-gray-50 border border-gray-300 p-6 rounded-xl cursor-pointer transform hover:scale-[1.02] transition-all duration-200 
                           shadow-sm hover:shadow-md hover:border-gray-400"
              >
                <div className="text-center">
                  <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h4 className="text-xl font-bold mb-2 text-slate-900">
                    {level.title.split(' - ')[0]}
                  </h4>
                  <h5 className="text-lg font-semibold mb-3 text-slate-700">
                    {level.title.split(' - ')[1] || level.title}
                  </h5>
                  <p className="text-slate-600 text-sm mb-4 leading-relaxed">
                    {level.description}
                  </p>
                  <div className="flex justify-center space-x-2 mb-4 text-xs">
                    <span className="bg-gray-200 text-slate-700 px-3 py-1 rounded-full font-medium capitalize">
                      {level.difficulty}
                    </span>
                    <span className="bg-gray-200 text-slate-700 px-3 py-1 rounded-full font-medium">
                      {level.estimatedDuration}
                    </span>
                  </div>
                  <div className="text-sm text-slate-700 font-semibold">START TUTORIAL</div>
                </div>
              </div>
            ))}

            {/* Coming Soon Levels */}
            {comingSoonLevels.map((level) => (
              <div 
                key={level.id}
                className="bg-gray-200 border-2 border-dashed border-gray-400 p-6 rounded-xl opacity-60"
              >
                <div className="text-center">
                  <div className="w-12 h-12 bg-gray-300 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <h4 className="text-xl font-bold mb-2 text-slate-500">
                    {level.title.split(' - ')[0]}
                  </h4>
                  <h5 className="text-lg font-semibold mb-3 text-slate-500">
                    {level.title.split(' - ')[1] || level.title}
                  </h5>
                  <p className="text-slate-500 text-sm mb-4 leading-relaxed">
                    {level.description}
                  </p>
                  <div className="flex justify-center space-x-2 mb-4 text-xs">
                    <span className="bg-slate-200 text-slate-500 px-3 py-1 rounded-full font-medium capitalize">
                      {level.difficulty}
                    </span>
                    <span className="bg-slate-200 text-slate-500 px-3 py-1 rounded-full font-medium">
                      {level.estimatedDuration}
                    </span>
                  </div>
                  <span className="text-slate-500 text-sm font-semibold">Coming Soon</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Production Deployment */}
        <div className="bg-gray-200 p-8 py-12">
          <h2 className="text-3xl font-semibold text-slate-700 mb-6 text-center">Ready for Production?</h2>
          <p className="text-slate-600 text-center mb-8 max-w-2xl mx-auto">
            Once you've designed your agent workflows, deploy them to production with enterprise-grade monitoring and scaling.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Features Card */}
            <div className="bg-gray-100 border border-gray-300 p-6 rounded-xl">
              <div>
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-6 text-slate-900 text-center">
                  Why {APP_CONFIG.app.name}?
                </h3>
                <div className="space-y-4 text-sm text-slate-700">
                  <div className="flex items-center space-x-3">
                    <div className="w-5 h-5 bg-gray-200 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-slate-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span>Visual workflow design eliminates complex coding</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-5 h-5 bg-gray-200 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-slate-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span>Rapid prototyping and testing of agent behaviors</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-5 h-5 bg-gray-200 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-slate-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span>Enterprise-grade monitoring and observability</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-5 h-5 bg-gray-200 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-slate-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span>Seamless deployment to production environments</span>
                  </div>
                </div>
              </div>
            </div>

            {/* CTA Card */}
            <div className="bg-gray-100 border border-gray-300 p-6 rounded-xl">
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-4 text-slate-900">
                  Get Started Today
                </h3>
                <p className="text-slate-600 text-sm mb-6">
                  Deploy your AI agent workflows to production with Keywords AI.
                </p>
                <a
                  href="https://keywordsai.co"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block bg-slate-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-slate-800 transition-colors"
                >
                  Get Started with Keywords AI
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 