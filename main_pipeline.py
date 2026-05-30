import os
import sys
import logging
import time
import traceback
import argparse
from pathlib import Path
from importlib import import_module

# Configure logging with both console and file handlers
logger = logging.getLogger(__name__)

def setup_logging(log_level=logging.INFO, log_file='pipeline.log'):
    """
    Set up logging with console and file handlers.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Path to log file (default: 'pipeline.log')
    """
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    logger.info("Logging setup complete. Logs will be written to console and %s", log_file)

class Pack:
    REQUIRED_PACKAGES = ['pandas', 'openpyxl', 'requests', 'python-docx', 'dotenv']

class PipelineConfig:
    """
    Configuration class for pipeline settings.
    Loads required values from .env file, throws error if any required value is missing.
    """
    # Remove defaults for required values
    LAWS_FOLDER = None
    OUTPUT_FOLDER = None
    XLSX_OUTPUT_FOLDER = None
    JSON_OUTPUT_FOLDER = None
    AGGREGATED_FILE = None
    DEFINED_LEVELS = None

    @staticmethod
    def load_config():
        """
        Loads configuration from a .env file into class attributes.
        Throws an error and stops the system if any required value is missing.
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        # List of required configuration keys
        required_keys = [
            'LAWS_FOLDER',
            'OUTPUT_FOLDER', 
            'XLSX_OUTPUT_FOLDER',
            'JSON_OUTPUT_FOLDER',
            'AGGREGATED_FILE',
            'DEFINED_LEVELS'
        ]
        
        missing_keys = []
        
        # Check each required key
        for key in required_keys:
            value = os.getenv(key)
            if value is None or value.strip() == '':
                missing_keys.append(key)
            else:
                # Set the value if it exists
                setattr(PipelineConfig, key, value)
        
        # If any keys are missing, show error and exit
        if missing_keys:
            print(f"❌ ERROR: Missing required configuration in .env file:")
            for key in missing_keys:
                print(f"   - {key}")
            print("\nPlease make sure all required settings are defined in your .env file.")
            sys.exit(1)
        
        # Process DEFINED_LEVELS from string to list of integers
        try:
            levels_str = PipelineConfig.DEFINED_LEVELS
            if levels_str:
                PipelineConfig.DEFINED_LEVELS = [int(level.strip()) for level in levels_str.split(',')]
            else:
                raise ValueError("DEFINED_LEVELS is empty")
        except ValueError as e:
            print(f"❌ ERROR: Invalid format for DEFINED_LEVELS in .env file: {e}")
            print("DEFINED_LEVELS should be comma-separated integers (e.g., '1,2,3')")
            sys.exit(1)

    @staticmethod
    def validate_config():
        """
        Validates the loaded configuration values.
        """
        # Check if folders exist or can be created
        required_folders = [
            PipelineConfig.LAWS_FOLDER,
            PipelineConfig.OUTPUT_FOLDER,
            PipelineConfig.XLSX_OUTPUT_FOLDER,
            PipelineConfig.JSON_OUTPUT_FOLDER
        ]
        
        for folder in required_folders:
            if not folder:
                print(f"❌ ERROR: Folder path is empty: {folder}")
                sys.exit(1)
            
            # Check if folder exists, if not try to create it
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder, exist_ok=True)
                    print(f"✓ Created folder: {folder}")
                except OSError as e:
                    print(f"❌ ERROR: Cannot create folder '{folder}': {e}")
                    sys.exit(1)

def confirm_configuration():
    """
    Display configuration and get user confirmation before running pipeline.
    
    Returns:
        bool: True if user confirms (T), False if user cancels (F)
    """
    logger.info("=" * 60)
    logger.info("🛠️  PIPELINE CONFIGURATION")
    logger.info("=" * 60)
    logger.info(f"Laws folder: {PipelineConfig.LAWS_FOLDER}")
    logger.info(f"Output folder: {PipelineConfig.OUTPUT_FOLDER}")
    logger.info(f"Excel output folder: {PipelineConfig.XLSX_OUTPUT_FOLDER}")
    logger.info(f"JSON output folder: {PipelineConfig.JSON_OUTPUT_FOLDER}")
    logger.info(f"Aggregated file: {PipelineConfig.AGGREGATED_FILE}")
    logger.info(f"Defined levels: {PipelineConfig.DEFINED_LEVELS}")
    logger.info("=" * 60)
    
    while True:
        # input() will print to the console, which is expected for user interaction.
        user_input = input("Start pipeline with these configurations? (T/F): ").strip().upper()
        
        if user_input == 'T':
            logger.info("✅ Configuration confirmed. Starting pipeline...")
            return True
        elif user_input == 'F':
            logger.warning("❌ Configuration rejected. Exiting pipeline.")
            return False
        else:
            logger.warning("❌ Invalid input. Please enter 'T' to continue or 'F' to cancel.")

def check_dependencies(required_packages):
    """
    Check if all required packages are installed using importlib.
    Automatically install missing packages.
    
    Args:
        required_packages (list): List of package names to check.
    
    Returns:
        bool: True if all dependencies are satisfied, False otherwise.
    """
    logger.info("🔍 Checking dependencies...")
    missing_packages = []
    
    # Mapping of package names to their import names
    package_mapping = {
        'python-docx': 'docx'
    }
    
    for package in required_packages:
        import_name = package_mapping.get(package, package)
        try:
            import_module(import_name)
            logger.info(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ {package} is missing")
    
    if missing_packages:
        logger.warning(f"⚠️ Missing packages: {', '.join(missing_packages)}")
        logger.info("🔄 Attempting to install missing packages...")
        
        try:
            import subprocess
            import sys
            
            for package in missing_packages:
                logger.info(f"📦 Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"✅ Successfully installed {package}")
            
            # Verify installation
            logger.info("🔍 Verifying installation...")
            for package in missing_packages:
                import_name = package_mapping.get(package, package)
                import_module(import_name)
                logger.info(f"✓ {package} is now available")
            
            logger.info("✅ All dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install missing packages: {e}")
            logger.info("Please install them manually using: pip install " + " ".join(missing_packages))
            return False
        except ImportError as e:
            logger.error(f"❌ Failed to import after installation: {e}")
            logger.info(f"Note: 'python-docx' is imported as 'docx' in Python code")
            return False
    
    logger.info("✅ All dependencies are satisfied")
    return True

def create_folders(folders):
    """
    Create necessary folders if they don't exist.
    
    Args:
        folders (list): List of folder paths to create.
    """
    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
        logger.info(f"✓ Folder '{folder}' is ready")

def convert_docx_to_txt_in_laws_folder():
    """
    Convert all DOCX files in laws folder to TXT files in the same folder.
    Only converts if TXT file doesn't already exist.
    """
    logger.info("📄 Step 0: Converting DOCX files to TXT in laws folder...")
    
    try:
        from docx_to_txt_converter import DocxToTxtConverter
        
        laws_folder = PipelineConfig.LAWS_FOLDER
        
        # Check if laws folder exists
        if not os.path.exists(laws_folder):
            logger.warning(f"⚠️ Laws folder '{laws_folder}' not found, creating it...")
            Path(laws_folder).mkdir(exist_ok=True)
            return True
        
        # Find all DOCX files in laws folder
        docx_files = list(Path(laws_folder).glob("*.docx"))
        
        if not docx_files:
            logger.info("No DOCX files found in laws folder, skipping conversion")
            return True
        
        converter = DocxToTxtConverter(encoding='utf-8')
        converted_count = 0
        
        for docx_file in docx_files:
            # Check if TXT file already exists
            txt_file = docx_file.with_suffix('.txt')
            
            if txt_file.exists():
                logger.info(f"✓ TXT file already exists: {txt_file.name}")
                continue
            
            # Convert DOCX to TXT
            logger.info(f"🔄 Converting: {docx_file.name} -> {txt_file.name}")
            success = converter.convert_file(str(docx_file), str(txt_file))
            
            if success:
                converted_count += 1
            else:
                logger.error(f"❌ Failed to convert: {docx_file.name}")
        
        logger.info(f"✅ Step 0 completed: Converted {converted_count} DOCX files to TXT")
        return True
        
    except ImportError as ie:
        logger.error(f"❌ DOCX converter module not available: {ie}")
        return False
    except Exception as e:
        logger.error(f"❌ Error in Step 0: {e}")
        logger.debug(traceback.format_exc())
        return False

def run_generator(mode='manual', defined_levels=[1,2,3,4]):
    """
    Run the legal question generator by executing its main function.
    """
    logger.info("🚀 Step 1: Running Legal Question Generator...")
    
    try:
        from legal_question_generator import main as generator_main
        
        # Pass configuration from pipeline to the standalone module
        success = generator_main(
            defined_levels=defined_levels,
            mode=mode,
            laws_folder=PipelineConfig.LAWS_FOLDER,
            output_folder=PipelineConfig.OUTPUT_FOLDER
        )
        
        if success:
            logger.info("✅ Step 1 completed: Legal Question Generator finished")
            return True
        else:
            logger.error("❌ Step 1 failed: Legal Question Generator returned False")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error in Step 1: {e}")
        logger.debug(traceback.format_exc())
        return False

def run_text_to_excel_converter():
    """Convert all text files to Excel format"""
    logger.info("📊 Step 2: Converting text files to Excel...")
    
    try:
        from table_text_to_excel_converter import convert_multiple_files
        convert_multiple_files(input_folder=PipelineConfig.OUTPUT_FOLDER, output_folder=PipelineConfig.XLSX_OUTPUT_FOLDER)
        logger.info("✅ Step 2 completed")
        return True
    except Exception as e:
        logger.error(f"❌ Error in Step 2: {e}")
        logger.debug(traceback.format_exc())
        return False

def run_aggregator(preview_rows=3):
    """Aggregate all Excel files into one"""
    logger.info("🔗 Step 3: Aggregating Excel files...")
    
    try:
        from aggregate_xlsx_tables import aggregate_xlsx_files, preview_output_file
        if aggregate_xlsx_files(input_folder=PipelineConfig.XLSX_OUTPUT_FOLDER, output_file=PipelineConfig.AGGREGATED_FILE):
            preview_output_file(PipelineConfig.AGGREGATED_FILE, num_rows=preview_rows)
            logger.info("✅ Step 3 completed")
            return True
        else:
            logger.error("❌ Aggregation failed")
            return False
    except Exception as e:
        logger.error(f"❌ Error in Step 3: {e}")
        logger.debug(traceback.format_exc())
        return False

def run_json_converter():
    """Convert the final Excel file to JSON"""
    logger.info("📝 Step 4: Converting final Excel to JSON...")
    
    try:
        from xlsx_to_json_converter import convert_xlsx_to_json, validate_json_files
        convert_xlsx_to_json()
        validation_results = validate_json_files(json_folder=PipelineConfig.JSON_OUTPUT_FOLDER)
        valid_files = sum(1 for result in validation_results.values() 
                          if isinstance(result, dict) and result.get('valid_structure', False))
        logger.info(f"✅ Step 4 completed - {valid_files} valid files")
        return True
    except Exception as e:
        logger.error(f"❌ Error in Step 4: {e}")
        logger.debug(traceback.format_exc())
        return False

def main(args):
    """Main pipeline execution"""
    setup_logging(log_level=logging.DEBUG if args.verbose else logging.INFO)
        
    # Check and install dependencies if needed
    if not check_dependencies(Pack.REQUIRED_PACKAGES):
        logger.error("❌ Failed to resolve dependencies. Exiting pipeline.")
        sys.exit(1)
    
    PipelineConfig.load_config()
    
    logger.info("🏁 Starting Legal Questions Pipeline")
    logger.info("=" * 60)

    if not confirm_configuration():
        logger.info("Pipeline cancelled by user")
        sys.exit(1)
    
    # Rest of the function remains the same...
    folders = [
        PipelineConfig.LAWS_FOLDER,
        PipelineConfig.OUTPUT_FOLDER,
        PipelineConfig.XLSX_OUTPUT_FOLDER,
        PipelineConfig.JSON_OUTPUT_FOLDER
    ]
    create_folders(folders)
    
    # Updated pipeline steps with DOCX conversion as Step 0
    pipeline_steps = [
        ("DOCX to TXT Conversion", convert_docx_to_txt_in_laws_folder),
        ("Legal Question Generation", lambda: run_generator(mode=args.mode,defined_levels=PipelineConfig.DEFINED_LEVELS)),
        ("Text to Excel Conversion", run_text_to_excel_converter),
        ("Excel Aggregation", lambda: run_aggregator(preview_rows=args.preview_rows)),
        ("JSON Conversion", run_json_converter)
    ]
    
    successful_steps = 0
    total_steps = len(pipeline_steps)
    
    for step_name, step_function in pipeline_steps:
        logger.info("=" * 60)
        logger.info(f"🔄 Executing: {step_name}")
        logger.info("=" * 60)
        
        start_time = time.time()
        try:
            if step_function():
                successful_steps += 1
                elapsed_time = time.time() - start_time
                logger.info(f"✓ {step_name} completed in {elapsed_time:.2f} seconds")
            else:
                raise RuntimeError(f"{step_name} returned False")
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"✗ {step_name} failed after {elapsed_time:.2f} seconds: {e}")
            logger.debug(traceback.format_exc())
            if args.stop_on_failure:
                logger.info("Stopping pipeline due to failure (stop-on-failure enabled)")
                break
    
    logger.info("=" * 60)
    logger.info("📊 PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Successful steps: {successful_steps}/{total_steps}")
    
    if successful_steps == total_steps:
        logger.info("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
        logger.info("📁 Output files created in:")
        logger.info(f"   - {PipelineConfig.LAWS_FOLDER}/ : Law files (DOCX/TXT)")
        logger.info(f"   - {PipelineConfig.OUTPUT_FOLDER}/ : Generated text files")
        logger.info(f"   - {PipelineConfig.XLSX_OUTPUT_FOLDER}/ : Individual Excel files")
        logger.info(f"   - {PipelineConfig.AGGREGATED_FILE} : Combined Excel file")
        logger.info(f"   - {PipelineConfig.JSON_OUTPUT_FOLDER}/ : JSON files")
    else:
        logger.warning("⚠️ Some steps failed. Check the logs above.")
    
    logger.info("🏁 Pipeline execution finished")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Legal Questions Pipeline")
    parser.add_argument('--mode', choices=['manual', 'auto'], default='manual', help="Mode for question generation (default: manual)")
    parser.add_argument('--stop-on-failure', action='store_true', help="Stop pipeline on first step failure")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose (DEBUG) logging")
    parser.add_argument('--preview-rows', type=int, default=3, help="Number of rows to preview in aggregation (default: 3)")
    
    args = parser.parse_args()
    
    try:
        main(args)
    except KeyboardInterrupt:
        logger.info("⏹️ Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)