import Link from "next/link"

export default function PaperNotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4">
      <h2 className="text-2xl font-bold mb-4 text-center">Paper Not Found</h2>
      <p className="text-gray-600 mb-6 text-center max-w-md">
        The paper you're looking for doesn't exist or has been removed.
      </p>
      <Link
        href="/"
        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors text-center"
      >
        Go back home
      </Link>
    </div>
  )
}

