import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
    return (
        <div className="p-4 space-y-4">
            <Skeleton className="h-12 w-full rounded-lg" />
            <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-32 rounded-lg" />
                <Skeleton className="h-32 rounded-lg" />
            </div>
            <Skeleton className="h-64 w-full rounded-lg" />
        </div>
    );
}
