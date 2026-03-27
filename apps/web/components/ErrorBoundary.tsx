"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

interface ErrorBoundaryProps {
    children: ReactNode;
    fallback?: ReactNode | ((error: Error, resetErrorBoundary: () => void) => ReactNode);
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        console.error("[ErrorBoundary] Caught error:", error);
        console.error("[ErrorBoundary] Component stack:", errorInfo.componentStack);
    }

    resetErrorBoundary = (): void => {
        this.setState({ hasError: false, error: null });
    };

    render(): ReactNode {
        if (this.state.hasError && this.state.error) {
            // If a custom fallback is provided, use it
            if (this.props.fallback) {
                if (typeof this.props.fallback === "function") {
                    return this.props.fallback(this.state.error, this.resetErrorBoundary);
                }
                return this.props.fallback;
            }

            // Default error UI
            return (
                <div className="p-8 max-w-2xl mx-auto">
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Something went wrong</AlertTitle>
                        <AlertDescription>
                            {this.state.error.message || "An unexpected error occurred."}
                        </AlertDescription>
                    </Alert>
                    <div className="mt-4">
                        <Button onClick={this.resetErrorBoundary}>Try Again</Button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
