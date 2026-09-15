import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ДагГАУ — RAG-ассистент",
  description: "Вопросы и ответы по документам университета",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>
        <div className="min-h-screen bg-background text-foreground">
          {children}
        </div>
      </body>
    </html>
  );
}
