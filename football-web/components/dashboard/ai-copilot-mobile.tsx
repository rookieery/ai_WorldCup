"use client"

import { useState } from "react"
import { MessageCircle, Sparkles } from "lucide-react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"
import { AICopilotPanel } from "@/components/dashboard/ai-copilot-panel"
import { useTranslation } from "@/lib/i18n"
import { useAIChatStore } from "@/lib/store"

/**
 * Mobile AI Copilot — FAB entry + bottom-sheet drawer.
 *
 * Visible only below the `lg` breakpoint. On desktop the sidebar
 * (rendered separately in page.tsx) takes over.
 */
export function AICopilotMobile() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)

  // Show a subtle pulse on the FAB while the AI is streaming
  const isStreaming = useAIChatStore((s) => s.isStreaming)

  return (
    <>
      {/* FAB — fixed bottom-right, hidden on lg+ */}
      <button
        onClick={() => setOpen(true)}
        aria-label={t("ai.fabLabel")}
        className={`
          fixed bottom-20 right-5 z-40 lg:hidden
          flex items-center gap-2 px-4 py-3 rounded-2xl
          bg-gradient-to-r from-[#00F0FF]/20 to-[#FF00E5]/20
          border border-[#00F0FF]/30
          shadow-[0_0_24px_rgba(0,240,255,0.3)]
          hover:shadow-[0_0_36px_rgba(0,240,255,0.5)]
          transition-all duration-300
          active:scale-95
          ${isStreaming ? "animate-pulse" : ""}
        `}
      >
        <div className="relative">
          <MessageCircle className="h-5 w-5 text-[#00F0FF]" />
          {isStreaming && (
            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-[#CCFF00] animate-ping" />
          )}
        </div>
        <span className="text-sm font-medium text-foreground">
          {t("ai.fabLabel")}
        </span>
        <Sparkles className="h-4 w-4 text-[#CCFF00]" />
      </button>

      {/* Bottom Sheet Drawer */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent
          side="bottom"
          className="h-[88vh] rounded-t-2xl border-t border-glass-border bg-background p-0 gap-0 overflow-hidden"
        >
          {/* Accessible header — visually hidden but required by Radix */}
          <SheetHeader className="sr-only">
            <SheetTitle>{t("ai.sheetTitle")}</SheetTitle>
            <SheetDescription>{t("ai.sheetDescription")}</SheetDescription>
          </SheetHeader>

          {/* Full-height chat panel */}
          <div className="h-full">
            <AICopilotPanel />
          </div>
        </SheetContent>
      </Sheet>
    </>
  )
}
