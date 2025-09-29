/**
 * Example usage of the Gabber NextJS Component
 *
 * This file shows how to integrate the GabberComponent into a NextJS application.
 * Copy this to your NextJS project and modify as needed.
 */

import GabberComponent from './components/gabber-nextjs-component';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-2xl font-bold text-gray-900">My Gabber App</h1>
            <nav className="flex space-x-4">
              <a href="#demo" className="text-gray-500 hover:text-gray-900">
                Demo
              </a>
              <a href="#docs" className="text-gray-500 hover:text-gray-900">
                Docs
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Gabber Streaming
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Experience real-time audio and video streaming with our powerful Gabber platform.
            Connect, stream, and interact in real-time.
          </p>
        </div>

        {/* Demo Section */}
        <section id="demo" className="mb-12">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Try the Echo Demo
            </h3>
            <p className="text-gray-600 mb-6">
              This demo uses the built-in echo functionality to stream your audio and video back to you.
              Perfect for testing your setup and getting familiar with the Gabber platform.
            </p>

            {/* Basic Gabber Component */}
            <GabberComponent
              runId="demo-session"
              className="border border-gray-200 rounded-lg"
            />
          </div>
        </section>

        {/* Advanced Configuration */}
        <section id="advanced" className="mb-12">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Advanced Configuration
            </h3>
            <p className="text-gray-600 mb-6">
              You can customize the component with different configurations:
            </p>

            {/* Custom Graph Example */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-2">Custom Graph</h4>
              <GabberComponent
                runId="custom-graph-demo"
                showDebug={true}
                className="border border-blue-200"
                // graph={yourCustomGraph} // Uncomment and add your graph
              />
            </div>

            {/* App ID Example */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Using App ID</h4>
              <GabberComponent
                appId="your-app-id" // Replace with your actual app ID
                runId="app-id-demo"
                className="border border-green-200"
              />
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="mb-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Real-time Streaming
              </h3>
              <p className="text-gray-600">
                Ultra-low latency audio and video streaming with WebRTC technology.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Flexible Configuration
              </h3>
              <p className="text-gray-600">
                Use graphs or app IDs to customize your streaming experience.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Easy Integration
              </h3>
              <p className="text-gray-600">
                Drop the component into any NextJS project with minimal setup.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>© 2024 Gabber. Built with NextJS and the Gabber React SDK.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
