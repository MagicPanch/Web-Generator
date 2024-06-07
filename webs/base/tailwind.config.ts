import { CUSTOM_COLORS } from "./constants/custom_tailwind_colors"

/** @type {import('tailwindcss').Config} */
    module.exports = {
        content: [
            "./pages/**/*.{js,ts,jsx,tsx,mdx}",
            "./components/**/*.{js,ts,jsx,tsx,mdx}",
            "./app/**/*.{js,ts,jsx,tsx,mdx}",
        ],
        theme: {
            extend: {
                fontFamily: {
                    body: ["Korolev Medium"],
                },
                colors: {
                    primary: {
                        400: "#CBEAF2",
                        500: "#66b7cb",
                        600: "#55a4b7",
                    },
                    customColor: CUSTOM_COLORS,
                    bgGray: "#E2E2E2",
                    bgBlack: "#1C1C1C",
                },
                backgroundSize: {
                    "16": "4rem",
                },
                screens: {
                    xs: "400px",
                    "3xl": "1680px",
                    "4xl": "2200px",
                },
                maxWidth: {
                    "10xl": "1512px",
                },
                borderRadius: {
                    "5xl": "40px",
                },
            },
        },
        plugins: []
    };