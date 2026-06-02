import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

const narkissTam = localFont({
  src: [
    { path: "./fonts/NarkissTam-Light.woff2",    weight: "300" },
    { path: "./fonts/NarkissTam-Regular.woff2",  weight: "400" },
    { path: "./fonts/NarkissTam-Medium.woff2",   weight: "500" },
    { path: "./fonts/NarkissTam-Semibold.woff2", weight: "600" },
    { path: "./fonts/NarkissTam-Bold.woff2",     weight: "700" },
    { path: "./fonts/NarkissTam-Heavy.woff2",    weight: "800" },
    { path: "./fonts/NarkissTam-Black.woff2",    weight: "900" },
  ],
  variable: "--font-sans",
  display: "swap",
});

const hadassah = localFont({
  src: [
    { path: "./fonts/Hadassah-Thin.woff2",    weight: "100" },
    { path: "./fonts/Hadassah-Light.woff2",   weight: "300" },
    { path: "./fonts/Hadassah-Regular.woff2", weight: "400" },
    { path: "./fonts/Hadassah-Medium.woff2",  weight: "500" },
    { path: "./fonts/Hadassah-Heavy.woff2",   weight: "700" },
    { path: "./fonts/Hadassah-Black.woff2",   weight: "900" },
  ],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ישראליטיקס",
  description: "נתונים על ערי ישראל על גבי מפה, לאורך זמן.",
};

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

const themeInit = `(function(){try{var t=localStorage.getItem('israelytics-theme');if(t==='dark'||t==='light'){document.documentElement.dataset.theme=t;}}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" className={`${narkissTam.variable} ${hadassah.variable}`}>
      <body>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
        {children}
      </body>
    </html>
  );
}
