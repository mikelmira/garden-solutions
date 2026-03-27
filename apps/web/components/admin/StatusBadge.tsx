import { Badge } from "@/components/ui/badge";

// Per STATUS_MODEL.md
type OrderStatus =
    | 'Draft'
    | 'Pending Approval'
    | 'Approved'
    | 'In Production'
    | 'Ready for Delivery'
    | 'Out for Delivery'
    | 'Partially Delivered'
    | 'Completed'
    | 'Cancelled';

export function StatusBadge({ status }: { status: string }) {
    // Map internal status to strict color variants
    // Using shadcn Badge variants mainly, but overriding with tailwind for specific colors

    const getStyle = (s: string) => {
        switch (s) {
            case 'Approved':
            case 'Completed':
                return "bg-green-100 text-green-800 hover:bg-green-200 border-green-200";
            case 'Pending Approval':
            case 'Draft':
                return "bg-yellow-100 text-yellow-800 hover:bg-yellow-200 border-yellow-200";
            case 'In Production':
            case 'Ready for Delivery':
            case 'Out for Delivery':
                return "bg-blue-100 text-blue-800 hover:bg-blue-200 border-blue-200";
            case 'Partially Delivered':
                return "bg-orange-100 text-orange-800 hover:bg-orange-200 border-orange-200";
            case 'Cancelled':
            case 'Failed':
                return "bg-red-100 text-red-800 hover:bg-red-200 border-red-200";
            default:
                return "bg-gray-100 text-gray-800 hover:bg-gray-200 border-gray-200";
        }
    };

    return (
        <Badge variant="outline" className={`whitespace-nowrap ${getStyle(status)}`}>
            {status}
        </Badge>
    );
}
