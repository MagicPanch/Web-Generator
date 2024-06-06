"use client";

import { useState } from "react";
import componentMap from "../../utils/componentMap";
import { SECTIONS } from "../../constants/sections";
import NavBar from "../../components/NavBar";

export default function Home() {
  const [currentSection, setCurrentSection] = useState(SECTIONS[0].name);

  const CurrentComponent = componentMap[currentSection];

  return (
    <div>
      <NavBar currentSection={currentSection} setSection={setCurrentSection} />
      <main className="h-full items-center justify-between p-24 w-full">
        <CurrentComponent />
      </main>
    </div>
  );
}
