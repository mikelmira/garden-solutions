import { Client } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Props {
    client: Client;
    onSelect: (client: Client) => void;
    isSelected?: boolean;
}

export function ClientCard({ client, onSelect, isSelected }: Props) {
    return (
        <Card
            onClick={() => onSelect(client)}
            className={`cursor-pointer transition-colors hover:border-blue-300 ${isSelected ? "border-green-500 bg-green-50" : ""
                }`}
        >
            <CardHeader className="p-4 pb-2">
                <div className="flex justify-between items-start">
                    <CardTitle className="text-base font-bold text-gray-900">{client.name}</CardTitle>
                    {client.price_tier && (
                        <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-200">
                            {client.price_tier.name}
                        </Badge>
                    )}
                </div>
            </CardHeader>
            <CardContent className="p-4 pt-0">
                <p className="text-sm text-gray-500">{client.address}</p>
            </CardContent>
        </Card>
    );
}
