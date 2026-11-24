/** Ma'lumot yuklanayotganda sahifa shaklidagi "skelet" */
export function HomeSkeleton() {
  return (
    <div className="page stack" aria-busy>
      <div className="row between"><div className="skel" style={{ width: 60, height: 26 }} /><div className="skel" style={{ width: 60, height: 26 }} /><div className="skel" style={{ width: 60, height: 26 }} /></div>
      <div className="row"><div className="skel" style={{ width: 88, height: 88, borderRadius: 24 }} /><div className="skel grow" style={{ height: 72 }} /></div>
      <div className="skel" style={{ height: 104 }} />
      <div className="row"><div className="skel grow" style={{ height: 116 }} /><div className="skel grow" style={{ height: 116 }} /></div>
      <div className="skel" style={{ height: 84, marginTop: 16 }} />
      <div className="skel" style={{ width: 78, height: 78, borderRadius: "50%", alignSelf: "center", marginTop: 20 }} />
      <div className="skel" style={{ width: 78, height: 78, borderRadius: "50%", alignSelf: "center", marginLeft: 100 }} />
    </div>
  );
}
