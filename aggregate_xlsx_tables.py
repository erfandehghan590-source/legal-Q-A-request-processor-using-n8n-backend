import pandas as pd
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def standardize_columns(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    استانداردسازی ستون‌ها: همه سوالات در یک ستون `سوال` و اضافه کردن ستون `سطح`
    
    Args:
        df: DataFrame اصلی
        source_file: نام فایل منبع برای استخراج سطح
    
    Returns:
        DataFrame استاندارد شده
    """
    # استخراج سطح از نام فایل (مثلاً level_1 → 1)
    level_match = pd.Series(source_file).str.extract(r'l[_-]?(\d+)')[0]
    level = int(level_match.iloc[0]) if level_match.notna().any() else None

    # پیدا کردن ستون سوال (سوال سطح ۱، سوال سطح ۲، ...)
    question_cols = [col for col in df.columns if 'سوال سطح' in col]
    if not question_cols:
        logger.warning(f"هیچ ستون سوالی در فایل {source_file} پیدا نشد.")
        return pd.DataFrame()

    # انتخاب اولین ستون سوال (در صورت وجود چندتا)
    question_col = question_cols[0]
    df = df.rename(columns={question_col: 'سوال'})

    # پیدا کردن ستون نحوه رسیدن، ...)
    detail_cols = [col for col in df.columns if 'نحوه رسیدن' in col]
    if not detail_cols:
        logger.warning(f"هیچ ستون توضیحاتی در فایل {source_file} پیدا نشد.")
        return pd.DataFrame()

    # انتخاب اولین ستون نحوه رسیدن (در صورت وجود چندتا)
    detail_col = detail_cols[0]
    df = df.rename(columns={detail_col: 'نحوه رسیدن به پاسخ از ماده قانونی'})

    # حذف ستون‌های سوال اضافی
    for col in question_cols[1:]:
        df = df.drop(columns=col)
    # حذف ستون‌های توضیحات اضافی
    for col in detail_cols[1:]:
        df = df.drop(columns=col)

    # اضافه کردن ستون‌های مشترک
    df['سطح'] = level
    df['Source_File'] = source_file

    # ستون‌های استاندارد
    standard_columns = [
        'ردیف', 'الگو', 'سوال', 'پاسخ', 'مرجع قانون', 'نحوه رسیدن به پاسخ',
        'سطح', 'Source_File', 'نحوه رسیدن به پاسخ از متن ماده'
    ]

    # فقط ستون‌های موجود را نگه دار
    available_cols = [col for col in standard_columns if col in df.columns]
    df = df[available_cols]

    return df

def aggregate_xlsx_files(input_folder="xlsx_output", output_file="aggregated_legal_questions.xlsx"):
    """
    Aggregate all XLSX files into one with unified 'سوال' column.
    """
    try:
        xlsx_files = [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]
        if not xlsx_files:
            logger.error(f"No XLSX files found in '{input_folder}'")
            return False

        logger.info(f"Found {len(xlsx_files)} XLSX files for aggregation")

        standardized_dfs = []

        for xlsx_file in xlsx_files:
            file_path = os.path.join(input_folder, xlsx_file)
            try:
                df = pd.read_excel(file_path)
                if df.empty:
                    logger.warning(f"Empty file: {xlsx_file}")
                    continue

                # استانداردسازی
                df_std = standardize_columns(df, xlsx_file)
                if not df_std.empty:
                    standardized_dfs.append(df_std)
                    logger.info(f"Processed: {xlsx_file} → {len(df_std)} rows")
                else:
                    logger.warning(f"Skipped: {xlsx_file} (no valid data)")

            except Exception as e:
                logger.error(f"Error reading {xlsx_file}: {e}")
                continue

        if not standardized_dfs:
            logger.error("No valid data to aggregate")
            return False

        # ترکیب همه
        combined_df = pd.concat(standardized_dfs, ignore_index=True)

        # مرتب‌سازی اختیاری: بر اساس سطح و ردیف
        if 'سطح' in combined_df.columns and 'ردیف' in combined_df.columns:
            combined_df['ردیف'] = pd.to_numeric(combined_df['ردیف'], errors='coerce')
            combined_df = combined_df.sort_values(['سطح', 'ردیف']).reset_index(drop=True)

        # ذخیره
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            combined_df.to_excel(writer, sheet_name='Legal_Questions', index=False)
            auto_adjust_column_widths(writer.sheets['Legal_Questions'])

        logger.info(f"Single XLSX created: {output_file}")
        logger.info(f"Total rows: {len(combined_df)} | Levels: {sorted(combined_df['سطح'].unique())}")
        return True

    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        return False

def auto_adjust_column_widths(worksheet):
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 60)
        worksheet.column_dimensions[column_letter].width = adjusted_width

def preview_output_file(file_path, num_rows=5):
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Preview: {os.path.basename(file_path)}")
        logger.info(f"Dimensions: {len(df)} rows × {len(df.columns)} columns")
        logger.info("Columns: " + " | ".join(df.columns))
        logger.info(f"Sample (first {num_rows} rows):")
        logger.info(df.head(num_rows)[['سوال', 'سطح', 'الگو']].to_string(index=False))
        logger.info("Level distribution:")
        logger.info(df['سطح'].value_counts().sort_index())
    except Exception as e:
        logger.error(f"Preview failed: {e}")

# Main
if __name__ == "__main__":
    if aggregate_xlsx_files():
        preview_output_file("aggregated_legal_questions.xlsx")