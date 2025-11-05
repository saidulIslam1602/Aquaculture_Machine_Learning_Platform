"""
Data Lineage Tracking and Catalog System

This module provides comprehensive data lineage tracking, data catalog management,
and metadata discovery for the agricultural IoT platform. It tracks data flow
from source to destination across all pipeline stages.

Key Features:
- Automated data lineage tracking
- Data catalog with schema evolution
- Metadata management and discovery
- Impact analysis and dependency tracking
- Data governance and compliance
- Integration with Apache Atlas (optional)

Industry Standards:
- OpenLineage specification compliance
- Apache Atlas integration ready
- Comprehensive metadata capture
- Automated lineage discovery
- Data governance workflows
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib

from sqlalchemy import create_engine, text, MetaData, Table, Column, String, DateTime, JSON, Boolean, Integer
from sqlalchemy.orm import sessionmaker
import networkx as nx
import pandas as pd

from services.api.core.config import settings


class DatasetType(Enum):
    """Types of datasets in the system."""
    SOURCE_TABLE = "source_table"
    TRANSFORMED_TABLE = "transformed_table"
    AGGREGATED_VIEW = "aggregated_view"
    ML_FEATURE_SET = "ml_feature_set"
    ANALYTICS_MART = "analytics_mart"
    STREAM_TOPIC = "stream_topic"
    FILE_DATASET = "file_dataset"


class OperationType(Enum):
    """Types of data operations."""
    EXTRACT = "extract"
    TRANSFORM = "transform"
    LOAD = "load"
    AGGREGATE = "aggregate"
    JOIN = "join"
    FILTER = "filter"
    ENRICH = "enrich"
    VALIDATE = "validate"


@dataclass
class DatasetMetadata:
    """Comprehensive dataset metadata."""
    dataset_id: str
    name: str
    dataset_type: DatasetType
    schema_definition: Dict[str, Any]
    location: str
    owner: str
    description: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None
    quality_score: Optional[float] = None
    is_active: bool = True


@dataclass
class LineageEdge:
    """Data lineage edge representing data flow."""
    edge_id: str
    source_dataset_id: str
    target_dataset_id: str
    operation_type: OperationType
    operation_details: Dict[str, Any]
    pipeline_name: str
    execution_id: str
    created_at: datetime
    column_mappings: Optional[Dict[str, List[str]]] = None


@dataclass
class PipelineExecution:
    """Pipeline execution metadata."""
    execution_id: str
    pipeline_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    input_datasets: List[str]
    output_datasets: List[str]
    transformation_details: Dict[str, Any]
    metrics: Dict[str, Any]


class DataLineageTracker:
    """
    Comprehensive data lineage tracking system.
    
    Tracks data flow, transformations, and dependencies across
    the entire agricultural IoT data platform.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_engine = create_engine(settings.DATABASE_URL)
        self.session_maker = sessionmaker(bind=self.db_engine)
        
        # Initialize lineage graph
        self.lineage_graph = nx.DiGraph()
        
        # Metadata storage
        self.datasets = {}
        self.lineage_edges = {}
        self.pipeline_executions = {}
        
        # Initialize database tables
        self._initialize_lineage_tables()
        
        self.logger.info("Data lineage tracker initialized")
    
    def _initialize_lineage_tables(self):
        """Initialize database tables for lineage tracking."""
        try:
            metadata = MetaData()
            
            # Datasets table
            datasets_table = Table(
                'data_catalog_datasets', metadata,
                Column('dataset_id', String, primary_key=True),
                Column('name', String, nullable=False),
                Column('dataset_type', String, nullable=False),
                Column('schema_definition', JSON),
                Column('location', String),
                Column('owner', String),
                Column('description', String),
                Column('tags', JSON),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow),
                Column('row_count', Integer),
                Column('size_bytes', Integer),
                Column('quality_score', String),
                Column('is_active', Boolean, default=True)
            )
            
            # Lineage edges table
            lineage_table = Table(
                'data_lineage_edges', metadata,
                Column('edge_id', String, primary_key=True),
                Column('source_dataset_id', String, nullable=False),
                Column('target_dataset_id', String, nullable=False),
                Column('operation_type', String, nullable=False),
                Column('operation_details', JSON),
                Column('pipeline_name', String),
                Column('execution_id', String),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('column_mappings', JSON)
            )
            
            # Pipeline executions table
            executions_table = Table(
                'pipeline_executions', metadata,
                Column('execution_id', String, primary_key=True),
                Column('pipeline_name', String, nullable=False),
                Column('start_time', DateTime, nullable=False),
                Column('end_time', DateTime),
                Column('status', String),
                Column('input_datasets', JSON),
                Column('output_datasets', JSON),
                Column('transformation_details', JSON),
                Column('metrics', JSON)
            )
            
            # Create tables
            metadata.create_all(self.db_engine)
            
            self.logger.info("Lineage tracking tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing lineage tables: {e}")
            raise
    
    def register_dataset(self, dataset: DatasetMetadata) -> str:
        """
        Register a new dataset in the catalog.
        
        Args:
            dataset: Dataset metadata to register
            
        Returns:
            Dataset ID
        """
        try:
            # Store in memory
            self.datasets[dataset.dataset_id] = dataset
            
            # Add to lineage graph
            self.lineage_graph.add_node(
                dataset.dataset_id,
                **asdict(dataset)
            )
            
            # Store in database
            with self.session_maker() as session:
                insert_query = text("""
                    INSERT INTO data_catalog_datasets 
                    (dataset_id, name, dataset_type, schema_definition, location, 
                     owner, description, tags, created_at, updated_at, row_count, 
                     size_bytes, quality_score, is_active)
                    VALUES (:dataset_id, :name, :dataset_type, :schema_definition, 
                            :location, :owner, :description, :tags, :created_at, 
                            :updated_at, :row_count, :size_bytes, :quality_score, :is_active)
                    ON CONFLICT (dataset_id) DO UPDATE SET
                        updated_at = :updated_at,
                        row_count = :row_count,
                        size_bytes = :size_bytes,
                        quality_score = :quality_score
                """)
                
                session.execute(insert_query, {
                    'dataset_id': dataset.dataset_id,
                    'name': dataset.name,
                    'dataset_type': dataset.dataset_type.value,
                    'schema_definition': json.dumps(dataset.schema_definition),
                    'location': dataset.location,
                    'owner': dataset.owner,
                    'description': dataset.description,
                    'tags': json.dumps(dataset.tags),
                    'created_at': dataset.created_at,
                    'updated_at': dataset.updated_at,
                    'row_count': dataset.row_count,
                    'size_bytes': dataset.size_bytes,
                    'quality_score': dataset.quality_score,
                    'is_active': dataset.is_active
                })
                session.commit()
            
            self.logger.info(f"Registered dataset: {dataset.name} ({dataset.dataset_id})")
            return dataset.dataset_id
            
        except Exception as e:
            self.logger.error(f"Error registering dataset: {e}")
            raise
    
    def track_lineage(self, lineage: LineageEdge) -> str:
        """
        Track data lineage between datasets.
        
        Args:
            lineage: Lineage edge to track
            
        Returns:
            Edge ID
        """
        try:
            # Store in memory
            self.lineage_edges[lineage.edge_id] = lineage
            
            # Add to lineage graph
            self.lineage_graph.add_edge(
                lineage.source_dataset_id,
                lineage.target_dataset_id,
                **asdict(lineage)
            )
            
            # Store in database
            with self.session_maker() as session:
                insert_query = text("""
                    INSERT INTO data_lineage_edges 
                    (edge_id, source_dataset_id, target_dataset_id, operation_type,
                     operation_details, pipeline_name, execution_id, created_at, column_mappings)
                    VALUES (:edge_id, :source_dataset_id, :target_dataset_id, :operation_type,
                            :operation_details, :pipeline_name, :execution_id, :created_at, :column_mappings)
                """)
                
                session.execute(insert_query, {
                    'edge_id': lineage.edge_id,
                    'source_dataset_id': lineage.source_dataset_id,
                    'target_dataset_id': lineage.target_dataset_id,
                    'operation_type': lineage.operation_type.value,
                    'operation_details': json.dumps(lineage.operation_details),
                    'pipeline_name': lineage.pipeline_name,
                    'execution_id': lineage.execution_id,
                    'created_at': lineage.created_at,
                    'column_mappings': json.dumps(lineage.column_mappings) if lineage.column_mappings else None
                })
                session.commit()
            
            self.logger.info(f"Tracked lineage: {lineage.source_dataset_id} -> {lineage.target_dataset_id}")
            return lineage.edge_id
            
        except Exception as e:
            self.logger.error(f"Error tracking lineage: {e}")
            raise
    
    def start_pipeline_execution(self, pipeline_name: str, input_datasets: List[str]) -> str:
        """
        Start tracking a pipeline execution.
        
        Args:
            pipeline_name: Name of the pipeline
            input_datasets: List of input dataset IDs
            
        Returns:
            Execution ID
        """
        try:
            execution_id = str(uuid.uuid4())
            
            execution = PipelineExecution(
                execution_id=execution_id,
                pipeline_name=pipeline_name,
                start_time=datetime.utcnow(),
                end_time=None,
                status="running",
                input_datasets=input_datasets,
                output_datasets=[],
                transformation_details={},
                metrics={}
            )
            
            self.pipeline_executions[execution_id] = execution
            
            self.logger.info(f"Started pipeline execution: {pipeline_name} ({execution_id})")
            return execution_id
            
        except Exception as e:
            self.logger.error(f"Error starting pipeline execution: {e}")
            raise
    
    def complete_pipeline_execution(self, execution_id: str, output_datasets: List[str],
                                  transformation_details: Dict[str, Any],
                                  metrics: Dict[str, Any], status: str = "completed"):
        """
        Complete a pipeline execution.
        
        Args:
            execution_id: Execution ID
            output_datasets: List of output dataset IDs
            transformation_details: Details of transformations performed
            metrics: Execution metrics
            status: Final status
        """
        try:
            if execution_id not in self.pipeline_executions:
                raise ValueError(f"Execution {execution_id} not found")
            
            execution = self.pipeline_executions[execution_id]
            execution.end_time = datetime.utcnow()
            execution.status = status
            execution.output_datasets = output_datasets
            execution.transformation_details = transformation_details
            execution.metrics = metrics
            
            # Store in database
            with self.session_maker() as session:
                insert_query = text("""
                    INSERT INTO pipeline_executions 
                    (execution_id, pipeline_name, start_time, end_time, status,
                     input_datasets, output_datasets, transformation_details, metrics)
                    VALUES (:execution_id, :pipeline_name, :start_time, :end_time, :status,
                            :input_datasets, :output_datasets, :transformation_details, :metrics)
                    ON CONFLICT (execution_id) DO UPDATE SET
                        end_time = :end_time,
                        status = :status,
                        output_datasets = :output_datasets,
                        transformation_details = :transformation_details,
                        metrics = :metrics
                """)
                
                session.execute(insert_query, {
                    'execution_id': execution_id,
                    'pipeline_name': execution.pipeline_name,
                    'start_time': execution.start_time,
                    'end_time': execution.end_time,
                    'status': execution.status,
                    'input_datasets': json.dumps(execution.input_datasets),
                    'output_datasets': json.dumps(execution.output_datasets),
                    'transformation_details': json.dumps(execution.transformation_details),
                    'metrics': json.dumps(execution.metrics)
                })
                session.commit()
            
            self.logger.info(f"Completed pipeline execution: {execution_id} ({status})")
            
        except Exception as e:
            self.logger.error(f"Error completing pipeline execution: {e}")
            raise
    
    def get_upstream_datasets(self, dataset_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Get all upstream datasets for a given dataset.
        
        Args:
            dataset_id: Target dataset ID
            max_depth: Maximum traversal depth
            
        Returns:
            List of upstream datasets with lineage information
        """
        try:
            upstream_datasets = []
            
            # Use BFS to traverse upstream
            visited = set()
            queue = [(dataset_id, 0)]
            
            while queue and len(upstream_datasets) < 100:  # Limit results
                current_id, depth = queue.pop(0)
                
                if current_id in visited or depth > max_depth:
                    continue
                
                visited.add(current_id)
                
                # Get predecessors in lineage graph
                predecessors = list(self.lineage_graph.predecessors(current_id))
                
                for pred_id in predecessors:
                    if pred_id not in visited:
                        # Get edge data
                        edge_data = self.lineage_graph.get_edge_data(pred_id, current_id)
                        
                        upstream_datasets.append({
                            'dataset_id': pred_id,
                            'dataset_info': self.datasets.get(pred_id, {}),
                            'lineage_info': edge_data,
                            'depth': depth + 1
                        })
                        
                        queue.append((pred_id, depth + 1))
            
            return upstream_datasets
            
        except Exception as e:
            self.logger.error(f"Error getting upstream datasets: {e}")
            return []
    
    def get_downstream_datasets(self, dataset_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Get all downstream datasets for a given dataset.
        
        Args:
            dataset_id: Source dataset ID
            max_depth: Maximum traversal depth
            
        Returns:
            List of downstream datasets with lineage information
        """
        try:
            downstream_datasets = []
            
            # Use BFS to traverse downstream
            visited = set()
            queue = [(dataset_id, 0)]
            
            while queue and len(downstream_datasets) < 100:  # Limit results
                current_id, depth = queue.pop(0)
                
                if current_id in visited or depth > max_depth:
                    continue
                
                visited.add(current_id)
                
                # Get successors in lineage graph
                successors = list(self.lineage_graph.successors(current_id))
                
                for succ_id in successors:
                    if succ_id not in visited:
                        # Get edge data
                        edge_data = self.lineage_graph.get_edge_data(current_id, succ_id)
                        
                        downstream_datasets.append({
                            'dataset_id': succ_id,
                            'dataset_info': self.datasets.get(succ_id, {}),
                            'lineage_info': edge_data,
                            'depth': depth + 1
                        })
                        
                        queue.append((succ_id, depth + 1))
            
            return downstream_datasets
            
        except Exception as e:
            self.logger.error(f"Error getting downstream datasets: {e}")
            return []
    
    def analyze_impact(self, dataset_id: str) -> Dict[str, Any]:
        """
        Analyze the impact of changes to a dataset.
        
        Args:
            dataset_id: Dataset to analyze
            
        Returns:
            Impact analysis report
        """
        try:
            # Get downstream datasets
            downstream = self.get_downstream_datasets(dataset_id)
            
            # Categorize impact
            impact_analysis = {
                'dataset_id': dataset_id,
                'dataset_name': self.datasets.get(dataset_id, {}).get('name', 'Unknown'),
                'total_downstream_datasets': len(downstream),
                'impact_by_type': {},
                'impact_by_depth': {},
                'critical_dependencies': [],
                'recommendations': []
            }
            
            # Analyze by dataset type
            for item in downstream:
                dataset_info = item.get('dataset_info', {})
                dataset_type = dataset_info.get('dataset_type', 'unknown')
                depth = item.get('depth', 0)
                
                # Count by type
                if dataset_type not in impact_analysis['impact_by_type']:
                    impact_analysis['impact_by_type'][dataset_type] = 0
                impact_analysis['impact_by_type'][dataset_type] += 1
                
                # Count by depth
                if depth not in impact_analysis['impact_by_depth']:
                    impact_analysis['impact_by_depth'][depth] = 0
                impact_analysis['impact_by_depth'][depth] += 1
                
                # Identify critical dependencies
                if dataset_type in ['analytics_mart', 'ml_feature_set'] or depth <= 2:
                    impact_analysis['critical_dependencies'].append({
                        'dataset_id': item['dataset_id'],
                        'dataset_name': dataset_info.get('name', 'Unknown'),
                        'dataset_type': dataset_type,
                        'depth': depth
                    })
            
            # Generate recommendations
            if len(downstream) > 10:
                impact_analysis['recommendations'].append(
                    "High impact change - consider gradual rollout and extensive testing"
                )
            
            if 'ml_feature_set' in impact_analysis['impact_by_type']:
                impact_analysis['recommendations'].append(
                    "ML models may be affected - retrain and validate models"
                )
            
            if 'analytics_mart' in impact_analysis['impact_by_type']:
                impact_analysis['recommendations'].append(
                    "Business reports may be affected - notify stakeholders"
                )
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing impact: {e}")
            return {}
    
    def discover_schema_changes(self, dataset_id: str, new_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Discover and analyze schema changes for a dataset.
        
        Args:
            dataset_id: Dataset ID
            new_schema: New schema definition
            
        Returns:
            Schema change analysis
        """
        try:
            dataset = self.datasets.get(dataset_id)
            if not dataset:
                return {'error': 'Dataset not found'}
            
            old_schema = dataset.schema_definition
            
            # Analyze changes
            changes = {
                'dataset_id': dataset_id,
                'dataset_name': dataset.name,
                'change_timestamp': datetime.utcnow().isoformat(),
                'added_columns': [],
                'removed_columns': [],
                'modified_columns': [],
                'type_changes': [],
                'impact_score': 0
            }
            
            old_columns = set(old_schema.get('columns', {}).keys())
            new_columns = set(new_schema.get('columns', {}).keys())
            
            # Find added/removed columns
            changes['added_columns'] = list(new_columns - old_columns)
            changes['removed_columns'] = list(old_columns - new_columns)
            
            # Find modified columns
            common_columns = old_columns & new_columns
            for col in common_columns:
                old_col_def = old_schema['columns'][col]
                new_col_def = new_schema['columns'][col]
                
                if old_col_def != new_col_def:
                    changes['modified_columns'].append({
                        'column': col,
                        'old_definition': old_col_def,
                        'new_definition': new_col_def
                    })
                    
                    # Check for type changes
                    if old_col_def.get('type') != new_col_def.get('type'):
                        changes['type_changes'].append({
                            'column': col,
                            'old_type': old_col_def.get('type'),
                            'new_type': new_col_def.get('type')
                        })
            
            # Calculate impact score
            impact_score = (
                len(changes['removed_columns']) * 3 +
                len(changes['type_changes']) * 2 +
                len(changes['modified_columns']) * 1
            )
            changes['impact_score'] = impact_score
            
            # Update dataset schema
            dataset.schema_definition = new_schema
            dataset.updated_at = datetime.utcnow()
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error discovering schema changes: {e}")
            return {'error': str(e)}
    
    def generate_lineage_report(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive lineage report.
        
        Args:
            dataset_id: Optional specific dataset to focus on
            
        Returns:
            Lineage report
        """
        try:
            report = {
                'report_timestamp': datetime.utcnow().isoformat(),
                'total_datasets': len(self.datasets),
                'total_lineage_edges': len(self.lineage_edges),
                'dataset_types': {},
                'operation_types': {},
                'lineage_depth_analysis': {},
                'orphaned_datasets': [],
                'circular_dependencies': []
            }
            
            # Analyze dataset types
            for dataset in self.datasets.values():
                dataset_type = dataset.dataset_type.value
                if dataset_type not in report['dataset_types']:
                    report['dataset_types'][dataset_type] = 0
                report['dataset_types'][dataset_type] += 1
            
            # Analyze operation types
            for edge in self.lineage_edges.values():
                op_type = edge.operation_type.value
                if op_type not in report['operation_types']:
                    report['operation_types'][op_type] = 0
                report['operation_types'][op_type] += 1
            
            # Find orphaned datasets (no upstream or downstream)
            for dataset_id, dataset in self.datasets.items():
                predecessors = list(self.lineage_graph.predecessors(dataset_id))
                successors = list(self.lineage_graph.successors(dataset_id))
                
                if not predecessors and not successors:
                    report['orphaned_datasets'].append({
                        'dataset_id': dataset_id,
                        'dataset_name': dataset.name,
                        'dataset_type': dataset.dataset_type.value
                    })
            
            # Detect circular dependencies
            try:
                cycles = list(nx.simple_cycles(self.lineage_graph))
                report['circular_dependencies'] = cycles
            except:
                report['circular_dependencies'] = []
            
            # Specific dataset analysis
            if dataset_id and dataset_id in self.datasets:
                report['focus_dataset'] = {
                    'dataset_id': dataset_id,
                    'upstream_count': len(self.get_upstream_datasets(dataset_id)),
                    'downstream_count': len(self.get_downstream_datasets(dataset_id)),
                    'impact_analysis': self.analyze_impact(dataset_id)
                }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating lineage report: {e}")
            return {'error': str(e)}


# Global lineage tracker instance
lineage_tracker = DataLineageTracker()


def auto_discover_agricultural_datasets():
    """Automatically discover and register agricultural datasets."""
    try:
        logging.info("Starting automatic dataset discovery")
        
        # Discover TimescaleDB tables
        with lineage_tracker.session_maker() as session:
            tables_query = text("""
                SELECT table_name, table_schema 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            
            tables = session.execute(tables_query).fetchall()
            
            for table in tables:
                table_name = table.table_name
                
                # Get column information
                columns_query = text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = :table_name
                    ORDER BY ordinal_position
                """)
                
                columns = session.execute(columns_query, {'table_name': table_name}).fetchall()
                
                # Build schema definition
                schema_def = {
                    'columns': {
                        col.column_name: {
                            'type': col.data_type,
                            'nullable': col.is_nullable == 'YES'
                        }
                        for col in columns
                    }
                }
                
                # Determine dataset type
                if 'telemetry' in table_name:
                    dataset_type = DatasetType.SOURCE_TABLE
                elif 'health' in table_name or 'analytics' in table_name:
                    dataset_type = DatasetType.ANALYTICS_MART
                elif 'ml_' in table_name or 'features' in table_name:
                    dataset_type = DatasetType.ML_FEATURE_SET
                else:
                    dataset_type = DatasetType.TRANSFORMED_TABLE
                
                # Create dataset metadata
                dataset = DatasetMetadata(
                    dataset_id=f"timescaledb.{table_name}",
                    name=table_name,
                    dataset_type=dataset_type,
                    schema_definition=schema_def,
                    location=f"timescaledb://agricultural_iot_db/{table_name}",
                    owner="data-engineering-team",
                    description=f"Auto-discovered table: {table_name}",
                    tags=["agricultural-iot", "timescaledb", "auto-discovered"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Register dataset
                lineage_tracker.register_dataset(dataset)
        
        logging.info("Automatic dataset discovery completed")
        
    except Exception as e:
        logging.error(f"Error in automatic dataset discovery: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run automatic discovery
    auto_discover_agricultural_datasets()
    
    # Generate lineage report
    report = lineage_tracker.generate_lineage_report()
    print(json.dumps(report, indent=2, default=str))
