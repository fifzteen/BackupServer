import { useState, useEffect } from "react";
import "./App.scss";
import { Status } from "@/types/status";
import { AppSection } from "@/components/AppSection.tsx";
import { AppButtonClear } from "@/components/AppButtonClear.tsx";

function App() {
  const [status, setStatus] = useState<Status>({
    error: [],
    finished: [],
    running: [],
    pending: [],
  });

  const updateStatus: () => Promise<void> = async () => {
    let response: Response;
    const url = new URL("/api/status", import.meta.env.VITE_SERVER);
    try {
      response = await fetch(url);
    } catch (error) {
      console.error(error);
      return;
    }

    if (response.ok) {
      const json = await response.json();
      setStatus(json);
    } else {
      console.error(response);
    }
  };

  useEffect(() => {
    updateStatus();
  }, []);

  return (
    <>
      <section className="page-header">
        <h1>Backup server</h1>
        <div className="actions">
          <AppButtonClear target="error" updateStatus={updateStatus} />
          <AppButtonClear target="finished" updateStatus={updateStatus} />
        </div>
      </section>
      <section className="section-container">
        {Object.entries(status).map(([name, tasks], idx) => (
          <AppSection key={idx} name={name} tasks={tasks} />
        ))}
      </section>
    </>
  );
}

export default App;
