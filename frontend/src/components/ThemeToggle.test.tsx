import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { ThemeToggle } from "./ThemeToggle"

describe("Theme selection", () => {
  it("FE-11 switches themes and stores the user's choice", async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)
    await user.click(screen.getByRole("button", { name: "Switch to dark mode" }))
    expect(document.documentElement).toHaveClass("dark")
    expect(localStorage.getItem("twitter-stats-theme")).toBe("dark")
    await user.click(screen.getByRole("button", { name: "Switch to light mode" }))
    expect(document.documentElement).not.toHaveClass("dark")
    expect(localStorage.getItem("twitter-stats-theme")).toBe("light")
  })

  it("FE-12 can be activated using the keyboard", async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)
    await user.tab()
    await user.keyboard("{Enter}")
    expect(document.documentElement).toHaveClass("dark")
  })

  it("FE-13 still toggles when browser storage is blocked", async () => {
    const user = userEvent.setup()
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Storage blocked") })
    render(<ThemeToggle />)
    await user.click(screen.getByRole("button", { name: "Switch to dark mode" }))
    expect(screen.getByRole("button", { name: "Switch to light mode" })).toBeInTheDocument()
  })
})
