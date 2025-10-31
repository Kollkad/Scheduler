// Layout.tsx
import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="h-screen" style={{ backgroundColor: '#FAFAFA' }}>
      <Sidebar />
      <Header />
      <main className="ml-80 pt-16 h-screen overflow-auto" style={{ paddingLeft: '24px' }}>
        {children}
      </main>
    </div>
  );
}