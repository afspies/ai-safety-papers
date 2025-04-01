import Loading from "@/components/loading";
import { AllPapers } from "@/components/papers-all";
import SearchDesktop, { SearchMobile } from "@/components/search";
import { getAllPapers } from "@/lib/api";
import { Suspense } from "react";
import FilterToggle from "../components/filter-toggle";

export default async function Home() {
  const papers = await getAllPapers();

  return (
    <div className="bg-white">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-heading font-bold text-center text-gray-900 mb-4">
            AI Safety Papers
          </h1>
          <p className="text-xl text-gray-600 text-center max-w-3xl mx-auto">
            A collection of important research papers on AI safety and alignment
          </p>
        </div>
      </div>

      <Suspense fallback={<Loading />}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Responsive header section */}
          <div className="mb-8">
            {/* Mobile: Title and filter on same line, search below */}
            <div className="md:hidden">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-heading font-semibold text-gray-900">
                  Papers
                </h2>
                <FilterToggle />
              </div>
              <div className="w-full">
                <SearchMobile />
              </div>
            </div>

            {/* Desktop: Title on left, search and filter on right */}
            <div className="hidden md:flex md:justify-between md:items-center">
              <h2 className="text-2xl font-heading font-semibold text-gray-900">
                Papers
              </h2>
              <div className="flex items-center space-x-4">
                <SearchDesktop />
                <FilterToggle />
              </div>
            </div>
          </div>

          <AllPapers papers={papers} />
        </div>
      </Suspense>
    </div>
  );
}
