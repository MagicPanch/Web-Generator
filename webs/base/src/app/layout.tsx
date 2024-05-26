import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Footer, Header, NavBar } from "../../components";
import { CartProvider } from "../../components/cartContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Ecommerce",
  description: "web base para webGenerator",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <CartProvider>
      <html lang="en">
        <body>
          <Header />
          {/*<NavBar />*/}
          <main>{children}</main>
          <Footer />
        </body>
      </html>
    </CartProvider>
  );
}
