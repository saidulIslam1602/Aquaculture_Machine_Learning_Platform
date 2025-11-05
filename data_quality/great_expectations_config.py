"""
Great Expectations Data Quality Framework Configuration

This module configures Great Expectations for comprehensive data quality validation
in the agricultural IoT platform. It includes custom expectations, validation suites,
and automated data quality reporting.

Key Features:
- Custom expectations for agricultural IoT data
- Automated validation suites for all data sources
- Data quality reporting and alerting
- Integration with data pipeline monitoring
- Historical data quality tracking

Industry Standards:
- Comprehensive data profiling
- Business rule validation
- Statistical anomaly detection
- Data drift monitoring
- Automated quality gates
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

import great_expectations as ge
from great_expectations.core import ExpectationSuite, ExpectationConfiguration
from great_expectations.data_context import DataContext
from great_expectations.data_context.types.base import DataContextConfig, DatasourceConfig
from great_expectations.datasource import BaseDatasource
from great_expectations.validator.validator import Validator
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from services.api.core.config import settings


class AgriculturalIoTExpectations:
    """
    Custom Great Expectations suite for agricultural IoT data validation.
    
    Provides domain-specific data quality checks for livestock monitoring,
    sensor telemetry, and agricultural analytics.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_engine = create_engine(settings.DATABASE_URL)
        
        # Initialize Great Expectations context
        self.context = self._initialize_ge_context()
        
        # Configuration for agricultural IoT validation
        self.validation_config = {
            "sensor_telemetry": {
                "freshness_threshold_minutes": 30,
                "temperature_range": (-10, 50),
                "battery_range": (0, 100),
                "signal_strength_range": (-120, -30),
                "quality_score_threshold": 0.7,
                "max_null_percentage": 5.0
            },
            "entities": {
                "required_fields": ["id", "farm_id", "entity_type", "entity_metadata"],
                "valid_entity_types": ["livestock", "aquaculture", "equipment"],
                "max_age_days": 365
            },
            "alerts": {
                "severity_levels": ["low", "medium", "high", "critical"],
                "max_resolution_hours": 24,
                "required_fields": ["id", "entity_id", "alert_type", "severity"]
            }
        }
    
    def _initialize_ge_context(self) -> DataContext:
        """Initialize Great Expectations data context."""
        try:
            # Create data context configuration
            data_context_config = DataContextConfig(
                config_version=3.0,
                datasources={
                    "agricultural_timescaledb": DatasourceConfig(
                        class_name="Datasource",
                        execution_engine={
                            "class_name": "SqlAlchemyExecutionEngine",
                            "connection_string": settings.DATABASE_URL
                        },
                        data_connectors={
                            "default_runtime_data_connector": {
                                "class_name": "RuntimeDataConnector",
                                "batch_identifiers": ["default_identifier_name"]
                            },
                            "default_inferred_data_connector": {
                                "class_name": "InferredAssetSqlDataConnector",
                                "include_schema_name": True
                            }
                        }
                    )
                },
                stores={
                    "expectations_store": {
                        "class_name": "ExpectationsStore",
                        "store_backend": {
                            "class_name": "TupleFilesystemStoreBackend",
                            "base_directory": "data_quality/expectations/"
                        }
                    },
                    "validations_store": {
                        "class_name": "ValidationsStore",
                        "store_backend": {
                            "class_name": "TupleFilesystemStoreBackend",
                            "base_directory": "data_quality/validations/"
                        }
                    },
                    "evaluation_parameter_store": {
                        "class_name": "EvaluationParameterStore"
                    }
                },
                expectations_store_name="expectations_store",
                validations_store_name="validations_store",
                evaluation_parameter_store_name="evaluation_parameter_store",
                data_docs_sites={
                    "local_site": {
                        "class_name": "SiteBuilder",
                        "show_how_to_buttons": True,
                        "store_backend": {
                            "class_name": "TupleFilesystemStoreBackend",
                            "base_directory": "data_quality/data_docs/"
                        },
                        "site_index_builder": {
                            "class_name": "DefaultSiteIndexBuilder"
                        }
                    }
                }
            )
            
            # Create context
            context = DataContext(project_config=data_context_config)
            
            self.logger.info("Great Expectations context initialized successfully")
            return context
            
        except Exception as e:
            self.logger.error(f"Error initializing Great Expectations context: {e}")
            raise
    
    def create_sensor_telemetry_suite(self) -> ExpectationSuite:
        """
        Create comprehensive expectation suite for sensor telemetry data.
        
        Returns:
            ExpectationSuite for sensor telemetry validation
        """
        suite_name = "agricultural_sensor_telemetry_suite"
        
        try:
            # Create or get existing suite
            suite = self.context.create_expectation_suite(
                expectation_suite_name=suite_name,
                overwrite_existing=True
            )
            
            config = self.validation_config["sensor_telemetry"]
            
            # Basic schema expectations
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_table_columns_to_match_ordered_list",
                    kwargs={
                        "column_list": [
                            "timestamp", "sensor_id", "entity_id", "metrics",
                            "location", "temperature", "battery_level", 
                            "signal_strength", "data_quality_score", "is_anomaly"
                        ]
                    }
                )
            )
            
            # Timestamp expectations
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_not_be_null",
                    kwargs={"column": "timestamp"}
                )
            )
            
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_of_type",
                    kwargs={"column": "timestamp", "type_": "datetime64"}
                )
            )
            
            # Data freshness expectation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_max_to_be_between",
                    kwargs={
                        "column": "timestamp",
                        "min_value": datetime.utcnow() - timedelta(minutes=config["freshness_threshold_minutes"]),
                        "max_value": datetime.utcnow() + timedelta(minutes=5)
                    }
                )
            )
            
            # Temperature validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_between",
                    kwargs={
                        "column": "temperature",
                        "min_value": config["temperature_range"][0],
                        "max_value": config["temperature_range"][1]
                    }
                )
            )
            
            # Battery level validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_between",
                    kwargs={
                        "column": "battery_level",
                        "min_value": config["battery_range"][0],
                        "max_value": config["battery_range"][1]
                    }
                )
            )
            
            # Signal strength validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_between",
                    kwargs={
                        "column": "signal_strength",
                        "min_value": config["signal_strength_range"][0],
                        "max_value": config["signal_strength_range"][1]
                    }
                )
            )
            
            # Data quality score validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_between",
                    kwargs={
                        "column": "data_quality_score",
                        "min_value": 0.0,
                        "max_value": 1.0
                    }
                )
            )
            
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_mean_to_be_between",
                    kwargs={
                        "column": "data_quality_score",
                        "min_value": config["quality_score_threshold"],
                        "max_value": 1.0
                    }
                )
            )
            
            # Null value expectations
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_not_be_null",
                    kwargs={"column": "sensor_id"}
                )
            )
            
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_not_be_null",
                    kwargs={"column": "entity_id"}
                )
            )
            
            # Duplicate detection
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_compound_columns_to_be_unique",
                    kwargs={"column_list": ["timestamp", "sensor_id", "entity_id"]}
                )
            )
            
            # Geospatial validation (if location data exists)
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_not_be_null",
                    kwargs={"column": "location"}
                )
            )
            
            # Custom agricultural IoT expectations
            self._add_custom_agricultural_expectations(suite)
            
            # Save suite
            self.context.save_expectation_suite(suite)
            
            self.logger.info(f"Created sensor telemetry expectation suite with {len(suite.expectations)} expectations")
            return suite
            
        except Exception as e:
            self.logger.error(f"Error creating sensor telemetry suite: {e}")
            raise
    
    def create_entities_suite(self) -> ExpectationSuite:
        """
        Create expectation suite for entities (animals, equipment) data.
        
        Returns:
            ExpectationSuite for entities validation
        """
        suite_name = "agricultural_entities_suite"
        
        try:
            suite = self.context.create_expectation_suite(
                expectation_suite_name=suite_name,
                overwrite_existing=True
            )
            
            config = self.validation_config["entities"]
            
            # Required fields validation
            for field in config["required_fields"]:
                suite.add_expectation(
                    ExpectationConfiguration(
                        expectation_type="expect_column_values_to_not_be_null",
                        kwargs={"column": field}
                    )
                )
            
            # Entity type validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_in_set",
                    kwargs={
                        "column": "entity_type",
                        "value_set": config["valid_entity_types"]
                    }
                )
            )
            
            # Farm ID validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_match_regex",
                    kwargs={
                        "column": "farm_id",
                        "regex": r"^FARM_[A-Z0-9]{6,12}$"
                    }
                )
            )
            
            # Metadata validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_not_be_null",
                    kwargs={"column": "entity_metadata"}
                )
            )
            
            # Age validation for livestock
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_between",
                    kwargs={
                        "column": "created_at",
                        "min_value": datetime.utcnow() - timedelta(days=config["max_age_days"]),
                        "max_value": datetime.utcnow()
                    }
                )
            )
            
            # Unique constraints
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_unique",
                    kwargs={"column": "id"}
                )
            )
            
            # Save suite
            self.context.save_expectation_suite(suite)
            
            self.logger.info(f"Created entities expectation suite with {len(suite.expectations)} expectations")
            return suite
            
        except Exception as e:
            self.logger.error(f"Error creating entities suite: {e}")
            raise
    
    def create_alerts_suite(self) -> ExpectationSuite:
        """
        Create expectation suite for alerts data.
        
        Returns:
            ExpectationSuite for alerts validation
        """
        suite_name = "agricultural_alerts_suite"
        
        try:
            suite = self.context.create_expectation_suite(
                expectation_suite_name=suite_name,
                overwrite_existing=True
            )
            
            config = self.validation_config["alerts"]
            
            # Required fields validation
            for field in config["required_fields"]:
                suite.add_expectation(
                    ExpectationConfiguration(
                        expectation_type="expect_column_values_to_not_be_null",
                        kwargs={"column": field}
                    )
                )
            
            # Severity validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_in_set",
                    kwargs={
                        "column": "severity",
                        "value_set": config["severity_levels"]
                    }
                )
            )
            
            # Timestamp validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_of_type",
                    kwargs={"column": "created_at", "type_": "datetime64"}
                )
            )
            
            # Resolution time validation
            suite.add_expectation(
                ExpectationConfiguration(
                    expectation_type="expect_column_pair_values_A_to_be_greater_than_B",
                    kwargs={
                        "column_A": "resolved_at",
                        "column_B": "created_at",
                        "or_equal": True
                    }
                )
            )
            
            # Save suite
            self.context.save_expectation_suite(suite)
            
            self.logger.info(f"Created alerts expectation suite with {len(suite.expectations)} expectations")
            return suite
            
        except Exception as e:
            self.logger.error(f"Error creating alerts suite: {e}")
            raise
    
    def _add_custom_agricultural_expectations(self, suite: ExpectationSuite):
        """Add custom expectations specific to agricultural IoT data."""
        
        # Heart rate validation for livestock
        suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_between",
                kwargs={
                    "column": "metrics",
                    "min_value": 40,
                    "max_value": 200,
                    "parse_strings_as_datetimes": False,
                    "condition_parser": "json",
                    "condition_path": "$.heart_rate"
                }
            )
        )
        
        # Activity level validation
        suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_between",
                kwargs={
                    "column": "metrics",
                    "min_value": 0,
                    "max_value": 10,
                    "condition_parser": "json",
                    "condition_path": "$.activity_level"
                }
            )
        )
        
        # Step count validation
        suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_between",
                kwargs={
                    "column": "metrics",
                    "min_value": 0,
                    "max_value": 50000,
                    "condition_parser": "json",
                    "condition_path": "$.step_count"
                }
            )
        )
    
    def validate_data_batch(self, table_name: str, suite_name: str, 
                           time_window_hours: int = 1) -> Dict[str, Any]:
        """
        Validate a batch of data using the specified expectation suite.
        
        Args:
            table_name: Name of the table to validate
            suite_name: Name of the expectation suite to use
            time_window_hours: Time window for data selection
            
        Returns:
            Validation results dictionary
        """
        try:
            self.logger.info(f"Validating {table_name} with suite {suite_name}")
            
            # Get data batch
            query = f"""
                SELECT *
                FROM {table_name}
                WHERE timestamp >= NOW() - INTERVAL '{time_window_hours} hours'
                ORDER BY timestamp DESC
                LIMIT 10000
            """
            
            # Create batch request
            batch_request = {
                "datasource_name": "agricultural_timescaledb",
                "data_connector_name": "default_runtime_data_connector",
                "data_asset_name": table_name,
                "runtime_parameters": {"query": query},
                "batch_identifiers": {"default_identifier_name": f"{table_name}_{datetime.utcnow().isoformat()}"}
            }
            
            # Get validator
            validator = self.context.get_validator(
                batch_request=batch_request,
                expectation_suite_name=suite_name
            )
            
            # Run validation
            validation_result = validator.validate()
            
            # Process results
            results_summary = {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "table_name": table_name,
                "suite_name": suite_name,
                "success": validation_result.success,
                "statistics": validation_result.statistics,
                "results": []
            }
            
            # Extract detailed results
            for result in validation_result.results:
                result_detail = {
                    "expectation_type": result.expectation_config.expectation_type,
                    "success": result.success,
                    "result": result.result
                }
                
                if not result.success:
                    result_detail["exception_info"] = result.exception_info
                
                results_summary["results"].append(result_detail)
            
            # Calculate success rate
            total_expectations = len(validation_result.results)
            successful_expectations = sum(1 for r in validation_result.results if r.success)
            results_summary["success_rate"] = successful_expectations / total_expectations if total_expectations > 0 else 0
            
            self.logger.info(f"Validation completed: {results_summary['success_rate']:.2%} success rate")
            
            return results_summary
            
        except Exception as e:
            self.logger.error(f"Error validating data batch: {e}")
            raise
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive validation across all data sources.
        
        Returns:
            Complete validation report
        """
        self.logger.info("Running comprehensive data validation")
        
        validation_report = {
            "validation_timestamp": datetime.utcnow().isoformat(),
            "overall_success": True,
            "table_results": {}
        }
        
        # Validation configurations
        validations = [
            ("sensor_telemetry", "agricultural_sensor_telemetry_suite"),
            ("entities", "agricultural_entities_suite"),
            ("alerts", "agricultural_alerts_suite")
        ]
        
        for table_name, suite_name in validations:
            try:
                # Ensure suite exists
                if suite_name == "agricultural_sensor_telemetry_suite":
                    self.create_sensor_telemetry_suite()
                elif suite_name == "agricultural_entities_suite":
                    self.create_entities_suite()
                elif suite_name == "agricultural_alerts_suite":
                    self.create_alerts_suite()
                
                # Run validation
                result = self.validate_data_batch(table_name, suite_name)
                validation_report["table_results"][table_name] = result
                
                # Update overall success
                if not result["success"]:
                    validation_report["overall_success"] = False
                    
            except Exception as e:
                self.logger.error(f"Error validating {table_name}: {e}")
                validation_report["table_results"][table_name] = {
                    "success": False,
                    "error": str(e)
                }
                validation_report["overall_success"] = False
        
        # Generate summary statistics
        validation_report["summary"] = self._generate_validation_summary(validation_report["table_results"])
        
        return validation_report
    
    def _generate_validation_summary(self, table_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from validation results."""
        total_tables = len(table_results)
        successful_tables = sum(1 for result in table_results.values() if result.get("success", False))
        
        # Calculate average success rate
        success_rates = [
            result.get("success_rate", 0) 
            for result in table_results.values() 
            if "success_rate" in result
        ]
        avg_success_rate = np.mean(success_rates) if success_rates else 0
        
        return {
            "total_tables_validated": total_tables,
            "successful_tables": successful_tables,
            "table_success_rate": successful_tables / total_tables if total_tables > 0 else 0,
            "average_expectation_success_rate": avg_success_rate,
            "recommendations": self._generate_validation_recommendations(table_results)
        }
    
    def _generate_validation_recommendations(self, table_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        for table_name, result in table_results.items():
            if not result.get("success", True):
                recommendations.append(f"Investigate data quality issues in {table_name}")
            
            success_rate = result.get("success_rate", 1.0)
            if success_rate < 0.9:
                recommendations.append(f"Review data validation rules for {table_name} (success rate: {success_rate:.1%})")
        
        return recommendations
    
    def generate_data_docs(self):
        """Generate Great Expectations data documentation."""
        try:
            self.context.build_data_docs()
            self.logger.info("Data documentation generated successfully")
        except Exception as e:
            self.logger.error(f"Error generating data docs: {e}")
            raise


# Initialize Great Expectations configuration
ge_config = AgriculturalIoTExpectations()


def run_data_quality_validation() -> Dict[str, Any]:
    """Run complete data quality validation pipeline."""
    try:
        # Run comprehensive validation
        validation_report = ge_config.run_comprehensive_validation()
        
        # Generate data docs
        ge_config.generate_data_docs()
        
        return validation_report
        
    except Exception as e:
        logging.error(f"Error in data quality validation: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run validation
    report = run_data_quality_validation()
    print(json.dumps(report, indent=2, default=str))
