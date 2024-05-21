import React from "react";

// Define un tipo para los elementos
type Elemento = {
  id: string;
  nombre: string;
};

const SectionABM = () => {
  const elementos: Elemento[] = [
    { id: "n1", nombre: "juan" },
    { id: "n2", nombre: "Marcos" },
    { id: "n3", nombre: "Capitan Barbosa" }
  ];

  const columnas: (keyof Elemento)[] = ["id", "nombre"]; // selecciona qué columnas desea ver

  return (
    <section>
      <div className="max-w-screen bg-blue-300 p-4 h-full px-4">
        <h1>soy ABM</h1>
        <p>aca opciones para agregar columnas a mostrar o valores</p>
        <table className="bg-green-600 min-w-full border-collapse border border-gray-400">
          <thead>
            <tr>
              {columnas.map(columna => (
                <th key={columna} className="border border-gray-400 p-2">
                  {columna}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {elementos.map(elemento => (
              <tr key={elemento.id}>
                {columnas.map(columna => (
                  <td key={columna} className="border border-gray-400 p-2">
                    {elemento[columna]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default SectionABM;
