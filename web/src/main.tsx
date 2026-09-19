import React, { Component, type ErrorInfo, type ReactNode } from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import "./index.css"

type Props = { children: ReactNode }
type State = { error: Error | null }

class AppErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("The-Trader frontend runtime error", error, info)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <main className="min-h-screen bg-background px-6 py-16 text-foreground">
        <div className="mx-auto max-w-xl rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Application error</div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">The dashboard could not render.</h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            A frontend component failed during rendering. Refresh the page after checking the browser console.
          </p>
          <pre className="mt-4 overflow-auto rounded-md border border-border bg-muted p-3 text-xs text-muted-foreground">
            {this.state.error.message}
          </pre>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-5 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Reload dashboard
          </button>
        </div>
      </main>
    )
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>,
)
