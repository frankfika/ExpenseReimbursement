import { Component, type ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 ring-1 ring-rose-500/20">
            <AlertTriangle size={28} />
          </div>
          <h2 className="text-base font-semibold text-surface-100">出错了</h2>
          <p className="max-w-sm text-xs text-surface-500">
            应用遇到了意外错误。您可以尝试刷新页面，或重启应用。
          </p>
          {this.state.error && (
            <pre className="max-w-md rounded-xl bg-surface-900/80 p-3 text-left text-[11px] text-surface-500 ring-1 ring-white/[0.06]">
              {this.state.error.toString()}
            </pre>
          )}
          <button
            className="btn-primary text-xs"
            onClick={this.handleReload}
          >
            <RotateCcw size={14} /> 刷新页面
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
