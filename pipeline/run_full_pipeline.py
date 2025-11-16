"""
Main Pipeline Runner

Purpose: Single entry point for complete pipeline execution
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.predict_impact import predict_bill_impact
from pipeline.export_for_tableau import export_for_tableau
from pipeline.box_client import initialize_box_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main pipeline execution function."""
    parser = argparse.ArgumentParser(
        description="Education Policy Impact ML Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a local bill PDF
  python pipeline/run_full_pipeline.py --bill bills/sample_bill.pdf --scenario funding_cut_10pct

  # Process a bill from Box
  python pipeline/run_full_pipeline.py --bill bill_2024_123.pdf --scenario funding_cut_10pct --use-box --box-folder-id 123456789

  # Process with CSV analysis
  python pipeline/run_full_pipeline.py --bill bills/sample_bill.pdf --scenario test --run-analysis
        """
    )
    
    parser.add_argument(
        "--bill",
        required=True,
        help="Path to bill PDF (or filename if using Box)"
    )
    
    parser.add_argument(
        "--scenario",
        required=True,
        help="Scenario identifier (e.g., '10pct_funding_cut')"
    )
    
    parser.add_argument(
        "--master-colleges",
        default="data/master_colleges.csv",
        help="Path to master colleges CSV"
    )
    
    parser.add_argument(
        "--models-dir",
        default="models/saved_models",
        help="Directory containing trained models"
    )
    
    parser.add_argument(
        "--use-box",
        action="store_true",
        help="Download bill from Box instead of local file"
    )
    
    parser.add_argument(
        "--box-folder-id",
        help="Box folder ID (required if --use-box)"
    )
    
    parser.add_argument(
        "--affected-states",
        nargs="+",
        help="List of affected states (e.g., --affected-states CA TX NY)"
    )
    
    parser.add_argument(
        "--run-analysis",
        action="store_true",
        help="Run CSV analysis after prediction"
    )
    
    parser.add_argument(
        "--upload-to-box",
        action="store_true",
        help="Upload outputs to Box after processing"
    )
    
    parser.add_argument(
        "--box-output-folder-id",
        help="Box folder ID for outputs (required if --upload-to-box)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.use_box and not args.box_folder_id:
        logger.error("--box-folder-id required when using --use-box")
        sys.exit(1)
    
    if args.upload_to_box and not args.box_output_folder_id:
        logger.error("--box-output-folder-id required when using --upload-to-box")
        sys.exit(1)
    
    # Check if master colleges exists
    if not Path(args.master_colleges).exists():
        logger.error(f"Master colleges file not found: {args.master_colleges}")
        logger.error("Please run data/build_master_colleges.py first")
        sys.exit(1)
    
    # Check if models exist
    models_path = Path(args.models_dir)
    required_models = ["tuition_model.pkl", "enrollment_model.pkl", "grad_rate_model.pkl", "equity_model.pkl"]
    missing_models = [m for m in required_models if not (models_path / m).exists()]
    if missing_models:
        logger.error(f"Missing trained models: {missing_models}")
        logger.error("Please run models/train_models.py first")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("Education Policy Impact ML Pipeline")
    logger.info("="*60)
    logger.info(f"Bill: {args.bill}")
    logger.info(f"Scenario: {args.scenario}")
    logger.info(f"Using Box: {args.use_box}")
    logger.info("")
    
    # Step 1: Predict bill impact
    logger.info("Step 1: Predicting bill impact...")
    try:
        predictions_df, summary = predict_bill_impact(
            bill_pdf_path=args.bill,
            master_colleges_path=args.master_colleges,
            models_dir=args.models_dir,
            affected_states=args.affected_states,
            use_box=args.use_box,
            box_folder_id=args.box_folder_id
        )
        
        if predictions_df.empty:
            logger.error("No predictions generated. Exiting.")
            sys.exit(1)
        
        logger.info(f"✓ Generated predictions for {len(predictions_df)} colleges")
        logger.info(f"  Total students impacted: {summary.get('total_students_impacted', 0):,}")
        logger.info(f"  Average tuition change: ${summary.get('average_tuition_change_dollars', 0):,.0f}")
        
    except Exception as e:
        logger.error(f"Error in prediction step: {e}", exc_info=True)
        sys.exit(1)
    
    # Step 2: Export for Tableau
    logger.info("\nStep 2: Exporting for Tableau...")
    try:
        exported_files = export_for_tableau(
            predictions_df,
            summary,
            args.scenario,
            output_base_dir="outputs"
        )
        
        logger.info("✓ Exported files:")
        for file_type, file_path in exported_files.items():
            logger.info(f"  {file_type}: {file_path}")
        
    except Exception as e:
        logger.error(f"Error in export step: {e}", exc_info=True)
        sys.exit(1)
    
    # Step 3: Run CSV analysis (optional)
    if args.run_analysis:
        logger.info("\nStep 3: Running CSV analysis...")
        try:
            from analysis.csv_analyzer import analyze_scenario
            from analysis.custom_metrics import calculate_custom_metrics
            
            # Analyze the predicted impact CSV
            impact_csv = exported_files.get("predicted_impact")
            if impact_csv:
                analysis_results = analyze_scenario(impact_csv, args.scenario)
                logger.info("✓ CSV analysis complete")
                
                # Calculate custom metrics
                custom_metrics = calculate_custom_metrics(
                    predictions_df,
                    f"outputs/analysis/{args.scenario}_custom_metrics.json"
                )
                logger.info("✓ Custom metrics calculated")
        
        except Exception as e:
            logger.warning(f"Error in analysis step: {e}", exc_info=True)
            # Don't exit - analysis is optional
    
    # Step 4: Upload to Box (optional)
    if args.upload_to_box:
        logger.info("\nStep 4: Uploading to Box...")
        try:
            box_client = initialize_box_client()
            if box_client.is_available():
                for file_type, file_path in exported_files.items():
                    if Path(file_path).exists():
                        success = box_client.upload_output_to_box(
                            file_path,
                            args.box_output_folder_id,
                            file_name=Path(file_path).name
                        )
                        if success:
                            logger.info(f"✓ Uploaded {file_type} to Box")
                        else:
                            logger.warning(f"✗ Failed to upload {file_type}")
            else:
                logger.warning("Box client not available. Skipping upload.")
        
        except Exception as e:
            logger.warning(f"Error uploading to Box: {e}", exc_info=True)
            # Don't exit - upload is optional
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("Pipeline Complete!")
    logger.info("="*60)
    logger.info(f"\nScenario: {args.scenario}")
    logger.info(f"Colleges affected: {summary.get('total_colleges_affected', 0)}")
    logger.info(f"Students impacted: {summary.get('total_students_impacted', 0):,}")
    logger.info(f"\nPlain Language Summary:")
    logger.info(summary.get('plain_language_summary', 'N/A'))
    logger.info(f"\nOutput files:")
    for file_type, file_path in exported_files.items():
        logger.info(f"  {file_type}: {file_path}")
    logger.info("\n" + "="*60)


if __name__ == "__main__":
    main()

