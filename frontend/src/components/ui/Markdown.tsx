"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function Markdown({ children }: { children: string }) {
  return (
    <div
      className={[
        "text-sm leading-relaxed",
        "[&>p]:my-1.5 first:[&>p]:mt-0 last:[&>p]:mb-0",
        "[&_strong]:font-bold [&_strong]:text-ink",
        "[&_ul]:my-1.5 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:my-1.5 [&_ol]:list-decimal [&_ol]:pl-5",
        "[&_li]:my-0.5",
        "[&_a]:font-medium [&_a]:text-accent [&_a]:underline",
        "[&_code]:rounded [&_code]:bg-surface-sunken [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-[0.85em]",
        "[&_h1]:mt-2 [&_h1]:text-base [&_h1]:font-bold [&_h2]:mt-2 [&_h2]:text-base [&_h2]:font-bold [&_h3]:font-bold",
      ].join(" ")}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // The assistant should never embed images; drop any that slip through
          // so a broken-image icon never appears in a reply.
          img: () => null,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
