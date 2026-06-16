import { Outlet } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { ProfileSelect } from "./profile-select";

export function AppShell() {
  return (
    <div className="flex h-full">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 shrink-0 border-b border-line bg-surface flex items-center justify-between px-6">
          <h1 className="font-semibold">Nền tảng dịch thuật đa team · Termbase + QC</h1>
          <ProfileSelect />
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
