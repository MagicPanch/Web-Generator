import mongoose, { Document,Schema } from 'mongoose';
import {Nombre_Esquema} from "../../../constants/collection"

export interface producto extends Document {
    name: string;
    desc: string;
    price: Number;
    multimedia: string;
    stock: Number;
}

const productoSchema: Schema = new mongoose.Schema({
    name: { type: String, required: true },
    stock: { type: Number, required: true },
    price: { type: Number, required: true },
    multimedia: { type: String, required: true },
    desc: { type: String, required: true }
});


const producto =mongoose.models.producto|| mongoose.model<producto>(Nombre_Esquema, productoSchema);
export default producto;