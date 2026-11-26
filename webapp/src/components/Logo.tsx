/** Ilova logotipi: serif "T" va ostidagi oltin chiziq */
export function Logo({ withName = true }: { withName?: boolean }) {
  return (
    <span className="logo">
      <span className="logo-mark" aria-hidden>T</span>
      {withName && <span>Tarix</span>}
    </span>
  );
}
