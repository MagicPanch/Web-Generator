import Image from "next/image";
import { SearchBar, SectionECommerce, } from "../../components";
import SectionABM from "../../components/SectionABM";

export default function Home() {
  const SelectedComponent = SectionECommerce  //elige el component que se muestra
  return (
    <main className="h-full  items-center justify-between p-24 w-full">
      

      <div> 
      {SelectedComponent ? <SelectedComponent /> : <div>Componente no encontrado</div>}
      </div>
    
    </main>
  );
}
