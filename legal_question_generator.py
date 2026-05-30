import requests
import json
import os
import time
import logging
import re
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging for standalone use
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """
    Sanitize filename by removing or replacing invalid characters
    """
    invalid_chars = '<>:"/\\|?*\'"'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    filename = filename.replace(' ', '_')
    
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def send_to_n8n_workflow(
    level=1,
    law_content="",
    *,
    law_name=None,
    max_attempts=3,
    connect_timeout=15,
    read_timeout=180,
    backoff_seconds=60
):
    """
    Send request to n8n workflow for generating legal questions with controlled retries.
    """
    webhook_url = f"https://n8n.sokhan.ai/webhook/a89d00c5-21ba-40a9-84c8-b0c78d064458?level={level}"
    label = law_name or "unknown"
    session = requests.Session()
    timeout_config = (connect_timeout, read_timeout)
    headers = {'User-Agent': 'Python-Client'}
    data = {"law_content": law_content} if law_content else None

    try:
        for attempt in range(1, max_attempts + 1):
            logger.info(
                f"Sending request for level {level} ({label}), attempt {attempt}/{max_attempts}..."
            )
            start_time = time.time()

            try:
                if data is not None:
                    response = session.post(
                        webhook_url,
                        json=data,
                        timeout=timeout_config,
                        headers=headers
                    )
                else:
                    response = session.get(
                        webhook_url,
                        timeout=timeout_config,
                        headers=headers
                    )
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                elapsed = time.time() - start_time
                logger.warning(
                    f"Timeout while waiting for level {level} ({label}) after {elapsed:.2f}s"
                )
                response = None
            except requests.exceptions.RequestException as exc:
                elapsed = time.time() - start_time
                logger.error(
                    f"Request error for level {level} ({label}) on attempt {attempt}: {exc} "
                    f"(after {elapsed:.2f}s)"
                )
                response = None

            if response is None:
                if attempt < max_attempts:
                    sleep_for = backoff_seconds * attempt
                    logger.info(
                        f"Retrying level {level} ({label}) in {sleep_for}s (timeout encountered)..."
                    )
                    time.sleep(sleep_for)
                continue

            elapsed_time = time.time() - start_time
            logger.info(
                f"Level {level} ({label}) request completed in {elapsed_time:.2f}s "
                f"with status {response.status_code}"
            )

            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.warning(
                        f"JSON decode failed for level {level} ({label}), returning text response"
                    )
                    return {"output": response.text}

            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(
                    f"Server returned {response.status_code} for level {level} ({label}). "
                    "Will retry if attempts remain."
                )
                if attempt < max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            sleep_for = max(int(retry_after), backoff_seconds * attempt)
                        except ValueError:
                            sleep_for = backoff_seconds * attempt
                    else:
                        sleep_for = backoff_seconds * attempt
                    logger.info(
                        f"Retrying level {level} ({label}) in {sleep_for}s due to server response..."
                    )
                    time.sleep(sleep_for)
                continue

            logger.error(
                f"Received unexpected status {response.status_code} for level {level} ({label}). "
                f"Response preview: {response.text[:500]}..."
            )
            return None

        logger.error(
            f"All attempts exhausted for level {level} ({label}). Skipping this combination."
        )
        return None
    finally:
        session.close()

def save_output_to_file(data, output_folder="output", filename_prefix="legal_questions"):
    """
    Save output data to file with timestamp
    """
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        if data and 'output' in data:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            law_identifier = data.get('law_name', data.get('law_num', 'unknown'))
            law_identifier = sanitize_filename(str(law_identifier))
            filename_prefix = sanitize_filename(filename_prefix)
            level = str(data.get('level', 'unknown'))
            
            base_filename = f"{filename_prefix}_{law_identifier}_l{level}_{timestamp}"
            if len(base_filename) > 50:
                law_identifier_short = law_identifier[:20]
                base_filename = f"{filename_prefix}_{law_identifier_short}_l{level}_{timestamp}"
            
            filename = f"{output_folder}/{base_filename}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(data['output'])
            logger.info(f"Output saved to {filename}")
            return filename
        else:
            logger.warning("No data or output to save")
            return None
            
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        try:
            fallback_filename = f"{output_folder}/legal_l{data.get('level', 'unknown')}_{int(time.time())}.txt"
            with open(fallback_filename, 'w', encoding='utf-8') as f:
                if data and 'output' in data:
                    f.write(data['output'])
                else:
                    f.write("No output data available")
            logger.info(f"Output saved to fallback filename: {fallback_filename}")
            return fallback_filename
        except Exception as e2:
            logger.error(f"Failed to save with fallback filename: {e2}")
            return None

def parse_table_output(output_text):
    """
    Parse table output from n8n response
    """
    if not output_text:
        return None
    
    lines = output_text.strip().split('\n')
    if len(lines) < 3:
        return None
    
    data_rows = []
    for line in lines[2:]:
        line = line.strip()
        if line and '|' in line:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) >= 6:
                data_rows.append({
                    'ردیف': cells[0],
                    'الگو': cells[1],
                    'سوال': cells[2],
                    'پاسخ': cells[3],
                    'مرجع_قانونی': cells[4],
                    'نحوه_رسیدن_به_پاسخ': cells[5]
                })
    
    return data_rows

def main(defined_levels, mode="manual", laws_folder="laws", output_folder="output"):
    """
    Main execution - completely standalone
    
    Args:
        defined_levels (list): List of difficulty levels to generate
        mode (str): Operation mode - 'auto' or 'manual'
        laws_folder (str): Path to folder containing law files
        output_folder (str): Path to folder for saving outputs
    """
    try:
        logger.info("Starting legal questions generation...")
        logger.info(f"Mode: {mode}")
        logger.info(f"Levels: {defined_levels}")
        logger.info(f"Laws folder: {laws_folder}")
        logger.info(f"Output folder: {output_folder}")
        
        defined_law_num = list(range(1, 23))
        start_time = time.time()
        max_total_runtime = 14400  # 4 hours maximum
        
        # Request counter for sleep mechanism
        request_counter = 0
        
        if mode == "auto":
            for law_num in defined_law_num:
                for level in defined_levels:
                    if time.time() - start_time > max_total_runtime:
                        logger.warning("Maximum total runtime exceeded, stopping...")
                        return True
                    
                    logger.info("=" * 20)
                    logger.info(f"Generating level {level} questions for law {law_num}...")
                    logger.info("=" * 20)
                    
                    result = send_to_n8n_workflow(level, "", law_name=f"law_{law_num}")
                    
                    # Increment request counter
                    request_counter += 1
                    
                    if result:
                        result['level'] = level
                        result['law_num'] = law_num   
                        filename = save_output_to_file(result, output_folder, "legal_questions")
                        
                        if 'output' in result:
                            parsed_data = parse_table_output(result['output'])
                            if parsed_data:
                                logger.info(f"Questions generated: {len(parsed_data)}")
                                logger.info(f"Patterns used: {set(row['الگو'] for row in parsed_data)}")
                                
                                logger.info(f"Sample questions level {level} for law {law_num}:")
                                for i, row in enumerate(parsed_data[:2]):
                                    logger.info(f"  {i+1}. {row['سوال'][:100]}...")
                            else:
                                logger.warning("No data parsed from output")
                        else:
                            logger.warning("No output found in result")
                        
                        logger.info(f"Level {level} for law {law_num} completed successfully!")
                    else:
                        logger.error(f"Level {level} for law {law_num} failed!")
                    
                    # Sleep for 2 minutes after every 5 requests
                    if request_counter % 5 == 0:
                        logger.info("⏸️  5 requests completed. Sleeping for 2 minutes to avoid rate limiting...")
                        time.sleep(120)  # 2 minutes
                        logger.info("✅ Resuming operations...")
                    else:
                        # Normal delay between requests
                        time.sleep(2)
            
            logger.info("🎊 Project completed successfully!")
            return True
        
        elif mode == "manual":
            if not os.path.exists(laws_folder):
                logger.error(f"Folder {laws_folder} not found!")
                return False
            
            law_files = [f for f in os.listdir(laws_folder) if f.endswith('.txt')]
            
            if not law_files:
                logger.error(f"No txt files found in {laws_folder} folder!")
                return False
            
            logger.info(f"Law files found: {len(law_files)}")
            
            for law_file in law_files:
                if time.time() - start_time > max_total_runtime:
                    logger.warning("Maximum total runtime exceeded, stopping...")
                    return True
                    
                law_path = os.path.join(laws_folder, law_file)
                law_name = law_file.replace('.txt', '')
                
                try:
                    with open(law_path, 'r', encoding='utf-8') as f:
                        law_content = f.read().strip()
                    
                    logger.info(f"Processing law: {law_name}")
                    logger.info(f"Law content: {law_content[:100]}...")
                    
                    for level in defined_levels:
                        logger.info("=" * 60)
                        logger.info(f"Generating level {level} questions for law {law_name}...")
                        logger.info("=" * 60)
                        
                        result = send_to_n8n_workflow(level, law_content, law_name=law_name)
                        
                        # Increment request counter
                        request_counter += 1
                        
                        if result:
                            result['level'] = level
                            result['law_name'] = law_name
                            filename = save_output_to_file(result, output_folder, f"legal_questions_{law_name}")
                            
                            if 'output' in result:
                                parsed_data = parse_table_output(result['output'])
                                if parsed_data:
                                    logger.info(f"Questions generated: {len(parsed_data)}")
                                    logger.info(f"Patterns used: {set(row['الگو'] for row in parsed_data)}")
                                    
                                    logger.info(f"Sample questions level {level} for law {law_name}:")
                                    for i, row in enumerate(parsed_data[:2]):
                                        logger.info(f"  {i+1}. {row['سوال'][:100]}...")
                                else:
                                    logger.warning("No data parsed from output")
                            else:
                                logger.warning("No output found in result")
                            
                            logger.info(f"Level {level} for law {law_name} completed successfully!")
                        else:
                            logger.error(f"Level {level} for law {law_name} failed!")
                        
                        # Sleep for 2 minutes after every 5 requests
                        if request_counter % 5 == 0:
                            logger.info("⏸️  5 requests completed. Sleeping for 0.5 minute to avoid rate limiting...")
                            time.sleep(30)  # 0.5 minutes
                            logger.info("✅ Resuming operations...")
                        else:
                            # Normal delay between requests
                            time.sleep(2)
                
                except Exception as e:
                    logger.error(f"Error reading file {law_file}: {e}")
            
            logger.info("🎊 Project completed successfully!")
            return True
        
        else:
            logger.error("Execution mode not specified! Use 'auto' or 'manual'.")
            return False
    
    except KeyboardInterrupt:
        logger.info("Program stopped by user!")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return False

