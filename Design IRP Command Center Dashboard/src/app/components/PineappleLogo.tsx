import React from 'react';

export function PineappleLogo({ className = "w-8 h-8" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Crown/leaves */}
      <path
        d="M50 10 L45 25 L50 20 L55 25 L50 10Z"
        fill="currentColor"
        className="text-green-500"
      />
      <path
        d="M40 15 L38 28 L43 23 L40 15Z"
        fill="currentColor"
        className="text-green-500"
      />
      <path
        d="M60 15 L62 28 L57 23 L60 15Z"
        fill="currentColor"
        className="text-green-500"
      />
      <path
        d="M35 20 L34 30 L38 27 L35 20Z"
        fill="currentColor"
        className="text-green-600"
      />
      <path
        d="M65 20 L66 30 L62 27 L65 20Z"
        fill="currentColor"
        className="text-green-600"
      />
      
      {/* Pineapple body */}
      <ellipse cx="50" cy="55" rx="22" ry="30" fill="currentColor" className="text-amber-500" />
      
      {/* Pattern/texture */}
      <path
        d="M40 35 L45 40 M45 40 L40 45 M40 45 L45 50 M45 50 L40 55"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-amber-600"
        strokeLinecap="round"
      />
      <path
        d="M50 35 L55 40 M55 40 L50 45 M50 45 L55 50 M55 50 L50 55"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-amber-600"
        strokeLinecap="round"
      />
      <path
        d="M60 35 L55 40 M55 50 L60 55 M60 45 L55 50"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-amber-600"
        strokeLinecap="round"
      />
      <path
        d="M45 55 L40 60 M40 60 L45 65 M45 65 L40 70"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-amber-700"
        strokeLinecap="round"
      />
      <path
        d="M55 55 L60 60 M60 60 L55 65 M55 65 L60 70"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-amber-700"
        strokeLinecap="round"
      />
      <path
        d="M50 60 L45 65 M45 65 L50 70 M50 70 L55 75"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-amber-700"
        strokeLinecap="round"
      />
    </svg>
  );
}
