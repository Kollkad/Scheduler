// frontend/client/App.tsx
import "./global.css";
import { useEffect } from "react"; 
import { Toaster } from "@/components/ui/toaster";
import { createRoot } from "react-dom/client";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import Rainbow from "./pages/Rainbow";
import { Search } from "./pages/Search";
import Tasks from "./pages/Tasks";
import { TermsOfSupport } from "./pages/TermsOfSupport";
import { FilteredCases  } from "./pages/FilteredCases";
import { SystemOverview } from "./pages/SystemOverview"; 
import NotFound from "./pages/NotFound";
import DynamicCaseDetail from '@/pages/DynamicCaseDetail';
import DocumentDetail from '@/pages/DocumentDetail';
import { AnalysisProvider } from "@/contexts/AnalysisContext";
import TaskDetail from './pages/TaskDetail';
import Depersonalization from "./pages/Depersonalization";

const queryClient = new QueryClient();

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AnalysisProvider>
            <Layout>
              <Routes>
                <Route path="/" element={<SystemOverview />} /> 
                <Route path="/overview" element={<SystemOverview />} /> 
                <Route path="/rainbow" element={<Rainbow />} />
                <Route path="/search" element={<Search />} />
                <Route path="/tasks" element={<Tasks />} />
                <Route path="/terms" element={<TermsOfSupport />} />
                <Route path="/depersonalization" element={<Depersonalization />} />
                <Route path="/case/:caseCode" element={<DynamicCaseDetail />} />
                <Route path="/document" element={<DocumentDetail />} />
                <Route path="/filtered-cases" element={<FilteredCases />} />
                <Route path="/task/:taskCode" element={<TaskDetail />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Layout>
          </AnalysisProvider>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

createRoot(document.getElementById("root")!).render(<App />);