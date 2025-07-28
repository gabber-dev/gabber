/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import React, { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class FlowErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Flow Error Boundary caught an error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex items-center justify-center h-full bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-center">
              <div className="text-red-600 text-xl mb-2">⚠️</div>
              <h3 className="text-lg font-semibold text-red-800 mb-2">
                Flow Error
              </h3>
              <p className="text-red-600 mb-4">
                Something went wrong with the flow diagram.
              </p>
              <button
                className="btn btn-primary"
                onClick={() =>
                  this.setState({ hasError: false, error: undefined })
                }
              >
                Try Again
              </button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
