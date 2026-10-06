'use client';

import React from 'react';
import SplineHeroBackground from './SplineHeroBackground';
import MobileHeroStatic from './MobileHeroStatic';
import { ChevronDown } from 'lucide-react';

interface HeroProps {
  sceneUrl?: string;
}

export default function Hero({ sceneUrl }: HeroProps) {
  return (
    <section className="relative w-full bg-black overflow-hidden rounded-none">
      {/* Static UI for Mobile, Tablet, and screens below full laptop width (< xl / < 1280px) */}
      <div className="block xl:hidden w-full">
        <MobileHeroStatic />
      </div>

      {/* Fullscreen 3D Spline Scene for Fullscreen Laptop & Desktop Displays (>= xl / >= 1280px) */}
      <div className="hidden xl:block relative w-full h-screen">
        <SplineHeroBackground sceneUrl={sceneUrl} interactive={false} />

        {/* Scroll Down Indicator - Zero radius, Sky Blue accent */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-2 pointer-events-auto">
          <a
            href="#overview"
            aria-label="Scroll to platform details"
            className="text-zinc-400 hover:text-sky-400 transition-colors animate-bounce p-2 flex flex-col items-center gap-1 text-xs font-mono tracking-widest uppercase rounded-none"
          >
            <span>Scroll To Explore</span>
            <ChevronDown className="w-5 h-5 text-sky-400" />
          </a>
        </div>
      </div>
    </section>
  );
}
