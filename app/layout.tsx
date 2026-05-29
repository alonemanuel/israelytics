import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Israelytics",
  description: "Visualize data about Israeli cities on a map, over time.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he">
      <body>{children}</body>
    </html>
  );
}
