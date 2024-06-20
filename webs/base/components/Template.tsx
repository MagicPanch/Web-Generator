import React from "react";

const Template = () => {{
    return (
        <section className="min-h-screen bg-gradient-to-b from-customColor-100 to-customColor-200 flex flex-col items-center p-8 w-full">
                    <div className="min-h-screen flex flex-col w-full bg-white rounded-lg shadow-lg p-6 text-left">
                <h1 className="text-3xl font-bold text-customColor-800 mb-4">
                    ¡Bienvenido a tu nueva página!
                </h1>
                <p className="text-lg text-gray-700 mb-6">
                    Para crear nuevas secciones comunícate con el agente en Telegram.
                </p>
            </div>
        </section>
    );
}};

export default Template;