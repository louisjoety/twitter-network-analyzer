import { useCallback, useEffect, useState, type FormEvent } from "react"
import { ArrowDownLeft, ArrowUpRight, ChevronLeft, ChevronRight, Search, Users, Workflow } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ThemeToggle } from "@/components/ThemeToggle"

type User = { user_id: string; followers: number; followees: number }
type Health = {
  mode: string; users: number; unique_edges: number; duplicate_edges_removed?: number;
}
type Page = { items: User[]; offset: number; limit: number; total: number }
type RequiredUser = { id: string; user?: User; error?: string }
const requiredIds = ["214328887", "107830991"]
const pageSize = 25
const number = (value: number) => new Intl.NumberFormat("en-SG").format(value)

async function api<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal })
  if (!response.ok) {
    let message = `Request failed (${response.status}).`
    try {
      const body = await response.json()
      if (typeof body.detail === "string") message = body.detail
    } catch { /* Preserve the HTTP error if the response is not JSON. */ }
    throw new Error(message)
  }
  return response.json()
}

function ErrorMessage({ children }: { children: string }) {
  return <Alert variant="destructive" role="alert"><AlertDescription>{children}</AlertDescription></Alert>
}

function UserCard({ id, user, error }: RequiredUser) {
  return <Card role="group" aria-label={`Statistics for user ${id}`} className="border-border shadow-none">
    <CardHeader className="pb-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-medium tracking-widest text-muted-foreground">USER ID</span>
        <Users className="size-4 text-muted-foreground" aria-hidden="true" />
      </div>
      <CardTitle className="font-mono text-2xl tracking-tight">{id}</CardTitle>
    </CardHeader>
    <CardContent className="space-y-3">
      {user ? <>
        <p className="flex flex-wrap items-baseline gap-x-1.5 text-sm text-muted-foreground">
          {id} has <strong className="text-xl font-semibold tabular-nums text-foreground">{number(user.followers)}</strong> followers
        </p>
        <p className="flex flex-wrap items-baseline gap-x-1.5 text-sm text-muted-foreground">
          {id} has <strong className="text-xl font-semibold tabular-nums text-foreground">{number(user.followees)}</strong> followees
        </p>
      </> : error ? <p className="text-sm text-muted-foreground" role="status">{error}</p>
        : <div className="space-y-3"><Skeleton className="h-6 w-3/4" /><Skeleton className="h-6 w-2/3" /></div>}
    </CardContent>
  </Card>
}

export default function TwitterApp() {
  const [health, setHealth] = useState<Health | null>(null)
  const [initialError, setInitialError] = useState("")
  const [required, setRequired] = useState<RequiredUser[]>(requiredIds.map((id) => ({ id })))
  const [page, setPage] = useState<Page | null>(null)
  const [pageLoading, setPageLoading] = useState(true)
  const [pageError, setPageError] = useState("")
  const [query, setQuery] = useState("")
  const [searchUser, setSearchUser] = useState<User | null>(null)
  const [searchError, setSearchError] = useState("")
  const [searching, setSearching] = useState(false)

  const loadPage = useCallback(async (offset: number, signal?: AbortSignal) => {
    setPageLoading(true)
    setPageError("")
    try {
      const result = await api<Page>(`/api/users?offset=${offset}&limit=${pageSize}`, signal)
      if (!signal?.aborted) setPage(result)
    } catch (error) {
      if (!signal?.aborted) setPageError((error as Error).message)
    } finally {
      if (!signal?.aborted) setPageLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const { signal } = controller
    api<Health>("/api/health", signal).then((result) => {
      if (!signal.aborted) setHealth(result)
    }).catch((error: Error) => { if (!signal.aborted) setInitialError(error.message) })
    Promise.all(requiredIds.map(async (id) => {
      try { return { id, user: await api<User>(`/api/users/${id}`, signal) } }
      catch (error) { return { id, error: (error as Error).message } }
    })).then((result) => { if (!signal.aborted) setRequired(result) })
    api<Page>(`/api/users?offset=0&limit=${pageSize}`, signal).then((result) => {
      if (!signal.aborted) setPage(result)
    }).catch((error: Error) => {
      if (!signal.aborted) setPageError(error.message)
    }).finally(() => { if (!signal.aborted) setPageLoading(false) })
    return () => controller.abort()
  }, [])

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const id = query.trim()
    setSearchUser(null)
    setSearchError("")
    if (!/^[0-9]+$/.test(id)) { setSearchError("Enter a numeric user ID."); return }
    setSearching(true)
    try { setSearchUser(await api<User>(`/api/users/${encodeURIComponent(id)}`)) }
    catch (error) { setSearchError((error as Error).message) }
    finally { setSearching(false) }
  }

  const isDemo = health?.mode === "demo"
  const offset = page?.offset ?? 0
  const total = page?.total ?? 0

  return <div className="min-h-screen bg-background text-foreground">
    <header className="border-b border-border bg-card">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 flex-wrap px-5 py-5 sm:px-8">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary p-2.5 text-primary-foreground"><Workflow className="size-5" aria-hidden="true" /></div>
          <div className="min-w-0"><p className="break-words text-sm font-semibold">twitter-network-analyzer</p><p className="text-xs text-muted-foreground">Explore your network</p></div>
        </div>
        <ThemeToggle />
      </div>
    </header>

    <main className="mx-auto max-w-6xl space-y-8 px-5 py-9 sm:px-8 sm:py-11">
      <section className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[.18em] text-primary">NETWORK OVERVIEW</p>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Every connection, counted.</h1>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">Explore follower and followee counts across the Twitter dataset. Each unique directed relationship counts once.</p>
      </section>

      {initialError && <ErrorMessage>{`Cannot connect to the backend: ${initialError}`}</ErrorMessage>}
      {isDemo && <Alert className="border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-200"><AlertDescription>Sample preview only: five test users (100–500). These are not the results of your uploaded Twitter dataset.</AlertDescription></Alert>}

      <section className="grid gap-4 sm:grid-cols-3" aria-label="Dataset summary">
        {[
          { label: "Users", value: health?.users, icon: Users },
          { label: "Unique relationships", value: health?.unique_edges, icon: ArrowUpRight },
          { label: "Duplicates removed", value: health?.duplicate_edges_removed, icon: ArrowDownLeft },
        ].map(({ label, value, icon: Icon }) => <Card key={label} className="border-border shadow-none">
          <CardContent className="flex items-start justify-between gap-4 p-5">
            <div><p className="mb-2 text-xs font-medium text-muted-foreground">{label}</p>{health ? <p className="text-3xl font-semibold tracking-tight tabular-nums">{value === undefined ? "—" : number(value)}</p> : <Skeleton className="h-9 w-24" />}</div>
            <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
          </CardContent>
        </Card>)}
      </section>

      <section className="space-y-4" aria-labelledby="required-heading">
        <div><h2 id="required-heading" className="text-lg font-semibold tracking-tight">Featured users</h2><p className="mt-1 text-sm text-muted-foreground">Follower and followee counts for two selected users.</p></div>
        <div className="grid gap-4 md:grid-cols-2">{required.map((user) => <UserCard key={user.id} {...user} />)}</div>
      </section>

      <Card className="border-border shadow-none">
        <CardHeader><CardTitle className="text-lg">Find a user</CardTitle><CardDescription>Look up any user in the dataset.</CardDescription></CardHeader>
        <CardContent className="space-y-5">
          <form onSubmit={search} className="flex max-w-xl gap-3">
            <label className="sr-only" htmlFor="user-id">User ID</label>
            <Input id="user-id" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Enter a user ID" inputMode="numeric" required className="bg-card" />
            <Button type="submit" disabled={searching} className="gap-2"><Search className="size-4" aria-hidden="true" />{searching ? "Searching..." : "Search"}</Button>
          </form>
          <div aria-live="polite">{searchError && <ErrorMessage>{searchError}</ErrorMessage>}{searchUser && <UserCard id={searchUser.user_id} user={searchUser} />}</div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden border-border shadow-none">
        <CardHeader><div className="flex flex-wrap items-center justify-between gap-3"><CardTitle className="text-lg">All users</CardTitle><Badge variant="secondary" className="font-normal">{number(total)} users</Badge></div><CardDescription>Followers follow this user. Followees are people this user follows.</CardDescription></CardHeader>
        <CardContent className="px-0 pb-0">
          {pageError && <div className="px-6 pb-4"><ErrorMessage>{pageError}</ErrorMessage></div>}
          <Table>
            <TableHeader><TableRow className="bg-muted/50"><TableHead className="pl-6">User ID</TableHead><TableHead className="text-right">Followers</TableHead><TableHead className="pr-6 text-right">Followees</TableHead></TableRow></TableHeader>
            <TableBody>
              {pageLoading && !page ? Array.from({ length: 5 }, (_, index) => <TableRow key={index}><TableCell className="pl-6"><Skeleton className="h-4 w-24" /></TableCell><TableCell><Skeleton className="ml-auto h-4 w-12" /></TableCell><TableCell className="pr-6"><Skeleton className="ml-auto h-4 w-12" /></TableCell></TableRow>)
                : page?.items.map((user) => <TableRow key={user.user_id}><TableCell className="py-3.5 pl-6 font-mono text-sm">{user.user_id}</TableCell><TableCell className="text-right tabular-nums">{number(user.followers)}</TableCell><TableCell className="pr-6 text-right tabular-nums">{number(user.followees)}</TableCell></TableRow>)}
            </TableBody>
          </Table>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t px-6 py-4">
            <p className="text-xs text-muted-foreground" aria-live="polite">{pageLoading ? "Loading users..." : total ? `${number(offset + 1)}–${number(offset + (page?.items.length ?? 0))} of ${number(total)} users` : "No users loaded"}</p>
            <div className="flex gap-2"><Button variant="outline" size="sm" disabled={pageLoading || offset === 0} onClick={() => void loadPage(Math.max(0, offset - pageSize))}><ChevronLeft className="size-4" />Previous</Button><Button variant="outline" size="sm" disabled={pageLoading || offset + (page?.items.length ?? 0) >= total} onClick={() => void loadPage(offset + pageSize)}>Next<ChevronRight className="size-4" /></Button></div>
          </div>
        </CardContent>
      </Card>
      <footer className="pb-2 text-center text-xs text-muted-foreground">Directed relationships · Duplicate pairs removed · Zero counts preserved</footer>
    </main>
  </div>
}
