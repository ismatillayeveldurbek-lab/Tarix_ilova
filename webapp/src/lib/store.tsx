// Ilova bo'ylab umumiy ma'lumot: foydalanuvchi, statistika va alifbo.
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";
import { tr, type Alphabet } from "./translit";
import type { Home } from "./types";

type Store = {
  home: Home | null;
  error: string | null;
  alphabet: Alphabet;
  reload: () => Promise<void>;
  setHome: (h: Home) => void;
  /** Lotinda yozilgan matnni foydalanuvchi alifbosiga o'giradi */
  t: (text: string) => string;
};

const Ctx = createContext<Store | null>(null);

export function StoreProvider({ children, enabled }: { children: ReactNode; enabled: boolean }) {
  const [home, setHome] = useState<Home | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setHome(await api<Home>("/home"));
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (enabled) void reload();
  }, [enabled, reload]);

  const alphabet: Alphabet = home?.user.alphabet ?? "latn";
  const t = useCallback((text: string) => tr(text, alphabet), [alphabet]);

  return <Ctx.Provider value={{ home, error, alphabet, reload, setHome, t }}>{children}</Ctx.Provider>;
}

export function useStore(): Store {
  const s = useContext(Ctx);
  if (!s) throw new Error("StoreProvider yo'q");
  return s;
}
