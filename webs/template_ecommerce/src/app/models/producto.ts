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
    key: { type: Number, required: false }
}, {
    collection: Nombre_Esquema // Aquí se especifica el nombre de la colección de forma explícita
});

const Producto = mongoose.models[Nombre_Esquema] || mongoose.model<Producto>(Nombre_Esquema, productoSchema);
export default Producto;