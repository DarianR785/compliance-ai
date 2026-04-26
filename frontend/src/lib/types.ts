export interface ChecklistItem {
  id: string;
  title: string;
  status: "required" | "pending" | "compliant";
  priority: "critical" | "high" | "medium" | "low";
  category: "permits" | "licenses" | "inspections" | "zoning";
  detail: string;
  agency: string;
  fee: string;
  timeline: string;
  renewal: string;
}

export interface Source {
  title: string;
  agency: string;
  score: number;
}

export interface AnalyzeResponse {
  business_type: string;
  business_label: string;
  location: string;
  features: string[];
  summary: string;
  checklist: ChecklistItem[];
  sources: Source[];
  mock: boolean;
}

export interface SavedProfile {
  id: string;
  businessName: string;
  businessType: string;
  businessLabel: string;
  location: string;
  savedAt: string;
  itemCounts: { required: number; pending: number; compliant: number };
  data: AnalyzeResponse;
}
