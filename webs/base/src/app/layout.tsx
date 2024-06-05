import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Footer, Header, NavBar } from "../../components";
import { CartProvider } from "../../components/cartContext";
import { TAB_NAME } from "../../constants/tab_name"

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: TAB_NAME,
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
