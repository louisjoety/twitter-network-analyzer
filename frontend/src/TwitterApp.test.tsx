import { beforeEach, describe, expect, it, vi } from "vitest"
import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import TwitterApp from "./TwitterApp"

const required = {
  "214328887": { user_id: "214328887", followers: 180, followees: 214 },
  "107830991": { user_id: "107830991", followers: 180, followees: 157 },
}
const users = Array.from({ length: 30 }, (_, index) => ({ user_id: String(100 + index), followers: index, followees: index + 1 }))
let mode: string
let offline: boolean
let failHealth: boolean
let failNextPage: boolean
const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
  const url = new URL(String(input), "http://localhost")
  if (url.pathname === "/api/health") {
    if (failHealth) return reply({ detail: "Backend unavailable" }, 503)
    return reply({ mode, offline, users: 30, unique_edges: 42, duplicate_edges_removed: 12, region: "ap-southeast-2" })
  }
  if (url.pathname === "/api/users") {
    const offset = Number(url.searchParams.get("offset") ?? 0)
    if (offset > 0 && failNextPage) return reply({ detail: "Page unavailable" }, 503)
    return reply({ items: users.slice(offset, offset + 25), offset, limit: 25, total: users.length })
  }
  const id = url.pathname.split("/").at(-1) ?? ""
  if (id in required) return reply(required[id as keyof typeof required])
  if (id === "999") return reply({ user_id: id, followers: 4, followees: 3 })
  return reply({ detail: "User not found in this dataset." }, 404)
})

beforeEach(() => {
  mode = "emr"
  offline = failHealth = failNextPage = false
  fetchMock.mockClear()
  vi.stubGlobal("fetch", fetchMock)
})

describe("Dashboard", () => {
  it("FE-01 displays both required users with API-provided counts", async () => {
    render(<TwitterApp />)
    const first = screen.getByRole("group", { name: "Statistics for user 214328887" })
    const second = screen.getByRole("group", { name: "Statistics for user 107830991" })
    await waitFor(() => expect(first).toHaveTextContent("214328887 has 180 followers"))
    expect(first).toHaveTextContent("214328887 has 214 followees")
    await waitFor(() => expect(second).toHaveTextContent("107830991 has 157 followees"))
    expect(second).toHaveTextContent("107830991 has 180 followers")
    expect(fetchMock).toHaveBeenCalledWith("/api/users/214328887", expect.objectContaining({ signal: expect.any(AbortSignal) }))
  })

  it("FE-02 shows dataset totals from the backend", async () => {
    render(<TwitterApp />)
    const summary = screen.getByRole("region", { name: "Dataset summary" })
    expect(await within(summary).findByText("42", { exact: true })).toBeInTheDocument()
    expect(within(summary).getByText("12", { exact: true })).toBeInTheDocument()
  })

  it("FE-03 searches for a numeric user and renders returned counts", async () => {
    const user = userEvent.setup()
    render(<TwitterApp />)
    await user.type(screen.getByLabelText("User ID", { exact: true }), "999")
    await user.click(screen.getByRole("button", { name: "Search" }))
    const result = await screen.findByRole("group", { name: "Statistics for user 999" })
    expect(result).toHaveTextContent("999 has 4 followers")
    expect(result).toHaveTextContent("999 has 3 followees")
  })

  it("FE-04 rejects nonnumeric input without requesting that user", async () => {
    const user = userEvent.setup()
    render(<TwitterApp />)
    await user.type(screen.getByLabelText("User ID", { exact: true }), "abc")
    await user.click(screen.getByRole("button", { name: "Search" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("Enter a numeric user ID")
    expect(fetchMock.mock.calls.some(([path]) => String(path).includes("/api/users/abc"))).toBe(false)
  })

  it("FE-05 shows the backend's unknown-user error", async () => {
    const user = userEvent.setup()
    render(<TwitterApp />)
    await user.type(screen.getByLabelText("User ID", { exact: true }), "888")
    await user.click(screen.getByRole("button", { name: "Search" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("User not found in this dataset")
  })

  it("FE-06 navigates pages and disables navigation at boundaries", async () => {
    const user = userEvent.setup()
    render(<TwitterApp />)
    await screen.findByRole("cell", { name: "100" })
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled()
    await user.click(screen.getByRole("button", { name: "Next" }))
    await screen.findByRole("cell", { name: "125" })
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled()
    expect(screen.getByRole("button", { name: "Previous" })).toBeEnabled()
    await user.click(screen.getByRole("button", { name: "Previous" }))
    expect(await screen.findByRole("cell", { name: "100" })).toBeInTheDocument()
  })

  it("FE-07 preserves the existing page when loading another page fails", async () => {
    const user = userEvent.setup()
    failNextPage = true
    render(<TwitterApp />)
    await screen.findByRole("cell", { name: "100" })
    await user.click(screen.getByRole("button", { name: "Next" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("Page unavailable")
    expect(screen.getByRole("cell", { name: "100" })).toBeInTheDocument()
  })

  it("FE-08 reports a failed backend health request", async () => {
    failHealth = true
    render(<TwitterApp />)
    expect(await screen.findByRole("alert")).toHaveTextContent("Cannot connect to the backend: Backend unavailable")
  })

  it("FE-09 labels sample data so it cannot be confused with cloud results", async () => {
    mode = "demo"
    render(<TwitterApp />)
    expect(await screen.findByText(/Sample preview only: five test users/)).toBeInTheDocument()
    expect(screen.getByText(/These are not the results of your uploaded Twitter dataset/)).toBeInTheDocument()
  })

  it("FE-10 shows real results without cloud infrastructure details", async () => {
    offline = true
    render(<TwitterApp />)
    const summary = screen.getByRole("region", { name: "Dataset summary" })
    expect(await within(summary).findByText("42", { exact: true })).toBeInTheDocument()
    expect(screen.queryByText(/Saved cloud results|EMR Serverless|Sydney|Analysed/)).not.toBeInTheDocument()
  })
})
