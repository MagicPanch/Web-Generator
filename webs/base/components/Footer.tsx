"use client";
import Image from "next/image";
import Link from "next/link";
import React from "react";
import { FOOTER_LINKS,  SOCIALS, } from "../constants/footer";
import { FOOTER_CONTACT_INFO } from "../constants/footer_contact_info";

const Footer = () => {
  return (
    <footer className="flex items-center justify-between pt-24 bg-customColor-900 px-36 py-14">
      <div className="padding-container max-container flex flex-col w-full gap-14">
        <div className="flex flex-col items-start justify-center gap-[10%] md:flex-row">
          <div className="flex flex-wrap gap-10 sm:justify-between md:flex-1">
            {FOOTER_LINKS.map((columns, index) => (
              <FooterColumn key={index} title={columns.title}>
                <ul className="regular-18 flex flex-col gap-4 text-gray-300">
                  {columns.links.map((link) => (
                    <Link href={link.href} key={link.label}>
                      {link.label}
                    </Link>
                  ))}
                </ul>
              </FooterColumn>
            ))}

            <div className="flex flex-col gap-5">
              <FooterColumn title={FOOTER_CONTACT_INFO.title}>
                {FOOTER_CONTACT_INFO.links.map((link) => (
                  <Link
                    href="/"
                    key={link.label}
                    className="flex gap-4 md:flex-col lg:flex-row"
                  >
                    <p className="whitespace-nowrap">{link.label}:</p>
                    <p className="medium-18 text-customColor-400">{link.value}</p>
                  </Link>
                ))}
              </FooterColumn>
            </div>
            <div className="flex flex-col gap-5">
              <FooterColumn title={SOCIALS.title}>
                <ul className="regular-18 flex gap-4 text-gray-300">
                  {SOCIALS.data.map((data) => (
                    <Link href={data.href} key={data.href}>
                      <Image
                        src={data.image}
                        alt="logo"
                        width={24}
                        height={24}
                      />
                    </Link>
                  ))}
                </ul>
              </FooterColumn>
            </div>
          </div>
        </div>
        <div className="border bg-gray-200" />
        <p className="regular-14 w-full text-center text-gray-300">
          {"2024 Design Label | All rights reserved"}
        </p>
      </div>
    </footer>
  );
};

type FooterColumnTypes = {
  title: string;
  children: React.ReactNode;
};

const FooterColumn = ({ title, children }: FooterColumnTypes) => {
  return (
    <div className="flex flex-col gap-5 text-white">
      <h4 className="bold-18 whitespace-nowrap">{title}</h4>
      {children}
    </div>
  );
};

export default Footer;
