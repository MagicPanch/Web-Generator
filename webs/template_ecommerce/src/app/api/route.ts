import dbconnect from "@/app/lib/db_function";
import producto from "@/app/models/producto";
import { NextResponse } from "next/server";

export const dynamic = 'force-dynamic';
export async function GET(request: Request) {
    await dbconnect();
    try {
        const { searchParams } = new URL(request.url);
        const palabra = searchParams.get('search') || '';

        const productos = await producto.find({
            name: { $regex: new RegExp(palabra, 'i') }
        });
        return NextResponse.json(productos);
    } catch (err: any) {
        return NextResponse.json({ error: err.message });
    }
}