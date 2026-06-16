import { Outlet } from "react-router-dom";
import { LogOut } from "lucide-react";
import { Sidebar } from "./sidebar";
import { ProfileSelect } from "./profile-select";
import { Button } from "@/components/ui/button";
import { getAuthToken, logout } from "@/lib/api";

export function AppShell() {
  return (
    <div className="flex h-full">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 shrink-0 border-b border-line bg-surface flex items-center justify-between px-6">
          <h1 className="font-semibold">Nền tảng dịch thuật đa team · Termbase + QC</h1>
          <div className="flex items-center gap-3">
            <ProfileSelect />
            {getAuthToken() && (
              <Button size="sm" variant="ghost" onClick={logout} title="Đăng xuất">
                <LogOut size={16} />
              </Button>
            )}
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
