// Oddiy "hash" router: manzil #/lesson?mode=daily ko'rinishida bo'ladi.
import { useEffect, useState } from "react";

export type Route = { path: string; params: URLSearchParams };

function parse(): Route {
  const raw = window.location.hash.replace(/^#/, "") || "/";
  const [path, query = ""] = raw.split("?");
  return { path: path || "/", params: new URLSearchParams(query) };
}

export function useRoute(): Route {
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const onChange = () => {
      setRoute(parse());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

export function navigate(to: string, replace = false): void {
  const hash = `#${to}`;
  if (replace) window.location.replace(hash);
  else window.location.hash = hash;
}

export function goBack(fallback = "/"): void {
  if (window.history.length > 1) window.history.back();
  else navigate(fallback, true);
}
