"use client";
import React from "react";
import Link from "next/link";
import { NAVIGATION_LINKS } from "../constants/navbar";

const NavBar = ({ nombre,addMensaje }) => {
  const enviarMensaje= () => {
    addMensaje("childMensaje")
  }
  const secciones = [{"nombre":"ecommerce","seccion":"SectionEcommerce"},{"nombre":"inicio","seccion":"SectionInformativa"},{"nombre":"ABM","seccion":"SectionABM"},,{"nombre":"ABM2","seccion":"SectionABM"}]

  return (
    <div className="bg-neutral-600 flex items-center justify-between h-10 px-4">
      <nav className="flex flex-grow justify-evenly">
        {/* {NAVIGATION_LINKS &&
          NAVIGATION_LINKS.map((item, i) => (
            <Link href={item.href} key={i}>
              {item.label}
            </Link>
          ))
          <button onClick = {() => addMensaje("SectionEcommerce")}>Secommerce</button>
          <button onClick = {() => addMensaje("SectionABM")}>ABM</button>
          <button onClick = {() => addMensaje("SectionInformativa")}>Informativa</button>*/}
          {secciones.map(seccion => (
            <button onClick = {() => addMensaje(seccion["seccion"])}>{seccion["nombre"]}</button>
          ))}
          
        </nav>  
    </div>
  );
};

export default NavBar;
