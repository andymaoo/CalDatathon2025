"""
Build Master Colleges Dataset

Main script to aggregate, clean, and enhance college data from multiple CSV sources.
"""

import sys
from pathlib import Path

# Add project root to path so we can import data module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.csv_processor import build_master_colleges
from data.custom_analysis import enhance_master_colleges
from data.quality_checker import quality_checks
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Build and enhance master colleges dataset."""
    # Build master dataset
    logger.info("Building master colleges dataset...")
    master_df = build_master_colleges(
        csv_paths={
            "affordability": "affordability.csv",
            "results": "college_results.csv"
        },
        merge_keys={
            "affordability": "institution_id",
            "results": "institution_id"
        },
        output_path="data/master_colleges.csv",
        data_dir="data/raw"
    )
    
    # Run quality checks
    logger.info("Running quality checks...")
    quality_report = quality_checks(master_df, "outputs/data_quality_report.json")
    
    # Enhance with custom metrics
    logger.info("Enhancing with custom metrics...")
    enhanced_df = enhance_master_colleges(master_df)
    
    # Save enhanced version
    enhanced_df.to_csv("data/master_colleges.csv", index=False)
    logger.info("Master colleges dataset complete!")
    logger.info(f"Final shape: {enhanced_df.shape}")
    logger.info(f"Quality score: {quality_report['overall_quality_score']}/100")


if __name__ == "__main__":
    main()

