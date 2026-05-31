export interface CandidateProfile {
  candidate_id: string;
  file_name?: string;
  name: string;
  age: string;
  experience: string;
  skills: string[];
  role: string;
  job_roles: string[];
  recommended_jobs: string[];
  resume_text?: string;
  created_at?: string;
  rank_score?: number;
  duplicate?: boolean;
}

export interface SearchResponse {
  total_results: number;
  filters_used: {
    skills: string[];
    experience: number | null;
  };
  candidates: CandidateProfile[];
}

export interface SearchHistory {
  query: string;
  candidates: CandidateProfile[];
  total_results: number;
  filters_used: {
    skills: string[];
    experience: number | null;
  };
  searched_at: string;
}
