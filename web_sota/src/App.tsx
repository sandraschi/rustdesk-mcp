import { AppLayout } from "@/components/layout/app-layout";
import Logging from "@/pages/Logging";
import { About } from "@/pages/about";
import { ApiDocs } from "@/pages/api-docs";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Control } from "@/pages/control";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import { Settings } from "@/pages/settings";
import { Skills } from "@/pages/skills";
import { Status } from "@/pages/status";
import { Tools } from "@/pages/tools";
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
          <Route path="/tools" element={<Tools />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/api-docs" element={<ApiDocs />} />
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
