"use client";
import { useEffect, useState } from "react";

const LINE1 = "Know Every Permit";
const LINE2 = "Before You Open.";

export default function TypewriterHeadline() {
  const [text1, setText1] = useState("");
  const [text2, setText2] = useState("");
  const [done1, setDone1] = useState(false);

  useEffect(() => {
    let i = 0;
    const t1 = setInterval(() => {
      setText1(LINE1.slice(0, i + 1));
      i++;
      if (i >= LINE1.length) {
        clearInterval(t1);
        setDone1(true);
      }
    }, 45);
    return () => clearInterval(t1);
  }, []);

  useEffect(() => {
    if (!done1) return;
    let i = 0;
    const t2 = setInterval(() => {
      setText2(LINE2.slice(0, i + 1));
      i++;
      if (i >= LINE2.length) clearInterval(t2);
    }, 45);
    return () => clearInterval(t2);
  }, [done1]);

  return (
    <h1 className="display-heading text-4xl md:text-[3.25rem] text-[var(--paper)] mb-6 leading-tight min-h-[7rem]">
      {text1}
      {!done1 && <span className="animate-pulse text-[var(--emerald)]">█</span>}
      {done1 && (
        <>
          <br />
          <span className="text-[var(--emerald)]">
            {text2}
            {text2.length < LINE2.length && (
              <span className="animate-pulse">█</span>
            )}
          </span>
        </>
      )}
    </h1>
  );
}
