"use client"
import Image from "next/image";
import { SearchBar, SectionECommerce, SectionInformativa, SectionABM } from "../../components";
import { useState } from "react";
import { NavBar } from "../../components";

// Define los posibles valores de mensaje
type ComponentName = "SectionECommerce" | "SectionInformativa" | "SectionABM";

// Mapea los nombres de los componentes a los componentes reales
const componentMap: Record<ComponentName, () => JSX.Element> = {
  SectionECommerce: SectionECommerce,
  SectionInformativa: SectionInformativa,
  SectionABM: SectionABM,
  // Agrega más componentes aquí según sea necesario
};

export default function Home() {
  // const SelectedComponent = SectionECommerce  //elige el component que se muestra
  const [nombre, setNombre] = useState("Mario");
  const [mensaje, setMensaje] = useState<ComponentName>("SectionECommerce");

  // Cambia la definición de addMensaje para aceptar un argumento de tipo string
  const addMensaje = (mensaje: string) => {
    console.log(mensaje);
    setMensaje(mensaje as ComponentName); // Convierte el string a ComponentName
  };

  // Selecciona el componente basado en el valor de `mensaje`
  const SelectedComponent = componentMap[mensaje] || SectionECommerce;

  return (
    <main className="h-full items-center justify-between p-24 w-full">
      <NavBar nombre={nombre} addMensaje={addMensaje} />
      {mensaje}
      <div>
        {SelectedComponent ? <SelectedComponent /> : <div>Componente no encontrado</div>}
      </div>
    </main>
  );
}
