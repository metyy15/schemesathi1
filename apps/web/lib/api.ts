/**
 * API client for the SchemeSathi backend.
 * The bearer token is stored in localStorage and attached to every request.
 */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "schemesathi.token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const { auth = true, headers, ...rest } = options;

  const finalHeaders: Record<string, string> = {
    ...((headers as Record<string, string>) || {}),
  };

  if (!(rest.body instanceof FormData)) {
    finalHeaders["Content-Type"] = "application/json";
  }

  if (auth) {
    const token = getToken();
    if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
  });

  if (res.status === 401 && auth) {
    setToken(null);
    if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
    throw new ApiError("Your session expired. Please sign in again.", 401);
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) {
        detail = body.detail.map((d: any) => d.msg || String(d)).join("; ");
      }
    } catch {
      /* keep default detail */
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return (await res.json()) as T;
  return (await res.blob()) as T;
}

export const api = {
  // ---------------------------------------------------------- auth
  register: (body: {
    email: string;
    password: string;
    full_name?: string;
    state?: string;
    district?: string;
  }) =>
    request<{ access_token: string; token_type: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
      auth: false,
    }),

  login: (body: { email: string; password: string }) =>
    request<{ access_token: string; token_type: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
      auth: false,
    }),

  me: () =>
    request<{
      id: string;
      email: string;
      full_name: string | null;
      state: string | null;
      district: string | null;
      category: string | null;
      notification_preferences: Record<string, boolean>;
    }>("/api/auth/me"),

  updateMe: (body: Record<string, unknown>) =>
    request<{ status: string }>("/api/auth/me", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  // -------------------------------------------------------- consent
  consentPurposes: () =>
    request<{
      version: string;
      purposes: { purpose: string; description: string }[];
    }>("/api/consent/purposes"),

  myConsents: () =>
    request<
      {
        id: string;
        purpose: string;
        description: string;
        version: string;
        granted: boolean;
        granted_at: string | null;
        withdrawn_at: string | null;
      }[]
    >("/api/consent/mine"),

  grantConsent: (purpose: string) =>
    request<{ status: string; consent_id: string; already: boolean }>(
      "/api/consent/grant",
      { method: "POST", body: JSON.stringify({ purpose }) }
    ),

  withdrawConsent: (consentId: string) =>
    request<{ status: string }>("/api/consent/withdraw", {
      method: "POST",
      body: JSON.stringify({ consent_id: consentId }),
    }),

  // ------------------------------------------------------ documents
  uploadDocument: (file: File, documentType: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", documentType);
    return request<{
      document_id: string;
      status: string;
      filename: string;
      document_type: string;
      size_bytes: number;
      retention_date: string;
    }>("/api/documents/upload", { method: "POST", body: form });
  },

  myDocuments: () =>
    request<
      {
        id: string;
        filename: string;
        document_type: string;
        status: string;
        size_bytes: number;
        created_at: string;
        processed_at: string | null;
        retention_date: string | null;
      }[]
    >("/api/documents/mine"),

  deleteDocument: (id: string) =>
    request<{ status: string }>(`/api/documents/${id}`, { method: "DELETE" }),

  processDocument: (id: string) =>
    request<{
      document_id: string;
      status: string;
      extracted_text: string;
      suggested_fields: Record<string, unknown>;
      engine: string;
      notice: string;
    }>(`/api/ocr/process/${id}`, { method: "POST" }),

  // -------------------------------------------------------- profile
  facts: () => request<Fact[]>("/api/profile/facts"),

  addFact: (body: {
    field_name: string;
    value: string;
    source?: string;
    document_id?: string | null;
    confidence?: number | null;
    verified?: boolean;
  }) => request<Fact>("/api/profile/facts", { method: "POST", body: JSON.stringify(body) }),

  confirmFact: (id: string) =>
    request<Fact>(`/api/profile/facts/${id}/confirm`, { method: "POST" }),

  updateFact: (id: string, body: { value?: string; verified?: boolean }) =>
    request<Fact>(`/api/profile/facts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteFact: (id: string) =>
    request<{ status: string }>(`/api/profile/facts/${id}`, { method: "DELETE" }),

  // -------------------------------------------------------- schemes
  discover: (query: string, includeCommunity = true) =>
    request<DiscoveryResponse>("/api/schemes/discover", {
      method: "POST",
      body: JSON.stringify({ query, include_community: includeCommunity }),
    }),

  sources: () =>
    request<{
      official: string[];
      community: string[];
      tier_labels: Record<string, string>;
    }>("/api/schemes/sources"),

  extractScheme: (url: string) =>
    request<{
      scheme_id: string;
      source_tier: string;
      source_tier_label: string;
      verification_status: string;
      review_note: string | null;
      extracted: Record<string, unknown>;
    }>("/api/schemes/extract", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  listSchemes: () => request<Scheme[]>("/api/schemes/list"),

  getScheme: (id: string) => request<SchemeDetail>(`/api/schemes/${id}`),

  // ----------------------------------------------------- eligibility
  checkEligibility: (schemeId: string) =>
    request<EligibilityResult>("/api/eligibility/check", {
      method: "POST",
      body: JSON.stringify({ scheme_id: schemeId }),
    }),

  checkAllEligibility: () =>
    request<{ count: number; results: EligibilityResult[] }>(
      "/api/eligibility/check-all",
      { method: "POST" }
    ),

  results: () => request<EligibilityResult[]>("/api/eligibility/results"),

  // ------------------------------------------------------ certificate
  generateCertificate: () =>
    request<CertificatePayload>("/api/certificate/generate", { method: "POST" }),

  certificatePdfUrl: () => `${API_URL}/api/certificate/download`,

  // ------------------------------------------------------- monitoring
  checkUpdates: () =>
    request<{
      checked: number;
      update_count: number;
      updates_found: {
        scheme_id: string;
        scheme_name: string;
        url: string;
        source_tier: string;
        source_tier_label: string | null;
        change_detected: boolean;
        what_changed: string;
        why_it_matters: string;
        checked_at: string;
      }[];
      errors: { scheme: string; error: string }[];
      notice: string;
    }>("/api/monitoring/check-updates", { method: "POST" }),

  // --------------------------------------------------- notifications
  notifications: () => request<Notification[]>("/api/notifications/"),

  markNotificationRead: (id: string) =>
    request<{ status: string }>(`/api/notifications/mark-read/${id}`, {
      method: "POST",
    }),
};

// -------------------------------------------------------------- types

export interface Fact {
  id: string;
  field_name: string;
  value: string;
  source: string;
  document_id: string | null;
  confidence: number | null;
  verified: boolean;
  expiry_date: string | null;
  updated_at: string | null;
}

export interface Scheme {
  id: string;
  name: string;
  scope: string | null;
  state: string | null;
  ministry_department: string | null;
  benefit_description: string | null;
  benefit_amount: string | null;
  official_source_url: string;
  application_url: string | null;
  required_documents: string[];
  source_confidence: string;
  verification_status: string;
  source_tier: string;
  source_tier_label: string | null;
  official_application_confirmed: boolean;
  review_note: string | null;
  last_checked: string | null;
}

export interface SchemeCondition {
  id: string;
  condition_type: string;
  operator: string;
  value: string;
  description: string | null;
  evidence_url: string | null;
  evidence_tier: string;
  is_required: boolean;
}

export interface SchemeDetail extends Scheme {
  conditions: SchemeCondition[];
  evidence: {
    id: string;
    url: string;
    page_title: string | null;
    source_tier: string;
    source_tier_label: string | null;
    retrieved_at: string | null;
  }[];
}

export interface ConditionResult {
  condition: string;
  status: "matched" | "not_matched" | "needs_more_info" | "unknown";
  reason?: string;
  your_value?: string;
  required?: string;
  evidence_url?: string | null;
  evidence_excerpt?: string | null;
}

export interface EligibilityResult {
  scheme_id?: string;
  scheme_name?: string;
  outcome: "potentially_eligible" | "needs_more_info" | "likely_not_eligible";
  match_score: number;
  explanation?: string;
  condition_results: ConditionResult[];
  disclaimer: string;
  scope?: string | null;
  state?: string | null;
  ministry_department?: string | null;
  benefit_description?: string | null;
  benefit_amount?: string | null;
  official_source_url?: string;
  application_url?: string | null;
  required_documents?: string[];
  source_tier?: string;
  source_tier_label?: string | null;
  verification_status?: string;
  official_application_confirmed?: boolean;
  last_checked?: string | null;
  scheme?: Scheme;
}

export interface DiscoveryResult {
  title: string | null;
  url: string;
  snippet: string | null;
  source_tier: string;
  source_tier_label: string;
  source_tier_description: string;
  source_confidence: string;
  verification_status: string;
  is_official: boolean;
}

export interface DiscoveryResponse {
  count: number;
  official_count: number;
  community_count: number;
  results: DiscoveryResult[];
  notice: string;
}

export interface CertificatePayload {
  certificate_type: string;
  certificate_id: string;
  generated_at: string;
  holder: {
    name: string | null;
    email: string | null;
    state: string | null;
    district: string | null;
  };
  summary: {
    potentially_eligible: number;
    needs_more_information: number;
    likely_not_eligible: number;
    total_evaluated: number;
  };
  schemes: {
    name: string;
    outcome: string;
    match_score: number;
    official_source_url: string | null;
    application_url: string | null;
    benefit_description: string | null;
    last_checked: string | null;
    source_tier: string;
    source_tier_label: string | null;
    matched_conditions: ConditionResult[];
    missing_conditions: ConditionResult[];
    failed_conditions: ConditionResult[];
  }[];
  verification_hash: string;
  disclaimer: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  data: Record<string, unknown>;
  read: boolean;
  created_at: string;
}
