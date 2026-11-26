import { useEffect, useState } from "react";
import { Bell, Book, Calendar, Chart, Clipboard, Flag, Home, Layers, Search, Upload } from "../../components/Icons";
import { Logo } from "../../components/Logo";
import { Loading } from "../../components/ui";
import { api, ApiError, setAdminToken } from "../../lib/api";
import { navigate, useRoute } from "../../lib/router";
import { getInitData } from "../../lib/telegram";
import { BroadcastPage } from "./Broadcast";
import { Dashboard } from "./Dashboard";
import { FactsPage } from "./Facts";
import { ExamConfigPage } from "./ExamConfig";
import { HistoryPage } from "./History";
import { ImportPage } from "./Import";
import { QuestionsPage } from "./Questions";
import { ReportsPage } from "./Reports";
import { StructurePage } from "./Structure";

const MENU = [
  { path: "/admin", label: "Statistika", icon: Chart },
  { path: "/admin/facts", label: "Faktlar bazasi", icon: Book },
  { path: "/admin/questions", label: "Test savollari", icon: Search },
  { path: "/admin/import", label: "Import (Excel/CSV)", icon: Upload },
  { path: "/admin/structure", label: "Davr va mavzular", icon: Layers },
  { path: "/admin/history", label: "Tarixda bugun", icon: Calendar },
  { path: "/admin/reports", label: "Xato xabarlari", icon: Flag },
  { path: "/admin/exam", label: "Imtihon formati", icon: Clipboard },
  { path: "/admin/broadcast", label: "E'lon yuborish", icon: Bell },
];

export function AdminApp() {
  const { path, params } = useRoute();
  const [state, setState] = useState<"loading" | "ok" | "denied">("loading");
  const [message, setMessage] = useState("");
  const [newReports, setNewReports] = useState(0);

  // Bot /panel bergan havoladagi tokenni saqlab, manzildan olib tashlaymiz
  useEffect(() => {
    const token = params.get("token");
    if (token) {
      setAdminToken(token);
      navigate(path, true);
    }
  }, [params, path]);

  useEffect(() => {
    if (params.get("token")) return;
    api<{ reports_new: number }>("/admin/stats")
      .then((s) => { setNewReports(s.reports_new); setState("ok"); })
      .catch((e: ApiError) => { setMessage(e.message); setState("denied"); });
  }, [params, path]);

  if (state === "loading") return <Loading />;
  if (state === "denied") {
    return (
      <div className="page empty" style={{ minHeight: "85vh", justifyContent: "center", maxWidth: 480, margin: "0 auto" }}>
        <Logo />
        <h2>Admin panelga kirish</h2>
        <p className="muted">{message}</p>
        <div className="card" style={{ textAlign: "left" }}>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            <li>Telegramda botingizni oching.</li>
            <li><b>/panel</b> buyrug'ini yuboring (sizning ID raqamingiz <code>ADMIN_IDS</code> da bo'lishi kerak).</li>
            <li>"Brauzerda ochish" tugmasini bosing.</li>
          </ol>
        </div>
        {getInitData() && <button className="btn white" onClick={() => navigate("/", true)}>Ilovaga qaytish</button>}
      </div>
    );
  }

  const page = (() => {
    switch (path) {
      case "/admin/facts": return <FactsPage />;
      case "/admin/questions": return <QuestionsPage />;
      case "/admin/import": return <ImportPage />;
      case "/admin/structure": return <StructurePage />;
      case "/admin/history": return <HistoryPage />;
      case "/admin/reports": return <ReportsPage onCount={setNewReports} />;
      case "/admin/exam": return <ExamConfigPage />;
      case "/admin/broadcast": return <BroadcastPage />;
      default: return <Dashboard />;
    }
  })();

  return (
    <div className="admin-layout">
      <aside className="admin-side">
        <div className="brand"><Logo /><span className="chip" style={{ marginLeft: "auto" }}>Admin</span></div>
        {MENU.map(({ path: p, label, icon: Icon }) => (
          <button key={p} className={path === p ? "active" : ""} onClick={() => navigate(p)}>
            <Icon size={20} />{label}
            {p === "/admin/reports" && newReports > 0 && <span className="badge">{newReports}</span>}
          </button>
        ))}
        {getInitData() && (
          <button onClick={() => navigate("/", true)}><Home size={20} />Ilovaga qaytish</button>
        )}
      </aside>
      <main className="admin-main">{page}</main>
    </div>
  );
}
