// Frontend types. Keep these in lockstep with `backend/app/schemas/*.py`.

export type ProjectStatus = "Active" | "Planned" | "On Hold" | "Closed";

export interface Project {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  location: string | null;
  status: ProjectStatus;
  stage: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardCounts {
  work_packages: number;
  contracts: number;
  open_risks: number;
  schedule_activities: number;
  activities_critical: number;
}

export interface ProjectDashboard {
  project: Project;
  counts: DashboardCounts;
}

export interface MeResponse {
  user_id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: string;
}

export interface ModuleRegistryEntry {
  key: string;
  label: string;
  icon: string;
  route: string;
  is_enabled: boolean;
}

export interface Risk {
  id: string;
  project_id: string;
  code: string;
  title: string;
  category: string;
  status: string;
  likelihood: number;
  impact: number;
  gross_score: number;
  residual_score: number;
  owner: string | null;
}

export interface ScheduleActivity {
  id: string;
  project_id: string;
  activity_id_external: string;
  name: string;
  status: string;
  planned_start: string | null;
  planned_finish: string | null;
  percent_complete: number;
  total_float_days: number | null;
  is_critical: boolean | null;
}

// ---------------------------------------------------------------------------
// Stage Gate Governance — mirrors backend/app/schemas/governance.py
// ---------------------------------------------------------------------------

export type GateStatus = "Complete" | "Active" | "Upcoming" | "Blocked";

export interface GateDefinition {
  id: string;
  project_id: string;
  tenant_id: string;
  code: string;
  name: string;
  purpose: string;
  target_month: number;
  status: GateStatus;
  created_at: string;
  updated_at: string;
}

export interface GateReadinessSummary {
  gate_id: string;
  gate_code: string;
  gate_name: string;
  status: GateStatus;
  target_month: number;
  readiness_score: number;
  approval_progress: number;
  blocker_count: number;
  required_evidence_count: number;
  accepted_evidence_count: number;
  submitted_evidence_count: number;
  approval_count: number;
  decision_count: number;
  linked_package_count: number;
  latest_decision: string | null;
}

export interface GovernanceSummary {
  project_id: string;
  gate_count: number;
  active_gates: number;
  blocked_gates: number;
  evidence_count: number;
  approval_count: number;
  decision_count: number;
  average_readiness_score: number;
}

// ---------------------------------------------------------------------------
// Commercial / Cost & Change Control — mirrors backend/app/schemas/commercial.py
// ---------------------------------------------------------------------------

export type ChangeType =
  | "Compensation Event"
  | "Variation"
  | "Client Change"
  | "Authority Change"
  | "Claim";

export type ChangeStatus =
  | "Identified"
  | "Notified"
  | "Quoted"
  | "Approved"
  | "Rejected"
  | "Implemented";

export type EntitlementStrength = "Strong" | "Moderate" | "Weak";

export type NoticeKind = "EWN" | "Notice" | "CE Notification" | "Claim Notice";

export type NoticeStatus = "Open" | "Issued" | "Overdue" | "Closed";

export interface PackageCostControl {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string;
  budget_minor: number;
  committed_minor: number;
  forecast_minor: number;
  actual_minor: number;
  percent_complete: number;
  created_at: string;
  updated_at: string;
}

export interface CommercialChange {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string | null;
  ref: string;
  title: string;
  change_type: ChangeType;
  status: ChangeStatus;
  cost_impact_minor: number;
  time_impact_weeks: number;
  entitlement: EntitlementStrength;
  owner: string;
  cause: string;
  created_at: string;
  updated_at: string;
}

export interface CommercialNotice {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string | null;
  ref: string;
  contract_ref: string;
  kind: NoticeKind;
  due_days: number;
  status: NoticeStatus;
  owner: string;
  created_at: string;
  updated_at: string;
}

export interface CommercialSummary {
  project_id: string;
  budget_minor: number;
  committed_minor: number;
  forecast_minor: number;
  actual_minor: number;
  forecast_variance_minor: number;
  change_exposure_minor: number;
  notice_count: number;
  overdue_notice_count: number;
  strong_entitlement_count: number;
}

export interface EvmSummary {
  project_id: string;
  bac_minor: number;
  pv_minor: number;
  ev_minor: number;
  ac_minor: number;
  cpi: number;
  spi: number;
  cv_minor: number;
  sv_minor: number;
  average_percent_complete: number;
}

export interface PackageCommercialExposure {
  package_id: string;
  package_code: string;
  package_name: string;
  budget_minor: number;
  forecast_minor: number;
  actual_minor: number;
  change_exposure_minor: number;
  notice_count: number;
  overdue_notice_count: number;
}

// ---------------------------------------------------------------------------
// Design Management — mirrors backend/app/schemas/design.py
// ---------------------------------------------------------------------------

export type RibaStage = "0" | "1" | "2" | "3" | "4" | "5" | "6";

export type DesignPackageStatus =
  | "Draft"
  | "In Review"
  | "Coordinating"
  | "Ready for Issue"
  | "Frozen";

export type DeliverableType =
  | "Drawing"
  | "Report"
  | "Calculation"
  | "Specification"
  | "Schedule";

export type DeliverableStatus =
  | "WIP"
  | "Shared"
  | "Published"
  | "Accepted"
  | "Overdue";

export type InterfaceStatus =
  | "Open"
  | "Assigned"
  | "Resolving"
  | "Closed"
  | "Escalated";

export type ModelShareStatus = "WIP" | "Shared" | "Published";

export interface DesignPackage {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string | null;
  code: string;
  name: string;
  lead_discipline: string;
  stage: RibaStage;
  maturity_pct: number;
  status: DesignPackageStatus;
  freeze_planned_month: number;
  freeze_current_month: number;
  created_at: string;
  updated_at: string;
}

export interface DesignDeliverable {
  id: string;
  project_id: string;
  tenant_id: string;
  design_package_id: string | null;
  package_id: string | null;
  ref: string;
  title: string;
  discipline: string;
  deliverable_type: DeliverableType;
  stage: RibaStage;
  due_month: number;
  status: DeliverableStatus;
  owner: string;
  created_at: string;
  updated_at: string;
}

export interface DesignInterface {
  id: string;
  project_id: string;
  tenant_id: string;
  ref: string;
  title: string;
  package_a_id: string;
  package_b_id: string;
  owner: string;
  severity: number;
  status: InterfaceStatus;
  due_month: number;
  created_at: string;
  updated_at: string;
}

export interface BimItem {
  id: string;
  project_id: string;
  tenant_id: string;
  workstream: string;
  clash_open: number;
  clash_critical: number;
  federation_ready: boolean;
  model_share_status: ModelShareStatus;
  created_at: string;
  updated_at: string;
}

export interface DesignSummary {
  project_id: string;
  design_package_count: number;
  deliverable_count: number;
  interface_count: number;
  bim_item_count: number;
  average_maturity_pct: number;
  overdue_deliverable_count: number;
  frozen_package_count: number;
  escalated_interface_count: number;
  critical_clash_count: number;
  average_freeze_variance_months: number;
}

export interface FreezeControlEntry {
  design_package_id: string;
  code: string;
  name: string;
  status: DesignPackageStatus;
  stage: RibaStage;
  maturity_pct: number;
  freeze_planned_month: number;
  freeze_current_month: number;
  variance_months: number;
}

export interface FreezeControlReport {
  project_id: string;
  entries: FreezeControlEntry[];
}

// ---------------------------------------------------------------------------
// Document Control — mirrors backend/app/schemas/documents.py
// ---------------------------------------------------------------------------

export type DocumentType =
  | "Drawing"
  | "Report"
  | "Calculation"
  | "Specification"
  | "Letter"
  | "Transmittal"
  | "Procedure";

export type DocumentWorkflowStatus =
  | "WIP"
  | "Shared"
  | "Published"
  | "Accepted"
  | "Archived"
  | "Overdue";

export type CdeStage = "WIP" | "Shared" | "Published" | "Archived";

export type ReviewStatus = "Pending" | "In Review" | "Approved" | "Rejected";

export type RepositorySource = "Meridian" | "BIM360" | "SharePoint";

export type TransmittalStatus =
  | "Draft"
  | "Issued"
  | "Acknowledged"
  | "Returned";

export type SyncStatus = "Linked" | "Pending Sync" | "Out of Sync";

export interface ControlledDocument {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string | null;
  number: string;
  title: string;
  discipline: string;
  document_type: DocumentType;
  revision: string;
  suitability: string;
  workflow_status: DocumentWorkflowStatus;
  cde_stage: CdeStage;
  owner: string;
  due_month: number;
  metadata_pct: number;
  source: RepositorySource;
  created_at: string;
  updated_at: string;
}

export interface DocumentReview {
  id: string;
  project_id: string;
  tenant_id: string;
  document_id: string;
  reviewer: string;
  role: string;
  status: ReviewStatus;
  due_month: number;
  created_at: string;
  updated_at: string;
}

export interface TransmittalRecord {
  id: string;
  project_id: string;
  tenant_id: string;
  ref: string;
  package_id: string | null;
  recipient: string;
  document_count: number;
  issue_month: number;
  status: TransmittalStatus;
  created_at: string;
  updated_at: string;
}

export interface RepositoryLink {
  id: string;
  project_id: string;
  tenant_id: string;
  document_id: string;
  repository: RepositorySource;
  path: string;
  sync_status: SyncStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentControlSummary {
  project_id: string;
  document_count: number;
  review_count: number;
  transmittal_count: number;
  repository_link_count: number;
  average_metadata_pct: number;
  overdue_document_count: number;
  published_document_count: number;
  pending_review_count: number;
  sync_issue_count: number;
  issued_transmittal_count: number;
}

// ---------------------------------------------------------------------------
// Meetings, Actions & Compliance — mirrors backend/app/schemas/accountability.py
// ---------------------------------------------------------------------------

export type MeetingType =
  | "Governance Board"
  | "Package Review"
  | "Design Review"
  | "Commercial Review"
  | "ORAT Review"
  | "Coordination";

export type LinkedModule =
  | "Gate"
  | "Risk"
  | "Document"
  | "Commercial"
  | "Programme"
  | "ORAT";

export type ActionSourceType =
  | "Meeting"
  | "Gate"
  | "Risk"
  | "Document"
  | "Commercial"
  | "ORAT";

export type ActionPriority = "Critical" | "High" | "Medium" | "Low";

export type ActionStatus =
  | "Open"
  | "In Progress"
  | "Awaiting Review"
  | "Closed"
  | "Overdue";

export type ComplianceDomain =
  | "Governance"
  | "Document Control"
  | "Commercial"
  | "Design"
  | "ORAT"
  | "Programme";

export type ComplianceStatus =
  | "Open"
  | "In Progress"
  | "Compliant"
  | "Non-Compliant"
  | "Overdue";

export interface MeetingRecord {
  id: string;
  project_id: string;
  tenant_id: string;
  ref: string;
  title: string;
  meeting_type: MeetingType;
  month: number;
  chair: string;
  attendee_count: number;
  linked_module: LinkedModule;
  created_at: string;
  updated_at: string;
}

export interface ActionItem {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string | null;
  ref: string;
  title: string;
  owner: string;
  source_type: ActionSourceType;
  source_ref: string;
  priority: ActionPriority;
  due_month: number;
  status: ActionStatus;
  closure_evidence_pct: number;
  created_at: string;
  updated_at: string;
}

export interface ComplianceItem {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string | null;
  ref: string;
  title: string;
  domain: ComplianceDomain;
  owner: string;
  due_month: number;
  status: ComplianceStatus;
  evidence_pct: number;
  created_at: string;
  updated_at: string;
}

export interface AccountabilitySummary {
  project_id: string;
  meeting_count: number;
  action_count: number;
  compliance_count: number;
  open_action_count: number;
  overdue_action_count: number;
  average_closure_evidence_pct: number;
  compliant_count: number;
  non_compliant_count: number;
}

export interface PackageActionPressure {
  package_id: string;
  package_code: string;
  package_name: string;
  action_count: number;
  overdue_count: number;
  critical_count: number;
  average_closure_evidence_pct: number;
}

// ---------------------------------------------------------------------------
// ORAT Readiness & Handover — mirrors backend/app/schemas/orat.py
// ---------------------------------------------------------------------------

export type OratWorkstreamStatus =
  | "Not Started"
  | "In Progress"
  | "At Risk"
  | "Ready";

export type TrialStatus =
  | "Planned"
  | "Prepared"
  | "Executed"
  | "Passed"
  | "Failed";

export type TrainingStatus =
  | "Not Started"
  | "Scheduled"
  | "In Delivery"
  | "Complete";

export type HandoverStatus =
  | "Pending"
  | "In Verification"
  | "Accepted"
  | "Blocked";

export interface OratWorkstream {
  id: string;
  project_id: string;
  tenant_id: string;
  name: string;
  owner: string;
  progress_pct: number;
  status: OratWorkstreamStatus;
  due_month: number;
  created_at: string;
  updated_at: string;
}

export interface OratTrial {
  id: string;
  project_id: string;
  tenant_id: string;
  workstream_id: string | null;
  ref: string;
  title: string;
  month: number;
  participants: number;
  status: TrialStatus;
  observations: string;
  created_at: string;
  updated_at: string;
}

export interface TrainingGroup {
  id: string;
  project_id: string;
  tenant_id: string;
  function_name: string;
  target_headcount: number;
  trained_headcount: number;
  status: TrainingStatus;
  owner: string;
  created_at: string;
  updated_at: string;
}

export interface HandoverItem {
  id: string;
  project_id: string;
  tenant_id: string;
  package_id: string | null;
  ref: string;
  asset_group: string;
  status: HandoverStatus;
  evidence_pct: number;
  owner: string;
  created_at: string;
  updated_at: string;
}

export interface OratReadinessSummary {
  project_id: string;
  workstream_count: number;
  trial_count: number;
  training_group_count: number;
  handover_item_count: number;
  average_workstream_progress_pct: number;
  at_risk_workstream_count: number;
  passed_trial_count: number;
  training_completion_pct: number;
  accepted_handover_count: number;
  blocked_handover_count: number;
}

export interface PackageHandoverPressure {
  package_id: string;
  package_code: string;
  package_name: string;
  handover_count: number;
  accepted_count: number;
  blocked_count: number;
  pending_count: number;
  average_evidence_pct: number;
}

// ---------------------------------------------------------------------------
// Reporting & Export — mirrors backend/app/schemas/reporting.py
// ---------------------------------------------------------------------------

export type ReportFormat = "PDF" | "Excel" | "PDF + Excel";

export type ReportTemplateType =
  | "Board Pack"
  | "Monthly PMO Report"
  | "Gate Evidence Pack"
  | "Risk Report"
  | "Commercial Summary"
  | "Document Control Report"
  | "ORAT Readiness Pack";

export type ExportJobStatus =
  | "Draft"
  | "Queued"
  | "Generating"
  | "Ready"
  | "Failed";

export interface ReportTemplate {
  id: string;
  project_id: string;
  tenant_id: string;
  name: string;
  template_type: ReportTemplateType;
  audience: string;
  section_count: number;
  default_format: ReportFormat;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExportJob {
  id: string;
  project_id: string;
  tenant_id: string;
  template_id: string | null;
  ref: string;
  title: string;
  format: ReportFormat;
  created_by: string;
  created_month: number;
  status: ExportJobStatus;
  progress_pct: number;
  artifact_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArchiveRecord {
  id: string;
  project_id: string;
  tenant_id: string;
  export_job_id: string | null;
  ref: string;
  title: string;
  format: ReportFormat;
  generated_month: number;
  size_mb: number;
  tags: string[];
  artifact_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReportingSummary {
  project_id: string;
  template_count: number;
  enabled_template_count: number;
  job_count: number;
  active_job_count: number;
  ready_job_count: number;
  failed_job_count: number;
  archive_count: number;
  average_job_progress_pct: number;
}

export interface TemplateUsagePressure {
  template_id: string;
  template_name: string;
  template_type: ReportTemplateType;
  enabled: boolean;
  job_count: number;
  active_count: number;
  ready_count: number;
  failed_count: number;
}

// ---------------------------------------------------------------------------
// Enterprise Search & Retrieval — mirrors backend/app/schemas/search.py
// ---------------------------------------------------------------------------

export type SearchEntityType =
  | "Project"
  | "Schedule"
  | "Gate"
  | "Risk"
  | "Commercial"
  | "Design"
  | "Document"
  | "Action"
  | "ORAT"
  | "Repository"
  | "Report";

export type SearchSource = "Meridian" | "BIM360" | "SharePoint" | "Teams";

export type SearchGroup =
  | "Core"
  | "Delivery"
  | "Governance"
  | "Commercial"
  | "Technical"
  | "Operations"
  | "Outputs";

export type SavedSearchScope = "All" | "Module Specific" | "Repository Only";

export type ConnectorSyncStatus = "Indexed" | "Pending" | "Stale" | "Failed";

export interface SearchIndexRecord {
  id: string;
  project_id: string;
  tenant_id: string;
  entity_type: SearchEntityType;
  entity_ref: string;
  title: string;
  summary: string;
  source: SearchSource;
  group_name: SearchGroup;
  package_code: string | null;
  status_text: string | null;
  tags: string[];
  permission_scope: string;
  created_at: string;
  updated_at: string;
}

export interface SavedSearch {
  id: string;
  project_id: string;
  tenant_id: string;
  user_email: string;
  name: string;
  query_text: string;
  scope: SavedSearchScope;
  type_filter: string | null;
  source_filter: string | null;
  package_filter: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConnectorReference {
  id: string;
  project_id: string;
  tenant_id: string;
  source: SearchSource;
  external_ref: string;
  path: string;
  sync_status: ConnectorSyncStatus;
  index_record_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SearchQueryResult {
  total: number;
  grouped_counts: Record<string, number>;
  results: SearchIndexRecord[];
}

export interface SearchSummary {
  project_id: string;
  indexed_record_count: number;
  saved_search_count: number;
  connector_reference_count: number;
  indexed_connector_count: number;
  stale_connector_count: number;
  records_by_type: Record<string, number>;
  records_by_source: Record<string, number>;
}

export interface ConnectorSourcePressure {
  source: SearchSource;
  total_count: number;
  indexed_count: number;
  pending_count: number;
  stale_count: number;
  failed_count: number;
}
