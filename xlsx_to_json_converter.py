# -*- coding: utf-8 -*-
"""
XLSX to JSON Converter
Converts Excel files containing legal questions to JSON format

Created on Sun Nov  2 01:34:23 2025
@author: sokhan
"""

import pandas as pd
import json
import os
from pathlib import Path
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# xlsx_to_json_converter.py (فقط بخش تبدیل را جایگزین کنید)

def convert_xlsx_to_json():
    """
    Convert all XLSX files in input folder to JSON format with level and source
    """
    input_folder = "xlsx_output"
    output_folder = "json_output"
    
    Path(output_folder).mkdir(exist_ok=True)
    logger.info(f"Output directory ensured: {output_folder}")
    
    xlsx_files = [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]
    
    if not xlsx_files:
        logger.warning(f"No XLSX files found in directory: {input_folder}")
        return
    
    logger.info(f"Found {len(xlsx_files)} XLSX files for conversion")
    
    for xlsx_file in xlsx_files:
        try:
            file_path = os.path.join(input_folder, xlsx_file)
            df = pd.read_excel(file_path)
            
            logger.info(f"Processing file: {xlsx_file}")
            logger.info(f"DataFrame shape: {len(df)} rows, {len(df.columns)} columns")
            
            # استخراج level از نام فایل (مثلاً level_1)
            level_match = re.search(r'level[_-]?(\d+)', xlsx_file, re.IGNORECASE)
            level = int(level_match.group(1)) if level_match else None
            
            # نرمال‌سازی نام ستون‌ها
            col_map = {
                'سوال سطح 1': 'سوال سطح 1', 'سوال سطح ۲': 'سوال سطح 2',
                'سوال سطح1': 'سوال سطح 1', 'سوال سطح2': 'سوال سطح 2',
                'سوال سطح 1 ': 'سوال سطح 1', 'سوال سطح  1': 'سوال سطح 1'
            }
            df.columns = [col_map.get(col.strip(), col.strip()) for col in df.columns]
            
            # پیدا کردن ستون سوال
            question_cols = [c for c in df.columns if 'سوال سطح' in c]
            if not question_cols:
                logger.warning(f"No question column found in {xlsx_file}")
                continue
            question_col = question_cols[0]
            
            json_data = []
            for index, row in df.iterrows():
                question_txt = str(row[question_col]).strip() if pd.notna(row[question_col]) else ""
                answer_txt = str(row.get('پاسخ', '')).strip() if pd.notna(row.get('پاسخ')) else ""
                
                if not question_txt or not answer_txt:
                    logger.debug(f"Skipped row {index+1}: missing question or answer")
                    continue
                
                question_record = {
                    "question_id": str(row.get('ردیف', f"row_{index+1}")).strip(),
                    "question_txt": question_txt,
                    "correct_answer_txt": answer_txt,
                    "level": level,  # اضافه شد
                    "source_file": xlsx_file,  # اضافه شد
                    "pattern": str(row.get('الگو', '')).strip(),
                    "law_reference": str(row.get('مرجع قانون', '')).strip(),
                    "answer_reasoning": str(row.get('نحوه رسیدن به پاسخ', '')).strip()
                }
                json_data.append(question_record)
            
            # ذخیره JSON
            output_filename = os.path.splitext(xlsx_file)[0] + '.json'
            output_path = os.path.join(output_folder, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Saved {output_filename} with {len(json_data)} questions (Level {level})")
            
        except Exception as e:
            logger.error(f"Error processing {xlsx_file}: {e}")
    
    logger.info("XLSX to JSON conversion completed with level & source info")

def validate_json_files(json_folder="json_output"):
    """
    Validate generated JSON files for structure and content
    
    Args:
        json_folder (str): Path to folder containing JSON files
    
    Returns:
        dict: Validation results summary
    """
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    validation_results = {}
    
    for json_file in json_files:
        try:
            file_path = os.path.join(json_folder, json_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            valid_records = 0
            for record in data:
                if all(key in record for key in ['question_id', 'question_txt', 'correct_answer_txt']):
                    if record['question_txt'] and record['correct_answer_txt']:
                        valid_records += 1
            
            validation_results[json_file] = {
                'total_records': len(data),
                'valid_records': valid_records,
                'valid_structure': valid_records == len(data)
            }
            
            logger.info(f"Validation - {json_file}: {valid_records}/{len(data)} valid records")
            
        except Exception as e:
            logger.error(f"Validation failed for {json_file}: {e}")
            validation_results[json_file] = {'error': str(e)}
    
    return validation_results

# Main execution
if __name__ == "__main__":
    """
    Main execution block for XLSX to JSON conversion
    """
    logger.info("Starting XLSX to JSON conversion process")
    
    try:
        # Perform conversion
        convert_xlsx_to_json()
        
        # Optional: Validate generated JSON files
        logger.info("Starting JSON files validation")
        validation_results = validate_json_files()
        
        # Log validation summary
        valid_files = sum(1 for result in validation_results.values() 
                         if isinstance(result, dict) and result.get('valid_structure', False))
        
        logger.info(f"Validation completed: {valid_files}/{len(validation_results)} files have valid structure")
        
    except Exception as e:
        logger.error(f"Conversion process failed: {e}")
        raise
    
    logger.info("XLSX to JSON conversion pipeline finished successfully")