import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { CartProvider } from "../../components/cartContext";
import { TAB_NAME } from "../../constants/tab_name";
import { Footer, Header } from "../../components";

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
    <CartProvider>
      <html lang="en">
        <head>
          <link rel="icon" href="/favicon.ico" />
        </head>
        <body>
          <Header />
          <main>{children}</main>
          <Footer />
        </body>
      </html>
    </CartProvider>
  );
}