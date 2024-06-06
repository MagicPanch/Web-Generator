import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Footer, Header } from "../../components";
import { TAB_NAME } from "../../constants/tab_name";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: TAB_NAME,
  description: "web base para webGenerator",
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
      <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico"/>
      </head>
      <body>
        <Header/>
        <main>{children}</main>
        <Footer/>
      </body>
      </html>
  );
}