import Image from "next/image";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <Image
        src="/pc.jpeg"
        alt="pc"
        width={320}
        height={320}
        className="inline-block cursor-pointer"
      />
      <Image
        src="https://img.global.news.samsung.com/mx/wp-content/uploads/2019/01/Notebook-9-Pro-3.jpg"
        alt="Descripción de la imagen"
        width={320}
        height={320}
        className="inline-block cursor-pointer"
      />
    </main>
  );
}
