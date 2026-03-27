import { format, parseISO } from "date-fns";

// Canonical Display Format: "14 Jan 2024"
export function formatDate(isoString: string): string {
    try {
        return format(parseISO(isoString), "d MMM yyyy");
    } catch (e) {
        return isoString;
    }
}

// Canonical DateTime: "14 Jan 2024, 14:30"
export function formatDateTime(isoString: string): string {
    try {
        return format(parseISO(isoString), "d MMM yyyy, HH:mm");
    } catch (e) {
        return isoString;
    }
}

// Currency Helper (Rands)
export function formatCurrency(amount: number): string {
    return new Intl.NumberFormat("en-ZA", {
        style: "currency",
        currency: "ZAR",
    }).format(amount);
}
