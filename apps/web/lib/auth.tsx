"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiService } from "./api";

const TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

interface User {
    email: string;
    full_name: string;
    role: "admin" | "sales" | "manufacturing" | "delivery";
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    error: string | null;
    login: (accessToken: string, refreshToken?: string) => void;
    logout: () => void;
    refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    isLoading: true,
    error: null,
    login: () => { },
    logout: () => { },
    refreshSession: async () => { },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    const logout = useCallback(() => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        setUser(null);
        setError(null);
        router.push("/login");
    }, [router]);

    const fetchUser = useCallback(async () => {
        try {
            setError(null);
            const profile = await apiService.auth.me();
            setUser(profile as User);
        } catch (err: any) {
            if (err.response?.status === 401) {
                // Try refresh before logging out
                const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
                if (refreshToken) {
                    try {
                        const res = await apiService.auth.refresh(refreshToken);
                        localStorage.setItem(TOKEN_KEY, res.access_token);
                        if (res.refresh_token) {
                            localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token);
                        }
                        // Retry fetching user with new token
                        const profile = await apiService.auth.me();
                        setUser(profile as User);
                        return;
                    } catch {
                        // Refresh failed - logout
                    }
                }
                logout();
            } else {
                setError(err.message || "Failed to fetch session");
            }
        } finally {
            setIsLoading(false);
        }
    }, [logout]);

    const refreshSession = useCallback(async () => {
        const token = localStorage.getItem(TOKEN_KEY);
        if (token) {
            setIsLoading(true);
            await fetchUser();
        }
    }, [fetchUser]);

    useEffect(() => {
        const token = localStorage.getItem(TOKEN_KEY);
        if (token) {
            fetchUser();
        } else {
            setIsLoading(false);
        }
    }, [fetchUser]);

    const login = useCallback((accessToken: string, refreshToken?: string) => {
        localStorage.setItem(TOKEN_KEY, accessToken);
        if (refreshToken) {
            localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
        }
        fetchUser();
    }, [fetchUser]);

    return (
        <AuthContext.Provider value={{ user, isLoading, error, login, logout, refreshSession }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
