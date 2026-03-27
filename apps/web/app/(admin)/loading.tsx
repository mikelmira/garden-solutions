export default function Loading() {
    return (
        <div className="flex h-full w-full items-center justify-center p-8 text-muted-foreground">
            <div className="flex flex-col items-center gap-2">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                <p>Loading Admin Portal...</p>
            </div>
        </div>
    );
}
