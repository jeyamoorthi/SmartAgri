import React from 'react';
import PestAlert from '../components/PestAlert';

export default function PestPage() {
  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-extrabold text-[var(--text-900)]">Pest & Disease Control</h2>
        <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Cluster Sighting Alerts</p>
      </div>
      <PestAlert />
    </div>
  );
}
