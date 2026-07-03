import { AppLayout } from "@/components/layout/app-layout";
import Logging from "@/pages/Logging";
import { About } from "@/pages/about";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Control } from "@/pages/control";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import { Settings } from "@/pages/settings";
import { Status } from "@/pages/status";
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/status" element={<Status />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/help" element={<Help />} />
          <Route path="/control" element={<Control />} />
          <Route path="/about" element={<About />} />
          <Route path="/logs" element={<Logging />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
