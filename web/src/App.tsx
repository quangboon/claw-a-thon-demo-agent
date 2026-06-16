import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { Playground } from "@/routes/playground";
import { Termbase } from "@/routes/termbase";
import { Review } from "@/routes/review";
import { Corrections } from "@/routes/corrections";
import { Dashboard } from "@/routes/dashboard";
import { ProfileAdmin } from "@/routes/admin";

export default function App() {
  return (
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
  );
}
