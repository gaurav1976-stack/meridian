"""Aggregate model imports so Alembic + Base.metadata see every table.

Add new model modules here when converting Track A files.
"""
from app.models.core import (  # noqa: F401
    AuditLog,
    Project,
    ProjectMembership,
    Tenant,
    User,
    WorkPackage,
)
from app.models.project_setup import (  # noqa: F401
    Contract,
    MetadataFieldDefinition,
    NumberingRule,
    WorkflowDefinition,
)
from app.models.governance import (  # noqa: F401
    GateApproval,
    GateDecision,
    GateDefinition,
    GateEvidenceItem,
    GatePackageLink,
)
from app.models.commercial import (  # noqa: F401
    CommercialChangeItem,
    CommercialNoticeItem,
    PackageCostControl,
)
from app.models.design import (  # noqa: F401
    BimCoordinationItem,
    DesignDeliverable,
    DesignInterfaceItem,
    DesignPackage,
)
from app.models.documents import (  # noqa: F401
    ControlledDocument,
    DocumentReview,
    RepositoryLink,
    TransmittalRecord,
)
from app.models.accountability import (  # noqa: F401
    ActionItem,
    ComplianceItem,
    MeetingRecord,
)
from app.models.orat import (  # noqa: F401
    HandoverItem,
    OratTrial,
    OratWorkstream,
    TrainingGroup,
)
from app.models.reporting import (  # noqa: F401
    ArchiveRecord,
    ExportJob,
    ReportTemplate,
)
from app.models.risk import OpportunityItem, RiskItem  # noqa: F401
from app.models.schedule import (  # noqa: F401
    ActivityDependency,
    ScheduleActivity,
    ScheduleFile,
    ScheduleSnapshot,
)
from app.models.search import (  # noqa: F401
    ConnectorReference,
    SavedSearch,
    SearchIndexRecord,
)
