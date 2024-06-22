import mongoose, { Document, Schema } from 'mongoose';
import { Nombre_Esquema } from "../../../constants/collection";

export interface Producto extends Document {
    name: string;
    desc: string;
    price: number;
    multimedia: string;
    stock: number;
    key: number;
}

const productoSchema: Schema = new mongoose.Schema({
    name: { type: String, required: true },
    stock: { type: Number, required: true },
    price: { type: Number, required: true },
    multimedia: { type: String, required: true },
    desc: { type: String, required: true },
    key: { type: Number, required: true }
}, {
    collection: Nombre_Esquema
});

const Producto = mongoose.models[Nombre_Esquema] || mongoose.model<Producto>(Nombre_Esquema, productoSchema);
export default Producto;