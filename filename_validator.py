# -*- coding: utf-8 -*-
"""
文件名格式驗證器 - 確保完全符合對外格式要求
Character_{角色編號}_{類型}_{索引}.ext
"""

import re


# Character規則格式：Character_{角色編號}_{類型}_{索引}.ext
# 重點是前面的格式，擴展名可以是任何格式（保留原始擴展名）
CHARACTER_FILENAME_PATTERN = re.compile(
    r'^Character_(\d{2})_(Idle|Intro|Open)_(\d{2})(\.[^.]+)?$',
    re.IGNORECASE
)


def validate_character_filename(filename):
    """
    驗證文件名是否符合Character規則格式
    
    格式要求：Character_{角色編號}_{類型}_{索引}.ext
    重點是前面的格式，擴展名保留原始格式（不強制為.mp4）
    - 角色編號：兩位數字（01-99）
    - 類型：Idle, Intro, Open（大小写敏感）
    - 索引：兩位數字
      - Idle/Intro：01-20
      - Open：00-06（顏色索引）
    - 擴展名：保留原始擴展名（可以是任何格式）
    
    Args:
        filename: 檔案名（不含路徑）
        
    Returns:
        (is_valid, error_message, parsed_data)
        parsed_data: {'char_id': str, 'char_type': str, 'char_index': str, 'ext': str}
    """
    if not filename:
        return False, "檔案名為空", None
    
    # 檢查格式（重點是前面的格式）
    match = CHARACTER_FILENAME_PATTERN.match(filename)
    if not match:
        return False, f"文件名格式不符合要求：應為 Character_XX_Type_XX.ext（重點是前面的格式）", None
    
    char_id, char_type, char_index, ext = match.groups()
    
    # 處理擴展名（如果沒有擴展名，設為空字符串）
    if ext is None:
        ext = ""
    else:
        ext = ext.lower()  # 擴展名轉為小寫
    
    # 驗證類型（大小写敏感）
    valid_types = ['Idle', 'Intro', 'Open']
    if char_type not in valid_types:
        return False, f"類型 '{char_type}' 無效，應為 Idle, Intro 或 Open", None
    
    # 驗證索引範圍（添加異常處理）
    try:
        index_num = int(char_index)
        if char_type in ['Idle', 'Intro']:
            if not (1 <= index_num <= 20):
                return False, f"Idle/Intro 索引應為 01-20，當前為 {char_index}", None
        elif char_type == 'Open':
            if not (0 <= index_num <= 6):
                return False, f"Open 索引應為 00-06，當前為 {char_index}", None
    except (ValueError, TypeError):
        return False, f"索引格式無效: {char_index}", None
    
    # 驗證角色編號範圍（01-99）（添加異常處理）
    try:
        char_id_num = int(char_id)
        if not (1 <= char_id_num <= 99):
            return False, f"角色編號應為 01-99，當前為 {char_id}", None
    except (ValueError, TypeError):
        return False, f"角色編號格式無效: {char_id}", None
    
    parsed_data = {
        'char_id': char_id,
        'char_type': char_type,
        'char_index': char_index,
        'ext': ext
    }
    
    return True, None, parsed_data


def generate_character_filename(char_id, char_type, char_index, ext=''):
    """
    生成符合Character規則的文件名
    
    格式：Character_{角色編號}_{類型}_{索引}.ext
    重點是前面的格式，擴展名保留原始格式（不強制為.mp4）
    
    Args:
        char_id: 角色編號（1-99，會自動補零為兩位）
        char_type: 類型（Idle, Intro, Open）
        char_index: 索引（會自動補零為兩位）
        ext: 擴展名（保留原始格式，如果沒有點會自動添加，如果為空則不添加）
        
    Returns:
        格式化的文件名
    """
    # 確保角色編號為兩位數字
    char_id_str = str(int(char_id)).zfill(2)
    
    # 確保類型正確
    valid_types = ['Idle', 'Intro', 'Open']
    if char_type not in valid_types:
        raise ValueError(f"類型 '{char_type}' 無效，應為 {valid_types}")
    
    # 確保索引為兩位數字
    char_index_str = str(int(char_index)).zfill(2)
    
    # 處理擴展名（保留原始格式，但轉為小寫）
    if ext:
        if not ext.startswith('.'):
            ext = '.' + ext
        ext = ext.lower()
    
    # 生成文件名（重點是前面的格式）
    filename = f"Character_{char_id_str}_{char_type}_{char_index_str}{ext}"
    
    # 驗證生成的文件名（重點是前面的格式）
    is_valid, error, _ = validate_character_filename(filename)
    if not is_valid:
        raise ValueError(f"生成的文件名無效: {error}")
    
    return filename


def ensure_character_format(filename):
    """
    確保文件名符合Character格式（如果不符，嘗試修正）
    
    Args:
        filename: 原始文件名
        
    Returns:
        修正後的文件名
    """
    # 先驗證
    is_valid, error, parsed = validate_character_filename(filename)
    if is_valid:
        return filename
    
    # 如果驗證失敗，嘗試從文件名中提取信息並重新生成
    # 這裡可以添加智能解析邏輯
    return filename

