import { useState } from "react"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"))
  const label = dark ? "Switch to light mode" : "Switch to dark mode"

  function toggle() {
    const next = !dark
    document.documentElement.classList.toggle("dark", next)
    setDark(next)
    try { localStorage.setItem("twitter-stats-theme", next ? "dark" : "light") }
    catch { /* The toggle still works when browser storage is unavailable. */ }
  }

  return <Button variant="outline" size="icon" onClick={toggle} aria-label={label} title={label}>
    {dark ? <Sun className="size-4" aria-hidden="true" /> : <Moon className="size-4" aria-hidden="true" />}
  </Button>
}
