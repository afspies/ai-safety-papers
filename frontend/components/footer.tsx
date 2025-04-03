"use client"

export default function Footer() {
  return (
    <footer className="bg-blue-600 text-white py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <h2 className="text-xl font-bold">AI Safety Papers</h2>
            <p className="text-gray-300">A curated selection of research papers on AI safety and Alignment</p>
          </div>
          <div>
            <p className="text-gray-300">© {new Date().getFullYear()} AI Safety Papers</p>
          </div>
        </div>
      </div>
    </footer>
  )
}

