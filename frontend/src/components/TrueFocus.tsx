"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface TrueFocusProps {
  sentence?: string;
  manualMode?: boolean;
  blurAmount?: number;
  borderColor?: string;
  glowColor?: string;
  animationDuration?: number;
  pauseBetweenAnimations?: number;
}

export default function TrueFocus({
  sentence = "Inteligencia Inmobiliaria en CABA",
  manualMode = false,
  blurAmount = 4,
  borderColor = "#3b82f6",
  glowColor = "rgba(59, 130, 246, 0.5)",
  animationDuration = 0.5,
  pauseBetweenAnimations = 1,
}: TrueFocusProps) {
  const words = sentence.split(" ");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [lastActiveIndex, setLastActiveIndex] = useState<number | null>(null);

  useEffect(() => {
    if (manualMode) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % words.length);
    }, (animationDuration + pauseBetweenAnimations) * 1000);

    return () => clearInterval(interval);
  }, [manualMode, animationDuration, pauseBetweenAnimations, words.length]);

  return (
    <div className="relative flex flex-wrap items-center justify-center gap-x-3 gap-y-2 py-2">
      {words.map((word, index) => {
        const isActive = index === currentIndex;

        return (
          <span
            key={index}
            onMouseEnter={() => {
              if (manualMode) {
                setLastActiveIndex(index);
                setCurrentIndex(index);
              }
            }}
            onMouseLeave={() => {
              if (manualMode && lastActiveIndex !== null) {
                setCurrentIndex(lastActiveIndex);
              }
            }}
            className="relative cursor-pointer text-3xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl select-none"
            style={{
              filter: isActive ? "blur(0px)" : `blur(${blurAmount}px)`,
              transition: `filter ${animationDuration}s ease`,
            }}
          >
            <span
              className={
                isActive
                  ? "bg-gradient-to-r from-blue-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent"
                  : "text-slate-400"
              }
            >
              {word}
            </span>

            {isActive && (
              <motion.span
                layoutId="focus-border"
                className="absolute -inset-1 z-10 rounded-lg pointer-events-none border-2"
                style={{
                  borderColor: borderColor,
                  boxShadow: `0 0 20px ${glowColor}`,
                }}
                transition={{
                  type: "spring",
                  stiffness: 300,
                  damping: 30,
                }}
              />
            )}
          </span>
        );
      })}
    </div>
  );
}
