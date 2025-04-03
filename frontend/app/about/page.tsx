"use client"

import Link from "next/link"

export default function AboutPage() {
  return (
    <div className="bg-white">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-heading font-bold text-center text-gray-900 mb-4">About AI Safety Papers</h1>
          <p className="text-xl text-gray-600 text-center max-w-3xl mx-auto">
            Our mission and the people behind this resource
          </p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4 text-gray-900">Our Mission</h2>
          <p className="text-gray-700 mb-4">
            AI Safety Papers is dedicated to collecting and organizing the most important research in the field of AI safety and alignment. 
            Our goal is to make this critical research more accessible to researchers, students, and anyone interested in ensuring that 
            artificial intelligence is developed safely and aligned with human values.
          </p>
          <p className="text-gray-700 mb-4">
            As AI systems become more powerful, ensuring they remain safe, beneficial, and aligned with human values becomes increasingly important. 
            This collection serves as a resource for those working on or interested in these crucial issues.
          </p>
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4 text-gray-900">The Creator</h2>
          <p className="text-gray-700 mb-4">
            AI Safety Papers is a side project created by <a href="https://www.afspies.com/" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Alex Spies</a>, 
            a PhD Candidate at Imperial College London focused on Mechanistic Interpretability & Object-Centric Representations.
          </p>
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4 text-gray-900">Technology Stack</h2>
          <p className="text-gray-700 mb-4">
            This project leverages several modern technologies:
          </p>
          <ul className="list-disc pl-5 text-gray-700 space-y-2">
            <li>Next.js for the frontend framework</li>
            <li>Tailwind CSS for styling</li>
            <li>Claude 3.7-sonnet for summarizing articles and generating insights</li>
            <li>TypeScript for type-safe code</li>
          </ul>
          <p className="text-gray-700 mt-4">
            The source code for this project is available on <a href="https://github.com/afspies/ai-safety-papers" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">GitHub</a>.
          </p>
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4 text-gray-900">What We Offer</h2>
          <ul className="list-disc pl-5 text-gray-700 space-y-2">
            <li>A curated selection of research papers on AI safety and Alignment</li>
            <li>Highlights of particularly important or influential works</li>
            <li>Easy navigation and search functionality</li>
            <li>Regular updates as new significant research emerges</li>
          </ul>
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4 text-gray-900">Contact Us</h2>
          <p className="text-gray-700 mb-4">
            Have suggestions for papers to include or other feedback? We'd love to hear from you. 
            Please reach out to us at <span className="text-blue-600">alex<span>&#64;</span>afspies<span>&#46;</span>com</span>.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-heading font-semibold mb-4 text-gray-900">Support This Project</h2>
          <p className="text-gray-700 mb-4">
            If you've found AI Safety Papers useful, consider buying me a coffee! This helps cover hosting costs and motivates further development.
          </p>
          <div className="mt-4">
            <iframe 
              id='kofiframe' 
              src='https://ko-fi.com/afspies/?hidefeed=true&widget=true&embed=true&preview=true' 
              style={{border: 'none', width: '100%', padding: '4px', background: 'transparent'}} 
              height='712' 
              title='afspies'
            />
          </div>
        </section>
      </div>
    </div>
  )
} 