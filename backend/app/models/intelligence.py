"""Intelligence entity models for Phase 2 - extracted decisions, actions, blockers, topics"""
from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, Enum, Boolean, Integer, Float
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class EntityTypeEnum(str, enum.Enum):
    """Intelligence entity types"""
    DECISION = "decision"
    ACTION = "action"
    BLOCKER = "blocker"
    TOPIC = "topic"


class IntelligenceEntity(Base):
    """Extracted intelligence entity (decision, action, blocker, topic)"""
    __tablename__ = "intelligence_entities"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    entity_type = Column(Enum(EntityTypeEnum), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # For action items
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), nullable=True)  # "low", "medium", "high"
    
    # For blockers
    blocked_item = Column(String(500), nullable=True)
    impact = Column(Text, nullable=True)
    
    # For topics
    semantic_embedding = Column(JSON, nullable=True)  # Vector stored as JSON
    
    # Metadata
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0 from AI extraction
    source_speaker = Column(String(255), nullable=True)
    source_timestamp = Column(Integer, nullable=True)  # Seconds from meeting start
    meta = Column("metadata_json", JSON, nullable=True)
    
    # Status tracking
    resolved = Column(Boolean, default=False)
    status = Column(String(50), nullable=True)  # "open", "in_progress", "resolved"
    
    # Temporal
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TopicCluster(Base):
    """Semantic topic cluster for meetings"""
    __tablename__ = "topic_clusters"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Semantic properties
    keywords = Column(JSON, nullable=True)  # List of key terms
    embedding = Column(JSON, nullable=True)  # Vector stored as JSON
    
    # Context
    segment_indices = Column(JSON, nullable=True)  # Indices of transcript chunks in this topic
    speaker_count = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GraphMutation(Base):
    """Record of incremental graph changes for realtime updates"""
    __tablename__ = "graph_mutations"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    
    mutation_type = Column(String(50), nullable=False)  # "node_added", "edge_added", "node_updated", "edge_updated"
    node_id = Column(String(36), nullable=True)
    edge_id = Column(String(36), nullable=True)
    
    # Mutation payload
    payload = Column(JSON, nullable=False)  # Full node/edge data
    
    # Order tracking for replay
    sequence_number = Column(Integer, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SemanticMemory(Base):
    """Indexed semantic memories for organizational knowledge retrieval"""
    __tablename__ = "semantic_memory"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Source references
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=True, index=True)
    entity_id = Column(String(36), ForeignKey("intelligence_entities.id"), nullable=True)
    
    memory_type = Column(String(50), nullable=False, index=True)  # "decision", "action", "blocker", "transcript_segment", "insight"
    content = Column(Text, nullable=False)
    
    # Embedding for semantic search
    embedding = Column(JSON, nullable=False)  # Vector stored as JSON
    
    # Search metadata
    keywords = Column(JSON, nullable=True)
    related_memory_ids = Column(JSON, nullable=True)  # List of related memory IDs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExecutionState(Base):
    """Tracks execution continuity and task status"""
    __tablename__ = "execution_state"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Reference to action item or decision
    entity_id = Column(String(36), ForeignKey("intelligence_entities.id"), nullable=False, index=True)
    
    # Status tracking
    status = Column(String(50), nullable=False)  # "pending", "in_progress", "completed", "blocked", "overdue"
    progress_percent = Column(Integer, nullable=True, default=0)
    
    # Dependency tracking
    depends_on_entity_ids = Column(JSON, nullable=True)
    blocking_entity_ids = Column(JSON, nullable=True)
    
    # Timeline
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Recurrence tracking
    recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100), nullable=True)  # "weekly", "daily", etc.
    
    # Decay detection
    is_stale = Column(Boolean, default=False)
    is_overdue = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AIProcessingCache(Base):
    """Cache for AI extraction results and embeddings"""
    __tablename__ = "ai_processing_cache"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Reference to what was processed
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=True, index=True)
    transcript_segment_hash = Column(String(255), nullable=True, unique=True, index=True)
    
    cache_type = Column(String(50), nullable=False, index=True)  # "extraction", "embedding", "summary"
    
    # Cached result
    cache_key = Column(String(500), nullable=False, unique=True, index=True)
    cache_value = Column(JSON, nullable=False)
    
    # Metadata
    ttl_seconds = Column(Integer, nullable=True)  # Time to live; None = no expiry
    hit_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
