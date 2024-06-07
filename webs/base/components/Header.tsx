"use client";

import React from "react";
import logo from './logo.png';
import Image from "next/image";
import { SECTIONS } from "../constants/sections";

type HeaderProps = {
  currentSection: string;
  setSection: (section: string) => void;
};

const Header = ({ currentSection, setSection }: HeaderProps) => {
  return (
      <div className="bg-customColor-500 flex items-center h-20 px-4">
          <div className="relative h-full flex items-center">
              <Image
                  src={logo}
                  alt="Logo"
                  layout="fixed"
                  objectFit="contain"
                  width={100}
                  height={100}
                  style={{maxHeight: "100%", height: "auto", width: "auto"}}
              />
          </div>
          <nav className="flex flex-grow items-center ml-4">
              {SECTIONS.map((section) => (
                  <button
                      key={section.name}
                      className={`mx-2 px-4 py-2 rounded ${
                          currentSection === section.name ? 'bg-customColor-700 text-white font-bold' : 'hover:bg-customColor-600 text-white'
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

export default Header;