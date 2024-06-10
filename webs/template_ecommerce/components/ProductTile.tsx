import React, {useRef, useState} from "react";

interface CardProps {
  image: string;
  title: string;
  description: string;
  price: string;
  key: number;
  stock: number;
  onAddToCart: () => void;
}

const ProductTile = ({
  image,
  title,
  description,
  price,
  stock,
  onAddToCart,
}: CardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const descriptionRef = useRef<HTMLParagraphElement>(null);

  const toggleDescription = () => {
    setIsExpanded(!isExpanded);
  };

  const truncateDescription = (text: string, length: number) => {
    return text.length > length ? text.substring(0, length) + "..." : text;
  };

  const isTitleLong = () => {
    if (titleRef.current) {
      const lines = titleRef.current.clientHeight / parseFloat(getComputedStyle(titleRef.current).lineHeight);
      return lines > 1;
    }
    return false;
  };
  const isDescriptionLong = () => {
    if (descriptionRef.current) {
      const lines = descriptionRef.current.clientHeight / parseFloat(getComputedStyle(descriptionRef.current).lineHeight);
      if (isTitleLong()) {
        return lines >= 1;
      } else {
        return lines >= 2;
      }
    }
    return false;
  };

  return (
      <div
          className="bg-white rounded-lg overflow-hidden shadow-md p-4 m-4 max-w-xl h-150 transition-transform duration-300 transform hover:scale-105">
          <img src={image} alt="Product" className="w-full h-full object-cover"/>
          <h2  ref={titleRef} className="text-lg font-bold  mb-2 text-customColor-800 ">{title}</h2>
          <div className={`text-gray-600 flex-grow overflow-hidden relative ${isTitleLong() ? truncateDescription(description, 45) : truncateDescription(description, 90)}`}>
              <p ref={descriptionRef}>
                  {isExpanded ? description : truncateDescription(description, isTitleLong() ? 45 : 90)}
                  {isDescriptionLong() && (
                      <button
                          onClick={toggleDescription}
                          className="text-customColor-500 hover:underline ml-1"
                      >
                          {isExpanded ? "Leer menos" : "Leer más"}
                      </button>
                  )}
              </p>
          </div>
          <p className="text-customColor-800 mt-2">Stock disponible: {stock} unidades.</p>
          <div className="flex flex-col justify-between h-full">
              <div className="mt-4 flex items-center justify-between">
                  <span className="font-semibold text-xl text-customColor-800">${price}</span>
                  <button
                      onClick={onAddToCart}
                      className="bg-customColor-500 hover:bg-customColor-600 text-white px-3 py-2 rounded-md"
                  >
                      Agregar al carrito
                  </button>
              </div>
          </div>
      </div>
  );
};

export default ProductTile;
