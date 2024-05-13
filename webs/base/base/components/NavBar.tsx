"use client";

import React from "react";

const NavBar = () => {
    return (
        <div className="bg-neutral-600 flex items-center justify-between h-10 px-4">
            <nav className="flex flex-grow justify-evenly">
                <a href="#" className="text-white hover:text-gray-300">Home</a>
                <a href="#" className="text-white hover:text-gray-300">Shop</a>
                <a href="#" className="text-white hover:text-gray-300">About</a>
                <a href="#" className="text-white hover:text-gray-300">Services</a>
                <a href="#" className="text-white hover:text-gray-300">Contact</a>
            </nav>
        </div>
    );
}

export default NavBar;


