import dbconnect from "@/app/lib/db_function";
import producto from "@/app/models/producto";
import { NextResponse } from "next/server";

export async function GET() {
    await dbconnect();
    try{
        const Producto = await producto.find({ stock: { $gt: 0 } });
        return NextResponse.json(Producto);
    }
    catch(err:any){
        return NextResponse.json({error: err.message});
    }
}