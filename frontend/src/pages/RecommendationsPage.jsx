import React from 'react';
import RecommendationEngine from '../components/RecommendationEngine';

export default function RecommendationsPage() {
  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-extrabold text-[var(--text-900)]">Crop Recommendations</h2>
        <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">High Profit Suggestion Engine</p>
      </div>
      <RecommendationEngine />
    </div>
  );
}
