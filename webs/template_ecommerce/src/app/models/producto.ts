import mongoose, { Document,Schema } from 'mongoose';
import {Nombre_Esquema} from "../../../constants/collection"

export interface producto extends Document {
    name: string;
    desc: string;
    price: Number;
    multimedia: string;
    stock: Number;
    key: Number;
}

const productoSchema: Schema = new mongoose.Schema({
    name: { type: String, required: true },
    stock: { type: Number, required: true },
    price: { type: Number, required: true },
    multimedia: { type: String, required: true },
    desc: { type: String, required: true },
    key:{type:Number, required: false}
});


const producto =mongoose.models[Nombre_Esquema]|| mongoose.model<producto>(Nombre_Esquema, productoSchema);
export default producto;