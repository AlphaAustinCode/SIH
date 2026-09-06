from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


# ============================================================
# ENUMS
# ============================================================

class LineType(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"
    LOOP = "LOOP"


class Department(str, enum.Enum):
    TMS = "TMS"
    SMMS = "SMMS"
    TDMS = "TDMS"


class MaintenanceStatus(str, enum.Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class BlockStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"


# ============================================================
# TRACK SECTION
# ============================================================

class TrackSection(Base):
    """
    Represents a physical railway corridor segment.

    Example:
    Dadar -> Thane
    Chainage: KM 9.50 to KM 24.00
    """

    __tablename__ = "track_sections"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    section_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    start_station_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    end_station_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    line_type: Mapped[LineType] = mapped_column(
        Enum(LineType),
        nullable=False,
    )

    start_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    end_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    max_permissible_speed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    trains: Mapped[list["TrainSchedule"]] = relationship(
        back_populates="track_section"
    )

    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(
        back_populates="track_section"
    )

    allocated_blocks: Mapped[list["AllocatedBlock"]] = relationship(
        back_populates="track_section"
    )


# ============================================================
# TRAIN SCHEDULE
# ============================================================

class TrainSchedule(Base):
    """
    Represents a train occupying a particular track section
    during a scheduled time interval.
    """

    __tablename__ = "train_schedules"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    train_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    train_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # 1 = Highest priority
    # 2 = Express / Mail
    # 3 = Freight / lower priority
    priority_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    track_section_id: Mapped[int] = mapped_column(
        ForeignKey("track_sections.id"),
        nullable=False,
    )

    scheduled_entry: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    scheduled_exit: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    direction: Mapped[LineType] = mapped_column(
        Enum(LineType),
        nullable=False,
    )

    track_section: Mapped["TrackSection"] = relationship(
        back_populates="trains"
    )


# ============================================================
# MAINTENANCE REQUEST
# ============================================================

class MaintenanceRequest(Base):
    """
    Maintenance task received from:

    TMS  -> Track Maintenance System
    SMMS -> Signalling Maintenance Management System
    TDMS -> Traction Distribution Management System
    """

    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    department: Mapped[Department] = mapped_column(
        Enum(Department),
        nullable=False,
        index=True,
    )

    asset_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    track_section_id: Mapped[int] = mapped_column(
        ForeignKey("track_sections.id"),
        nullable=False,
    )

    location_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    required_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    urgency_priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    power_isolation_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    traffic_block_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus),
        default=MaintenanceStatus.PENDING,
        nullable=False,
    )

    # Nullable because requests start out unassigned to any block
    allocated_block_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("allocated_blocks.id"),
        nullable=True,
    )

    track_section: Mapped["TrackSection"] = relationship(
        back_populates="maintenance_requests"
    )

    allocated_block: Mapped[Optional["AllocatedBlock"]] = relationship(
        back_populates="maintenance_requests"
    )


# ============================================================
# ALLOCATED BLOCK
# ============================================================

class AllocatedBlock(Base):
    """
    Represents an optimized integrated maintenance block.
    """

    __tablename__ = "allocated_blocks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    track_section_id: Mapped[int] = mapped_column(
        ForeignKey("track_sections.id"),
        nullable=False,
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    status: Mapped[BlockStatus] = mapped_column(
        Enum(BlockStatus),
        default=BlockStatus.DRAFT,
        nullable=False,
    )

    track_section: Mapped["TrackSection"] = relationship(
        back_populates="allocated_blocks"
    )

    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(
        back_populates="allocated_block"
    )