import React from "react";
import { SECTIONS } from "../constants/sections";

type NavBarProps = {
  currentSection: string;
  setSection: (section: string) => void;
};

const NavBar = ({ currentSection, setSection }: NavBarProps) => {
  return (
    <div className="bg-neutral-600 flex items-center justify-between h-10 px-4">
      <nav className="flex flex-grow justify-evenly">
        {SECTIONS.map((section) => (
          <button
            key={section.name}
            className={`${
              currentSection === section.name ? "font-bold" : ""
            }`}
            onClick={() => setSection(section.name)}
          >
            {section.name.replace("Section", "")}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default NavBar;