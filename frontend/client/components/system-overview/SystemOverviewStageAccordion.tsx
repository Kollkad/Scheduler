// frontend/client/components/system-overview/SystemOverviewStageAccordion.tsx

import { useState } from "react";

interface StageAccordionProps {
  title: string;
  description?: string;
  checks: string[];
}

export function SystemOverviewStageAccordion({ title, description, checks }: StageAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-border-default rounded-lg">
      <button
        className="w-full px-4 py-3 text-left flex justify-between items-center hover:bg-bg-default-light-field transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div>
          <h4 className="font-semibold text-text-primary">{title}</h4>
          {description && <p className="text-sm text-text-secondary mt-1">{description}</p>}
        </div>
        <svg 
          className={`w-5 h-5 text-gray-500 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isOpen && (
        <div className="px-4 pb-3">
          <ul className="list-disc list-inside text-sm text-text-secondary space-y-2 mt-2">
            {checks.map((check, index) => (
              <li key={index}>{check}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}


