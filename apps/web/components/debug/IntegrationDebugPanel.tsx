"use client";

import { useAuth } from "@/lib/auth";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

export function IntegrationDebugPanel() {
    // Only render in development
    if (process.env.NODE_ENV === 'production') return null;

    const { user, error, refreshSession, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-4 right-4 z-50 bg-black text-white px-3 py-2 rounded-full text-xs font-mono shadow-lg opacity-50 hover:opacity-100 transition-opacity"
            >
                Debug
            </button>
        );
    }

    return (
        <div className="fixed bottom-4 right-4 z-50 w-80 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl text-zinc-100 font-mono text-xs overflow-hidden">
            <div className="flex justify-between items-center bg-zinc-800 px-3 py-2 border-b border-zinc-700">
                <span className="font-bold text-green-400">Integration Debug</span>
                <button onClick={() => setIsOpen(false)} className="text-zinc-400 hover:text-white">X</button>
            </div>
            <div className="p-3 space-y-3">
                <div className="space-y-1">
                    <div className="text-zinc-500 uppercase text-[10px] tracking-wider">API Config</div>
                    <div className="truncate text-blue-300" title={apiUrl}>{apiUrl}</div>
                </div>

                <div className="space-y-1">
                    <div className="text-zinc-500 uppercase text-[10px] tracking-wider">Auth State</div>
                    {user ? (
                        <div className="flex flex-col gap-1">
                            <div className="flex justify-between">
                                <span>Role:</span>
                                <span className={cn(
                                    "font-bold",
                                    user.role === 'admin' ? "text-purple-400" : "text-orange-400"
                                )}>{user.role}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>User:</span>
                                <span className="truncate max-w-[150px]">{user.email}</span>
                            </div>
                            <div className="flex justify-between text-[10px] text-zinc-500">
                                <span>Fetched:</span>
                                <span>—</span>
                            </div>
                        </div>
                    ) : (
                        <div className="text-zinc-500 italic">Not Authenticated</div>
                    )}
                </div>

                {error && (
                    <div className="bg-red-900/30 border border-red-900/50 p-2 rounded text-red-200">
                        <div className="font-bold mb-1">Last API Error</div>
                        <div>{error}</div>
                    </div>
                )}

                <div className="flex gap-2 pt-2 border-t border-zinc-800">
                    <button
                        onClick={() => refreshSession()}
                        className="flex-1 bg-zinc-800 hover:bg-zinc-700 py-1.5 rounded transition-colors"
                    >
                        Refetch Session
                    </button>
                    <button
                        onClick={logout}
                        className="flex-1 bg-red-900/20 hover:bg-red-900/40 text-red-200 py-1.5 rounded transition-colors"
                    >
                        Clear Session
                    </button>
                </div>
            </div>
        </div>
    );
}
