import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { Playground } from "@/routes/playground";
import { Termbase } from "@/routes/termbase";
import { Review } from "@/routes/review";
import { Corrections } from "@/routes/corrections";
import { Dashboard } from "@/routes/dashboard";
import { ProfileAdmin } from "@/routes/admin";
import { Login } from "@/routes/login";
import { api, getAuthToken } from "@/lib/api";
import { ProfileProvider } from "@/lib/profile-context";

export default function App() {
  const [token, setToken] = useState(getAuthToken());
  // Public endpoint — tells us whether the login gate is active server-side.
  const status = useQuery({ queryKey: ["auth-status"], queryFn: api.authStatus });

  if (status.isLoading) return null; // brief; avoids a login flash when auth is off
  const needLogin = status.data?.auth_required && !token;
  if (needLogin) return <Login onSuccess={() => setToken(getAuthToken())} />;

  return (
    <ProfileProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Playground />} />
            <Route path="termbase" element={<Termbase />} />
            <Route path="review" element={<Review />} />
            <Route path="corrections" element={<Corrections />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="admin" element={<ProfileAdmin />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ProfileProvider>
  );
}
