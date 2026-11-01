import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("loading...");

  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/health")
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => setStatus("backend not reachable"));
  }, []);

  return <h1>Backend status: {status}</h1>;
}

export default App;