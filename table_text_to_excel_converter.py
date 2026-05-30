import pandas as pd
import os
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def convert_text_to_xlsx(input_file_path, output_file_path):
    """
    Convert a text file with table format to XLSX file
    
    Args:
        input_file_path (str): Path to the input text file
        output_file_path (str): Path to the output XLSX file
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    
    try:
        # Read the text file
        with open(input_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Remove empty lines and clean the data
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and '|' in line:
                cleaned_lines.append(line)
        
        if len(cleaned_lines) < 2:
            logger.error("Input file does not have correct format")
            return False
        
        # Extract headers (first line)
        headers_line = cleaned_lines[0]
        # Remove the header separator line (second line)
        data_lines = cleaned_lines[2:]
        
        # Parse headers
        headers = [header.strip() for header in headers_line.split('|')[1:-1]]
        
        # Prepare data for DataFrame
        data_rows = []
        
        for line in data_lines:
            # Split by pipe and remove empty cells at start and end
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            
            # Clean each cell - remove extra spaces and normalize
            cleaned_cells = []
            for cell in cells:
                # Remove multiple spaces and clean the text
                cleaned_cell = re.sub(r'\s+', ' ', cell).strip()
                cleaned_cells.append(cleaned_cell)
            
            if len(cleaned_cells) == len(headers):
                data_rows.append(cleaned_cells)
            else:
                logger.warning(f"Line ignored (column count mismatch): {line}")
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=headers)
        
        # Write to Excel file
        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Legal Questions', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Legal Questions']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Maximum width 50
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"XLSX file created successfully: {output_file_path}")
        logger.info(f"Rows converted: {len(df)} rows")
        logger.info(f"Columns: {len(df.columns)} columns")
        
        return True
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file_path}")
        return False
    except ImportError:
        logger.error("Required libraries not installed. Please run: pip install pandas openpyxl")
        return False
    except Exception as e:
        logger.error(f"Error converting file: {e}")
        return False

def convert_multiple_files(input_folder="output", output_folder="xlsx_output"):
    """
    Convert all text files in input folder to XLSX files in output folder
    
    Args:
        input_folder (str): Folder containing text files
        output_folder (str): Folder to save XLSX files
    """
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logger.info(f"Folder '{output_folder}' created")
    
    # Get all text files in input folder
    text_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
    
    if not text_files:
        logger.error(f"No text files found in folder '{input_folder}'")
        return
    
    logger.info(f"Found {len(text_files)} text files for conversion")
    
    success_count = 0
    for text_file in text_files:
        input_path = os.path.join(input_folder, text_file)
        output_filename = text_file.replace('.txt', '.xlsx')
        output_path = os.path.join(output_folder, output_filename)
        
        logger.info(f"Converting: {text_file}")
        if convert_text_to_xlsx(input_path, output_path):
            success_count += 1
    
    logger.info("=" * 50)
    logger.info("File conversion completed!")
    logger.info(f"Successfully converted {success_count} out of {len(text_files)} files")
    logger.info(f"XLSX files saved in '{output_folder}' folder")

def preview_xlsx_file(xlsx_file_path, num_rows=5):
    """
    Preview the first few rows of an XLSX file
    
    Args:
        xlsx_file_path (str): Path to the XLSX file
        num_rows (int): Number of rows to preview
    """
    try:
        df = pd.read_excel(xlsx_file_path)
        logger.info(f"Preview of file {os.path.basename(xlsx_file_path)}:")
        logger.info("-" * 80)
        logger.info(f"Data dimensions: {len(df)} rows × {len(df.columns)} columns")
        
        logger.info("Columns:")
        for i, col in enumerate(df.columns, 1):
            logger.info(f"  {i}. {col}")
        
        logger.info(f"Sample data (first {num_rows} rows):")
        logger.info(df.head(num_rows).to_string(index=False))
                
    except FileNotFoundError:
        logger.error(f"XLSX file not found: {xlsx_file_path}")
    except Exception as e:
        logger.error(f"Error reading XLSX file: {e}")

def convert_specific_file_with_level(input_file_path, level=None):
    """
    Convert a specific file and add level information
    
    Args:
        input_file_path (str): Path to input text file
        level (int): Level number to include in sheet name
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    if not os.path.exists(input_file_path):
        logger.error(f"Input file not found: {input_file_path}")
        return False
    
    # Determine output path
    output_filename = os.path.basename(input_file_path).replace('.txt', '.xlsx')
    output_folder = "xlsx_output"
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_path = os.path.join(output_folder, output_filename)
    
    # Convert the file
    return convert_text_to_xlsx(input_file_path, output_path)

# Main execution
if __name__ == "__main__":
    logger.info("Text to XLSX Converter")
    logger.info("=" * 50)
    
    # Check if required libraries are installed
    try:
        import pandas as pd
        import openpyxl
        logger.info("Required libraries are installed")
    except ImportError:
        logger.error("Required libraries not installed")
        logger.error("Please run: pip install pandas openpyxl")
        exit()
    
    # Option 1: Convert a specific file
    specific_file = "output/legal_questions_level_1.txt"
    output_xlsx = "legal_questions_level_1.xlsx"
    
    if os.path.exists(specific_file):
        logger.info(f"Converting specific file: {specific_file}")
        if convert_text_to_xlsx(specific_file, output_xlsx):
            preview_xlsx_file(output_xlsx, 3)
    else:
        logger.warning(f"Specific file not found: {specific_file}")
    
    logger.info("=" * 50)
    
    # Option 2: Convert all files in output folder
    logger.info("Converting all files in output folder")
    convert_multiple_files()
    
    logger.info("🎉" * 20)
    logger.info("Program completed successfully!")