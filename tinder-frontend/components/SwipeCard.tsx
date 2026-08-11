"use client";

import {
  forwardRef,
  useImperativeHandle,
  useRef,
} from "react";
import {
  motion,
  useMotionValue,
  useTransform,
  useAnimation,
  useReducedMotion,
} from "framer-motion";
import type { Creation } from "@/lib/types";
import CreationMedia from "./CreationMedia";
import Tag from "./Tag";

export interface SwipeCardHandle {
  swipe: (direction: "like" | "pass") => void;
}

interface SwipeCardProps {
  creation: Creation;
  onSwiped: (direction: "like" | "pass") => void;
}

const SWIPE_THRESHOLD = 120;

// Небольшой случайный наклон карточки, стабильный для конкретного творения
// (чтобы при перерендере не "дёргался"), имитирует ручную приколку на доску.
function tiltFor(id: string): number {
  let hash = 0;
  for (const ch of id) hash = (hash * 31 + ch.charCodeAt(0)) % 1000;
  return (hash / 1000) * 4 - 2; // от -2 до 2 градусов
}

const SwipeCard = forwardRef<SwipeCardHandle, SwipeCardProps>(
  ({ creation, onSwiped }, ref) => {
    const x = useMotionValue(0);
    const controls = useAnimation();
    const prefersReducedMotion = useReducedMotion();
    const baseTilt = useRef(tiltFor(creation.id)).current;

    const rotate = useTransform(x, [-300, 0, 300], [-18, baseTilt, 18]);
    const likeOpacity = useTransform(x, [20, 120], [0, 1]);
    const passOpacity = useTransform(x, [-120, -20], [1, 0]);

    const fly = async (direction: "like" | "pass") => {
      if (prefersReducedMotion) {
        onSwiped(direction);
        return;
      }
      await controls.start({
        x: direction === "like" ? 500 : -500,
        rotate: direction === "like" ? 24 : -24,
        opacity: 0,
        transition: { duration: 0.35, ease: "easeIn" },
      });
      onSwiped(direction);
    };

    useImperativeHandle(ref, () => ({
      swipe: (direction) => fly(direction),
    }));

    return (
      <div className="relative flex justify-center">
        <motion.div
          drag={prefersReducedMotion ? false : "x"}
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={0.7}
          style={{ x, rotate: prefersReducedMotion ? 0 : rotate }}
          animate={controls}
          onDragEnd={(_, info) => {
            if (info.offset.x > SWIPE_THRESHOLD) {
              fly("like");
            } else if (info.offset.x < -SWIPE_THRESHOLD) {
              fly("pass");
            } else {
              controls.start({ x: 0, transition: { type: "spring", stiffness: 300, damping: 26 } });
            }
          }}
          className="pinned-card w-full max-w-md cursor-grab overflow-hidden active:cursor-grabbing"
          role="group"
          aria-label={creation.title ?? "Творение без названия"}
        >
          <div className="pin-dot" aria-hidden="true" />

          {!prefersReducedMotion && (
            <>
              <motion.span
                style={{ opacity: likeOpacity }}
                className="absolute right-4 top-4 z-10 rotate-6 rounded border-2 border-coral px-2 py-1 font-mono text-xs font-bold uppercase tracking-wider text-coral"
              >
                нравится
              </motion.span>
              <motion.span
                style={{ opacity: passOpacity }}
                className="absolute left-4 top-4 z-10 -rotate-6 rounded border-2 border-slate px-2 py-1 font-mono text-xs font-bold uppercase tracking-wider text-slate"
              >
                мимо
              </motion.span>
            </>
          )}

          <CreationMedia creation={creation} />

          <div className="space-y-2 p-5">
            <div className="flex items-start justify-between gap-3">
              <h2 className="font-display text-lg font-semibold leading-snug text-ink">
                {creation.title || "Без названия"}
              </h2>
              {creation.category && <Tag label={creation.category} />}
            </div>
            {creation.media_type !== "text" && creation.description && (
              <p className="text-sm leading-relaxed text-ink/80">
                {creation.description}
              </p>
            )}
          </div>
        </motion.div>
      </div>
    );
  }
);

SwipeCard.displayName = "SwipeCard";
export default SwipeCard;
