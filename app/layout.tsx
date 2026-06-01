import type { Metadata, Viewport } from "next";
import { Heebo } from "next/font/google";
import "./globals.css";

// Branded Hebrew + Latin webfont, self-hosted by next/font (no layout shift).
const heebo = Heebo({
  subsets: ["hebrew", "latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Israelytics",
  description: "Visualize data about Israeli cities on a map, over time.",
};

// Drives the browser chrome color in each color scheme.
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f3ef" },
    { media: "(prefers-color-scheme: dark)", color: "#16161a" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

// Apply the persisted theme before first paint so there's no light/dark flash.
// Rendered as the first node in <body> (a raw <head> <script> isn't reliably
// executed under the App Router) so it runs synchronously during HTML parse.
const themeInit = `(function(){try{var t=localStorage.getItem('israelytics-theme');if(t==='dark'||t==='light'){document.documentElement.dataset.theme=t;}}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" className={heebo.variable}>
      <body>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
        {children}
      </body>
    </html>
  );
}
