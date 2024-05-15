"use client";
import Image from "next/image";
import { NavBar, SearchBar, SectionECommerce, } from "../../components";
import SectionABM from "../../components/SectionABM";
import { useState } from "react";
import SectionInformativa from "../../components/SectionInformativa";

// Mapea los nombres de los componentes a los componentes reales
const componentMap = {
  SectionECommerce: SectionECommerce,
  SectionInformativa: SectionInformativa,
  SectionABM: SectionABM,
  // Agrega más componentes aquí según sea necesario
};

export default function Home() {
  //const SelectedComponent = SectionECommerce  //elige el component que se muestra
  const [nombre, setNombre]= useState("Mario")
  const [mensaje,setMensaje] = useState("")
  const addMensaje = (mensaje: any) => {
    console.log(mensaje)
    setMensaje(mensaje);
  }
   // Selecciona el componente basado en el valor de `mensaje`
   const SelectedComponent = componentMap[mensaje] || SectionECommerce;
  return (
    <main className="h-full  items-center justify-between p-24 w-full">
      
      <NavBar nombre={nombre} addMensaje={addMensaje}/>
      {mensaje}
      <div> 
       
      {SelectedComponent ? <SelectedComponent /> : <div>Componente no encontrado</div>}
      </div>
    
    </main>
  );
}
