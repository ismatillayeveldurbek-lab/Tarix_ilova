import { useEffect } from "react";
import { Clipboard, Home, Trophy, User } from "./components/Icons";
import { Logo } from "./components/Logo";
import { ToastHost } from "./components/ui";
import { AdminApp } from "./pages/admin/AdminApp";
import { ExamPage } from "./pages/Exam";
import { HomePage } from "./pages/Home";
import { HomeSkeleton } from "./components/Skeleton";
import { LessonPage } from "./pages/Lesson";
import { ProfilePage } from "./pages/Profile";
import { ProgressPage } from "./pages/Progress";
import { InvitePage } from "./pages/Invite";
import { RatingPage } from "./pages/Rating";
import { goBack, navigate, useRoute } from "./lib/router";
import { StoreProvider, useStore } from "./lib/store";
import { haptic, tg } from "./lib/telegram";

const TABS = [
  { path: "/", label: "Asosiy", icon: Home },
  { path: "/exam", label: "Imtihon", icon: Clipboard },
  { path: "/rating", label: "Reyting", icon: Trophy },
  { path: "/profile", label: "Profil", icon: User },
];

function BottomNav({ path }: { path: string }) {
  return (
    <nav className="bottom-nav"><div className="inner">
      {TABS.map(({ path: p, label, icon: Icon }) => (
        <button key={p} className={path === p ? "active" : ""} onClick={() => { haptic.select(); navigate(p, true); }}>
          <span className="nav-icon"><Icon size={26} /></span>{label}
        </button>
      ))}
    </div></nav>
  );
}

/** Telegram'ning "Orqaga" tugmasi */
function useBackButton(show: boolean) {
  useEffect(() => {
    const bb = tg?.BackButton;
    if (!bb || !tg?.initData) return;
    const onClick = () => goBack();
    if (show) { bb.show(); bb.onClick(onClick); } else bb.hide();
    return () => bb.offClick(onClick);
  }, [show]);
}

function UserApp() {
  const { path, params } = useRoute();
  const { home, error } = useStore();
  useBackButton(path !== "/");

  if (error && !home) {
    return (
      <div className="page empty" style={{ minHeight: "80vh", justifyContent: "center" }}>
        <Logo withName={false} />
        <h2>Ulanib bo'lmadi</h2>
        <p className="muted">{error}</p>
        <button className="btn" onClick={() => window.location.reload()}>Qayta urinish</button>
      </div>
    );
  }
  if (!home) return <HomeSkeleton />;

  if (path === "/lesson") {
    const mode = (params.get("mode") || "mixed") as "daily" | "review" | "mixed" | "period" | "topic";
    const id = params.get("id") ? Number(params.get("id")) : null;
    return <LessonPage key={`${mode}-${id}`} mode={mode} id={id} />;
  }
  const page = path === "/invite" ? <InvitePage /> : path === "/progress" ? <ProgressPage /> : path === "/exam" ? <ExamPage /> : path === "/rating" ? <RatingPage /> : path === "/profile" ? <ProfilePage /> : <HomePage />;
  return <>{page}<BottomNav path={TABS.some((x) => x.path === path) ? path : "/"} /></>;
}

export default function App() {
  const { path } = useRoute();
  const isAdmin = path.startsWith("/admin");
  return (
    <div className={isAdmin ? "" : "app"}>
      <StoreProvider enabled={!isAdmin}>
        {isAdmin ? <AdminApp /> : <UserApp />}
      </StoreProvider>
      <ToastHost />
    </div>
  );
}
