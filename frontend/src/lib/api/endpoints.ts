// Endpoint wrappers — one typed function per REST surface. Components import
// from here rather than calling `api` directly so URLs live in one place.

import { api } from "./client";
import type {
  AccountabilitySummary,
  ActionItem,
  ArchiveRecord,
  BimItem,
  CommercialChange,
  CommercialNotice,
  CommercialSummary,
  ComplianceItem,
  ConnectorReference,
  ConnectorSourcePressure,
  ControlledDocument,
  DesignDeliverable,
  DesignInterface,
  DesignPackage,
  DesignSummary,
  DocumentControlSummary,
  DocumentReview,
  EvmSummary,
  ExportJob,
  FreezeControlReport,
  GateDefinition,
  GateReadinessSummary,
  GovernanceSummary,
  HandoverItem,
  MeetingRecord,
  MeResponse,
  ModuleRegistryEntry,
  OratReadinessSummary,
  OratTrial,
  OratWorkstream,
  PackageActionPressure,
  PackageCommercialExposure,
  PackageCostControl,
  PackageHandoverPressure,
  Project,
  ProjectDashboard,
  ReportTemplate,
  ReportingSummary,
  RepositoryLink,
  Risk,
  SavedSearch,
  ScheduleActivity,
  SearchIndexRecord,
  SearchQueryResult,
  SearchSummary,
  TemplateUsagePressure,
  TrainingGroup,
  TransmittalRecord,
} from "../types";

export const endpoints = {
  health: () => api.get<{ status: string; app: string; version: string }>("/health"),
  modules: () => api.get<ModuleRegistryEntry[]>("/modules"),
  me: () => api.get<MeResponse>("/auth/me"),
  listProjects: () => api.get<Project[]>("/projects"),
  getProject: (id: string) => api.get<Project>(`/projects/${id}`),
  projectDashboard: (id: string) =>
    api.get<ProjectDashboard>(`/projects/${id}/dashboard`),
  listRisks: (projectId: string) =>
    api.get<Risk[]>(`/projects/${projectId}/risks`),
  listActivities: (projectId: string) =>
    api.get<ScheduleActivity[]>(`/projects/${projectId}/schedule/activities`),
  listGates: (projectId: string) =>
    api.get<GateDefinition[]>(`/projects/${projectId}/stage-gates`),
  gateReadiness: (projectId: string, gateId: string) =>
    api.get<GateReadinessSummary>(
      `/projects/${projectId}/stage-gates/${gateId}/readiness`
    ),
  governanceSummary: (projectId: string) =>
    api.get<GovernanceSummary>(`/projects/${projectId}/stage-gates/summary`),
  listCostControls: (projectId: string) =>
    api.get<PackageCostControl[]>(
      `/projects/${projectId}/commercial/cost-controls`
    ),
  listChanges: (projectId: string) =>
    api.get<CommercialChange[]>(`/projects/${projectId}/commercial/changes`),
  listNotices: (projectId: string) =>
    api.get<CommercialNotice[]>(`/projects/${projectId}/commercial/notices`),
  commercialSummary: (projectId: string) =>
    api.get<CommercialSummary>(`/projects/${projectId}/commercial/summary`),
  evmSummary: (projectId: string) =>
    api.get<EvmSummary>(`/projects/${projectId}/commercial/evm-summary`),
  packageExposure: (projectId: string) =>
    api.get<PackageCommercialExposure[]>(
      `/projects/${projectId}/commercial/exposure`
    ),
  listDesignPackages: (projectId: string) =>
    api.get<DesignPackage[]>(
      `/projects/${projectId}/design/design-packages`
    ),
  listDeliverables: (projectId: string) =>
    api.get<DesignDeliverable[]>(
      `/projects/${projectId}/design/deliverables`
    ),
  listInterfaces: (projectId: string) =>
    api.get<DesignInterface[]>(`/projects/${projectId}/design/interfaces`),
  listBimItems: (projectId: string) =>
    api.get<BimItem[]>(`/projects/${projectId}/design/bim-items`),
  designSummary: (projectId: string) =>
    api.get<DesignSummary>(`/projects/${projectId}/design/summary`),
  freezeControl: (projectId: string) =>
    api.get<FreezeControlReport>(`/projects/${projectId}/design/freeze-control`),
  listDocuments: (projectId: string) =>
    api.get<ControlledDocument[]>(`/projects/${projectId}/documents`),
  listDocumentReviews: (projectId: string) =>
    api.get<DocumentReview[]>(`/projects/${projectId}/documents/reviews`),
  listTransmittals: (projectId: string) =>
    api.get<TransmittalRecord[]>(`/projects/${projectId}/documents/transmittals`),
  listRepositoryLinks: (projectId: string) =>
    api.get<RepositoryLink[]>(
      `/projects/${projectId}/documents/repository-links`
    ),
  documentControlSummary: (projectId: string) =>
    api.get<DocumentControlSummary>(
      `/projects/${projectId}/documents/summary`
    ),
  listMeetings: (projectId: string) =>
    api.get<MeetingRecord[]>(`/projects/${projectId}/meetings`),
  listActions: (projectId: string) =>
    api.get<ActionItem[]>(`/projects/${projectId}/meetings/actions`),
  listComplianceItems: (projectId: string) =>
    api.get<ComplianceItem[]>(
      `/projects/${projectId}/meetings/compliance-items`
    ),
  accountabilitySummary: (projectId: string) =>
    api.get<AccountabilitySummary>(
      `/projects/${projectId}/meetings/summary`
    ),
  actionPressure: (projectId: string) =>
    api.get<PackageActionPressure[]>(
      `/projects/${projectId}/meetings/action-pressure`
    ),
  listOratWorkstreams: (projectId: string) =>
    api.get<OratWorkstream[]>(`/projects/${projectId}/orat/workstreams`),
  listOratTrials: (projectId: string) =>
    api.get<OratTrial[]>(`/projects/${projectId}/orat/trials`),
  listTrainingGroups: (projectId: string) =>
    api.get<TrainingGroup[]>(`/projects/${projectId}/orat/training-groups`),
  listHandoverItems: (projectId: string) =>
    api.get<HandoverItem[]>(`/projects/${projectId}/orat/handover-items`),
  oratReadinessSummary: (projectId: string) =>
    api.get<OratReadinessSummary>(`/projects/${projectId}/orat/summary`),
  handoverPressure: (projectId: string) =>
    api.get<PackageHandoverPressure[]>(
      `/projects/${projectId}/orat/handover-pressure`
    ),
  listReportTemplates: (projectId: string) =>
    api.get<ReportTemplate[]>(`/projects/${projectId}/reporting/templates`),
  listExportJobs: (projectId: string) =>
    api.get<ExportJob[]>(`/projects/${projectId}/reporting/export-jobs`),
  listArchiveRecords: (projectId: string) =>
    api.get<ArchiveRecord[]>(`/projects/${projectId}/reporting/archive`),
  reportingSummary: (projectId: string) =>
    api.get<ReportingSummary>(`/projects/${projectId}/reporting/summary`),
  templateUsagePressure: (projectId: string) =>
    api.get<TemplateUsagePressure[]>(
      `/projects/${projectId}/reporting/template-pressure`
    ),
  listSearchIndex: (projectId: string) =>
    api.get<SearchIndexRecord[]>(`/projects/${projectId}/search/index`),
  querySearchIndex: (projectId: string, queryText: string) =>
    api.get<SearchQueryResult>(
      `/projects/${projectId}/search/query?q=${encodeURIComponent(queryText)}`
    ),
  listSavedSearches: (projectId: string) =>
    api.get<SavedSearch[]>(`/projects/${projectId}/search/saved-searches`),
  listConnectorReferences: (projectId: string) =>
    api.get<ConnectorReference[]>(
      `/projects/${projectId}/search/connector-references`
    ),
  searchSummary: (projectId: string) =>
    api.get<SearchSummary>(`/projects/${projectId}/search/summary`),
  connectorSourcePressure: (projectId: string) =>
    api.get<ConnectorSourcePressure[]>(
      `/projects/${projectId}/search/connector-pressure`
    ),
};
