import { useEffect, useRef } from "react";
import { Dumbbell, Home, User } from "./components/Icons";
import { cx } from "./components/kit";
import { Logo } from "./components/Logo";
import { ToastHost } from "./components/ui";
import { AdminApp } from "./pages/admin/AdminApp";
import { ExamPage } from "./pages/Exam";
import { HomePage } from "./pages/Home";
import { HomeSkeleton } from "./components/Skeleton";
import { CardsPage } from "./pages/Cards";
import { LessonPage } from "./pages/Lesson";
import { OldinPage } from "./pages/Oldin";
import { MashqPage } from "./pages/Mashq";
import { ProfilePage } from "./pages/Profile";
import { ProgressPage } from "./pages/Progress";
import { InvitePage } from "./pages/Invite";
import { RatingPage } from "./pages/Rating";
import { goBack, navigate, useRoute } from "./lib/router";
import { StoreProvider, useStore } from "./lib/store";
import { haptic, tg } from "./lib/telegram";

const TABS = [
  { path: "/", label: "Bosh", icon: Home },
  { path: "/mashq", label: "Mashq", icon: Dumbbell },
  { path: "/profile", label: "Profil", icon: User },
];
/** Ichki sahifalar qaysi bo‘limga tegishli (menyuda shu belgilanadi) */
const OWNER: Record<string, string> = { "/exam": "/mashq", "/rating": "/profile", "/progress": "/profile", "/invite": "/profile" };

/** Pastda suzib turuvchi oq menyu (Mezon) */
function BottomNav({ active }: { active: string }) {
  return (
    <nav className="app-nav fixed inset-x-0 bottom-0 z-30 px-3 pb-[calc(var(--safe-bottom)+10px)]">
      <div className="mx-auto flex max-w-[520px] rounded-[26px] border border-line bg-surface/95 p-1.5 shadow-lift backdrop-blur-md">
        {TABS.map(({ path: p, label, icon: Icon }) => {
          const on = active === p;
          return (
            <button key={p} type="button" onClick={() => { haptic.select(); navigate(p, true); }}
              className={cx("flex flex-1 flex-col items-center gap-0.5 rounded-[20px] py-2 text-[11.5px] font-semibold transition duration-300 active:scale-95",
                on ? "bg-peri-soft text-peri" : "text-faint hover:text-muted")}>
              <span key={on ? "on" : "off"} className={on ? "animate-pop" : undefined}><Icon size={23} /></span>{label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

/** Telegram’ning "Orqaga" tugmasi */
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
  const { home, error, reload } = useStore();
  useBackButton(path !== "/");

  // Asosiy bo'limga qaytilganda (test, karta yoki o'yindan keyin) ma'lumotni yangilaymiz:
  // seriya, bugungi faollik va XP har doim aniq bo'lsin. Birinchi yuklashni StoreProvider qiladi.
  const firstLoad = useRef(true);
  useEffect(() => {
    if (firstLoad.current) { firstLoad.current = false; return; }
    if (TABS.some((t) => t.path === path)) void reload();
  }, [path, reload]);

  if (error && !home) {
    return (
      <div className="page empty" style={{ minHeight: "80vh", justifyContent: "center" }}>
        <Logo withName={false} />
        <h2>Ulanib bo‘lmadi</h2>
        <p className="muted">{error}</p>
        <button className="btn" onClick={() => window.location.reload()}>Qayta urinish</button>
      </div>
    );
  }
  if (!home) return <HomeSkeleton />;

  if (path === "/oldin") return <OldinPage />;
  if (path === "/cards") {
    return <CardsPage key={params.toString()} tur={params.get("tur") ?? ""} davr={params.get("davr") ?? ""} />;
  }
  if (path === "/lesson") {
    const mode = (params.get("mode") || "mixed") as "daily" | "review" | "mixed" | "period" | "topic";
    const id = params.get("id") ? Number(params.get("id")) : null;
    return <LessonPage key={`${mode}-${id}`} mode={mode} id={id} />;
  }
  const pages: Record<string, React.ReactNode> = {
    "/mashq": <MashqPage />, "/profile": <ProfilePage />, "/invite": <InvitePage />, "/progress": <ProgressPage />,
    "/exam": <ExamPage />, "/rating": <RatingPage />,
  };
  const active = TABS.some((x) => x.path === path) ? path : OWNER[path] ?? "/";
  // Sahifa almashganda yumshoq paydo bo‘lish (faqat shaffoflik: transform pastki "fixed" tugmalarni buzadi)
  return <><div key={path} className="animate-enter">{pages[path] ?? <HomePage />}</div><BottomNav active={active} /></>;
}

export default function App() {
  const { path } = useRoute();
  const isAdmin = path.startsWith("/admin");
  return (
    <div className={isAdmin ? "" : "min-h-screen bg-sky"}>
      <StoreProvider enabled={!isAdmin}>
        {isAdmin ? <AdminApp /> : <UserApp />}
      </StoreProvider>
      <ToastHost />
    </div>
  );
}
