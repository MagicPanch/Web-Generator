import dbconnect from "@/app/lib/db_function";
import Product from '../../models/producto';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
    await dbconnect();
    const { cart } = await request.json();
  
    try {
      const updatePromises = cart.map(async (cartItem: { item: { key: Number }, quantity: number }) => {
        const product = await Product.findOne({key: cartItem.item.key});
        if (product) {
          product.stock -= cartItem.quantity;
          await product.save();
        }
      });
  
      await Promise.all(updatePromises);
  
      return NextResponse.json({ message: 'Product quantities updated successfully' });
    } catch (error) {
      console.error('Error updating product quantities:', error);
      return NextResponse.json({ error: 'Error updating product quantities' }, { status: 500 });
    }
  }