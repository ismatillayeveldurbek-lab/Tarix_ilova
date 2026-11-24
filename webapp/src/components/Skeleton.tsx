/** Ma'lumot yuklanayotganda sahifa shaklidagi "skelet" */
export function HomeSkeleton() {
  return (
    <div className="page stack" aria-busy>
      <div className="skel" style={{ width: 90, height: 12 }} />
      <div className="skel" style={{ width: "70%", height: 30 }} />
      <div className="skel" style={{ height: 70 }} />
      <div className="skel" style={{ height: 120 }} />
      <div className="row"><div className="skel grow" style={{ height: 96 }} /><div className="skel grow" style={{ height: 96 }} /></div>
      <div className="skel" style={{ width: 140, height: 18, marginTop: 12 }} />
      <div className="skel" style={{ height: 200 }} />
    </div>
  );
}
