import React from "react";
import Link from "next/link";
import { NAVIGATION_LINKS } from "../constants/navbar";

// Define un tipo para los props de NavBar
type NavBarProps = {
  nombre: string;
  addMensaje: (mensaje: string) => void;
};

const NavBar = ({ nombre, addMensaje }: NavBarProps) => {
  const enviarMensaje = () => {
    addMensaje("childMensaje");
  };

  const secciones = [
    { nombre: "ecommerce", seccion: "SectionEcommerce" },
    { nombre: "inicio", seccion: "SectionInformativa" },
    { nombre: "ABM", seccion: "SectionABM" },
    { nombre: "ABM2", seccion: "SectionABM" }
  ];

  return (
    <div className="bg-neutral-600 flex items-center justify-between h-10 px-4">
      <nav className="flex flex-grow justify-evenly">
        {secciones.map(seccion => (
          <button key={seccion.nombre} onClick={() => addMensaje(seccion.seccion)}>
            {seccion.nombre}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default NavBar;
