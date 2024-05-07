
import json

def generarFooter(dataDicFooter):
    print("genero footer")
    text = f""""

    export const FOOTER_LINKS = [
  {
    title: "Navegación",
    links: [
      { label: "Services", href: "/#services" },
      { label: "Portfolio", href: "/#portfolio" },
      { label: "Contact", href: "/contact-us" },
      { label: "About us", href: "/about-us" },
    ],
  },
];

export const FOOTER_CONTACT_INFO = {
  title: "Contactanos",
  links: [
    { label: "Email", value: {dataDicFooter["email"]} },
    { label: "Ubicación", value: {dataDicFooter["ubicacion"]} },
  ],
};

export const SOCIALS = {
  title: "Social",
  data: [
    {
      image: "/facebook.svg",
      href: "https://www.facebook.com",
    },
    { image: "/instagram.svg", href: "https://www.instagram.com" },
    { image: "/x.svg", href: "https://twitter.com" },
  ],
};
    """

    with open(data["address"]+"\constants\footer.ts", "w") as file:
        file.write(text)



addres ="C:/Users/Agustin/Desktop/DesingLabelBranchSanti/Web-Generator/webs/base/base" #direccion donde se ubica la web react
dataFooter =  {"address":addres , "email":"contactDesignLabel@gmail.com", "ubicacion": "Pinto 399 Argentina, Tandil"} 
dataFooter = json.dumps(dataFooter)
print(dataFooter)
dataDicFooter = json.loads(dataFooter)
print(dataDicFooter["titulo"])

generarFooter(dataDicFooter)