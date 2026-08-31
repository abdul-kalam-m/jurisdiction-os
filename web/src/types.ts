export type ConfidenceTier = 'A' | 'B' | 'C'
export type Action = 'approved' | 'denied' | 'carried' | 'heard' | 'withdrawn'
export type AssetType = 'multifamily' | 'small-commercial'

export interface JurisdictionRegistryEntry {
  city: string
  total_permits_in_window: number
  overall_exclusion_rate: number
  data_quality_flag: boolean
  best_confidence_tier: ConfidenceTier
  classes_with_data: string[]
}

export interface JurisdictionsRegistry {
  note: string
  jurisdictions: Record<string, JurisdictionRegistryEntry>
}

export interface ClassMetrics {
  coverage: 'ok' | 'no_data'
  n_permits?: number
  median_days?: number
  p25_days?: number
  p75_days?: number
  annual_volume?: Record<string, number>
  trend_slope_per_year?: number | null
  n_years?: number
  confidence_tier?: ConfidenceTier
}

export interface Scorecard {
  city: string
  total_permits_in_window: number
  overall_exclusion_rate: number
  data_quality_flag: boolean
  classes: Record<string, ClassMetrics>
}

export interface PlaybookCitation {
  name: string
  url: string
}

export interface SubmissionRequirement {
  item: string
  citation: string
}

export interface PermitPath {
  triggering_conditions: string[]
  likely_permits: string[]
  hearing_likelihood: string
  hearing_likelihood_basis: string
  review_body: string
  submission_requirements: SubmissionRequirement[]
}

export interface Playbook {
  jurisdiction: string
  state: string
  verified: boolean
  statutory_framework: { description: string; citations: PlaybookCitation[]; note?: string }
  local_code: Record<string, unknown>
  permit_paths: Record<string, PermitPath>
}

export interface SignalItem {
  meeting_date: string
  board: string
  case_ref: string | null
  applicant_type: string
  project_desc: string
  use_type: string
  action: Action
  variances_mentioned: string[]
  source_url: string
  confidence: number
  municipality: string
}

export interface AlertPoint {
  as_of: string
  median_90d: number | null
  median_baseline: number | null
  n_90d: number
  ratio: number | null
  alert: boolean
}

export interface AlertClassResult {
  coverage: 'ok' | 'insufficient_history' | 'no_data'
  detail?: string
  n_backtest_points?: number
  n_alert_points?: number
  current?: AlertPoint
  timeline?: AlertPoint[]
}

export interface AlertsPayload {
  note: string
  rule: {
    window_90d_days: number
    baseline_total_days: number
    ratio_threshold: number
    min_n_90d: number
    live_rule_cadence: string
    backtest_sample_step_days: number
  }
  jurisdictions: Record<string, { city: string; classes: Record<string, AlertClassResult> }>
  summary: {
    total_backtest_points: number
    total_alert_points: number
    currently_alerting: { jurisdiction: string; shared_class: string }[]
  }
}

export const CLASS_LABELS: Record<string, string> = {
  'new-construction-res': 'New Construction (Residential)',
  'new-construction-com': 'New Construction (Commercial)',
  'alteration-major': 'Alteration (Major)',
  'alteration-minor': 'Alteration (Minor)',
  demolition: 'Demolition',
  'site/civil': 'Site / Civil',
}

export const CITY_SLUGS = ['nyc', 'chicago', 'austin', 'san-francisco', 'seattle', 'los-angeles'] as const
export const MUNI_SLUGS = ['jersey-city', 'hoboken', 'princeton', 'montclair', 'nyc'] as const
