import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Index from "./pages/Index.tsx";
import NotFound from "./pages/NotFound.tsx";
import MllmBuilder from "./pages/MllmBuilder.tsx";
import DigitalTwin from "./pages/DigitalTwin.tsx";
import TrainingLab from "./pages/TrainingLab.tsx";
import Ablation from "./pages/Ablation.tsx";
import GridDetails from "./pages/GridDetails.tsx";
import CellDetailsPage from "./pages/CellDetailsPage.tsx";
import InternalPoiHeatmap from "./pages/InternalPoiHeatmap.tsx";
import PoiDataManager from "./pages/PoiDataManager.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/classification/:jobId/cell/:cellId" element={<CellDetailsPage />} />
          <Route path="/classification/:jobId" element={<Index />} />
          <Route path="/grid/:id/details" element={<GridDetails />} />
          <Route path="/mllm-builder" element={<MllmBuilder />} />
          <Route path="/digital-twin" element={<DigitalTwin />} />
          <Route path="/training-lab" element={<TrainingLab />} />
          <Route path="/ablation" element={<Ablation />} />
          <Route path="/internal/poi-heatmap" element={<InternalPoiHeatmap />} />
          <Route path="/poi-manager" element={<PoiDataManager />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
