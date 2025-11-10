# -*- coding: utf-8 -*-
"""
安全工具函數 - 防止路徑遍歷、非法字符等安全問題
"""

import os
import re
from pathlib import Path


# Windows不允許的檔案名字符
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
# Windows保留的檔案名
RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}
# Windows最大路徑長度（260字符，包括驅動器）
MAX_PATH_LENGTH = 260
# Windows最大檔案名長度（255字符）
MAX_FILENAME_LENGTH = 255

# 遊戲引擎文件名標準（只允許字母、數字、下劃線、連字符）
# 大多數遊戲引擎要求：A-Z, a-z, 0-9, _, -
GAME_ENGINE_FILENAME_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')
# 遊戲引擎通常不允許空格
GAME_ENGINE_INVALID_CHARS = re.compile(r'[^A-Za-z0-9_.-]')
# 遊戲引擎文件名長度限制（通常較短，這裡設為128字符）
GAME_ENGINE_MAX_FILENAME_LENGTH = 128


def sanitize_filename(filename, game_engine_mode=False):
    """
    清理檔案名，移除非法字符
    
    Args:
        filename: 原始檔案名
        game_engine_mode: 是否使用遊戲引擎模式（更嚴格）
        
    Returns:
        清理後的檔案名
    """
    if not filename:
        return "unnamed"
    
    # 分離文件名和擴展名
    name_part, ext_part = os.path.splitext(filename)
    
    if game_engine_mode:
        # 遊戲引擎模式：只允許字母、數字、下劃線、連字符
        # 移除所有非字母數字字符（除了下劃線和連字符）
        name_part = re.sub(GAME_ENGINE_INVALID_CHARS, '_', name_part)
        # 移除連續的下劃線和連字符
        name_part = re.sub(r'[_-]+', '_', name_part)
        # 移除前導和尾隨的下劃線、連字符
        name_part = name_part.strip('_-')
        # 確保擴展名小寫（遊戲引擎通常要求）
        ext_part = ext_part.lower()
    else:
        # 標準模式：移除路徑分隔符（防止路徑遍歷）
        name_part = name_part.replace('/', '').replace('\\', '')
        # 移除Windows不允許的字符
        name_part = re.sub(INVALID_FILENAME_CHARS, '_', name_part)
        # 移除前導和尾隨空格、點
        name_part = name_part.strip(' .')
    
    # 檢查是否為保留名稱
    name_upper = name_part.upper()
    if name_upper in RESERVED_NAMES:
        name_part = f"_{name_part}"
    
    # 確保檔案名不為空
    if not name_part or name_part == '.' or name_part == '..':
        name_part = "unnamed"
    
    # 組合文件名和擴展名
    filename = name_part + ext_part
    
    return filename


def validate_game_engine_filename(filename):
    """
    驗證文件名是否符合遊戲引擎標準
    
    Args:
        filename: 檔案名（不含路徑）
        
    Returns:
        (is_valid, error_message)
    """
    if not filename:
        return False, "檔案名為空"
    
    # 分離文件名和擴展名
    name_part, ext_part = os.path.splitext(filename)
    
    # 檢查文件名部分
    if not name_part:
        return False, "檔案名部分為空"
    
    # 檢查是否符合遊戲引擎模式（只允許字母、數字、下劃線、連字符）
    # 注意：點號在文件名部分不允許（只在擴展名中允許）
    if re.search(r'[^A-Za-z0-9_-]', name_part):
        invalid_chars = set(re.findall(r'[^A-Za-z0-9_-]', name_part))
        if invalid_chars:
            return False, f"檔案名包含非法字符: {', '.join(sorted(invalid_chars))}"
    
    # 檢查文件名長度
    if len(name_part) > GAME_ENGINE_MAX_FILENAME_LENGTH:
        return False, f"檔案名過長（超過{GAME_ENGINE_MAX_FILENAME_LENGTH}字符）"
    
    # 檢查完整文件名長度
    if len(filename) > MAX_FILENAME_LENGTH:
        return False, f"完整檔案名過長（超過{MAX_FILENAME_LENGTH}字符）"
    
    # 檢查擴展名
    if ext_part:
        # 擴展名應該小寫
        if ext_part != ext_part.lower():
            return False, "擴展名必須為小寫"
        # 擴展名應該以點開頭
        if not ext_part.startswith('.'):
            return False, "擴展名格式錯誤"
    
    return True, None


def validate_file_path(file_path):
    """
    驗證檔案路徑是否安全
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        (is_valid, error_message)
    """
    if not file_path:
        return False, "路徑為空"
    
    try:
        # 檢查路徑長度
        if len(file_path) > MAX_PATH_LENGTH:
            return False, f"路徑過長（超過{MAX_PATH_LENGTH}字符）"
        
        # 檢查檔案名長度
        filename = os.path.basename(file_path)
        if len(filename) > MAX_FILENAME_LENGTH:
            return False, f"檔案名過長（超過{MAX_FILENAME_LENGTH}字符）"
        
        # 檢查是否包含路徑遍歷（加強檢查）
        normalized_path = os.path.normpath(file_path)
        # 檢查路徑遍歷符號
        if '..' in normalized_path:
            return False, "路徑包含路徑遍歷符號 (..)"
        # 檢查絕對路徑（Unix 風格）
        if normalized_path.startswith('/'):
            return False, "路徑包含非法字符（絕對路徑）"
        # 檢查 Windows 風格的絕對路徑（如 C:\ 或 \\UNC）
        if len(normalized_path) >= 2 and normalized_path[1] == ':':
            # 這是 Windows 絕對路徑，需要進一步驗證
            if not os.path.isabs(file_path):
                # 如果原始路徑不是絕對路徑，但標準化後是，可能有問題
                pass
        # 檢查 UNC 路徑（\\server\share）
        if normalized_path.startswith('\\\\'):
            # UNC 路徑需要特殊處理，這裡暫時拒絕
            return False, "不支援 UNC 路徑"
        
        # 檢查檔案名是否包含非法字符
        if re.search(INVALID_FILENAME_CHARS, filename):
            return False, "檔案名包含非法字符"
        
        return True, None
    except Exception as e:
        return False, f"路徑驗證失敗: {str(e)}"


def safe_join_path(dir_path, filename):
    """
    安全地連接路徑和檔案名，防止路徑遍歷
    
    Args:
        dir_path: 目錄路徑
        filename: 檔案名
        
    Returns:
        完整路徑
    """
    # 清理檔案名
    safe_filename = sanitize_filename(filename)
    
    # 確保目錄路徑是絕對路徑
    if not os.path.isabs(dir_path):
        dir_path = os.path.abspath(dir_path)
    
    # 使用os.path.join連接路徑
    full_path = os.path.join(dir_path, safe_filename)
    
    # 標準化路徑並驗證
    normalized_path = os.path.normpath(full_path)
    
    # 確保結果路徑在目錄內（防止路徑遍歷）
    if not normalized_path.startswith(os.path.abspath(dir_path)):
        raise ValueError("路徑遍歷攻擊檢測：檔案名包含非法路徑字符")
    
    return normalized_path


def validate_and_sanitize_new_filename(original_path, new_name, game_engine_mode=True):
    """
    驗證並清理新檔案名（遊戲引擎模式）
    
    Args:
        original_path: 原始檔案路徑
        new_name: 新檔案名
        game_engine_mode: 是否使用遊戲引擎模式（更嚴格）
        
    Returns:
        (sanitized_name, error_message)
    """
    # 獲取原始檔案的擴展名（確保小寫）
    original_ext = os.path.splitext(original_path)[1].lower()
    
    # 清理檔案名（使用遊戲引擎模式）
    sanitized = sanitize_filename(new_name, game_engine_mode=game_engine_mode)
    
    # 確保新檔案名保留原始擴展名
    name_part, ext_part = os.path.splitext(sanitized)
    if ext_part.lower() != original_ext:
        sanitized = name_part + original_ext
    
    # 驗證文件名是否符合遊戲引擎標準
    if game_engine_mode:
        is_valid, error = validate_game_engine_filename(sanitized)
        if not is_valid:
            return None, f"檔案名不符合遊戲引擎標準: {error}"
    
    # 驗證檔案名長度
    name_part, ext_part = os.path.splitext(sanitized)
    max_name_len = GAME_ENGINE_MAX_FILENAME_LENGTH if game_engine_mode else MAX_FILENAME_LENGTH
    if len(name_part) > max_name_len:
        # 截斷檔案名但保留擴展名
        sanitized = name_part[:max_name_len] + ext_part
    
    # 驗證完整路徑
    dir_path = os.path.dirname(original_path)
    full_path = safe_join_path(dir_path, sanitized)
    
    # 檢查完整路徑長度
    if len(full_path) > MAX_PATH_LENGTH:
        return None, f"完整路徑過長（超過{MAX_PATH_LENGTH}字符）"
    
    return sanitized, None


def safe_rename(old_path, new_path):
    """
    安全地重命名檔案，包含完整的驗證和錯誤處理
    
    Args:
        old_path: 原始檔案路徑
        new_path: 新檔案路徑
        
    Returns:
        (success, error_message)
    """
    try:
        # 驗證原始路徑
        is_valid, error = validate_file_path(old_path)
        if not is_valid:
            return False, f"原始路徑無效: {error}"
        
        # 驗證新路徑
        is_valid, error = validate_file_path(new_path)
        if not is_valid:
            return False, f"新路徑無效: {error}"
        
        # 檢查原始檔案是否存在
        if not os.path.exists(old_path):
            return False, "原始檔案不存在"
        
        # 檢查原始檔案是否為檔案（不是目錄）
        if not os.path.isfile(old_path):
            return False, "原始路徑不是檔案"
        
        # 檢查新路徑是否已存在（且不是同一個檔案）
        # 使用絕對路徑比較，避免符號鏈接問題
        old_abs = os.path.abspath(old_path)
        new_abs = os.path.abspath(new_path)
        
        if old_abs == new_abs:
            # 如果新舊路徑相同，不需要重命名
            return True, None
        
        if os.path.exists(new_path):
            # 目標文件已存在，需要先刪除（原子操作）
            try:
                # 驗證目標文件是文件（不是目錄）
                if not os.path.isfile(new_path):
                    return False, "目標路徑是目錄，不是檔案"
                # 刪除現有文件
                os.remove(new_path)
            except OSError as e:
                return False, f"無法刪除現有目標檔案: {str(e)}"
        
        # 執行重命名（原子操作）
        try:
            os.rename(old_path, new_path)
        except OSError as e:
            # 如果重命名失敗，返回錯誤（不嘗試恢復，因為可能已經刪除目標文件）
            return False, f"重命名失敗: {str(e)}"
        
        # 驗證重命名成功
        if not os.path.exists(new_path):
            return False, "重命名後檔案不存在"
        
        return True, None
    except PermissionError:
        return False, "權限不足，無法重命名檔案"
    except OSError as e:
        return False, f"系統錯誤: {str(e)}"
    except Exception as e:
        return False, f"未知錯誤: {str(e)}"

