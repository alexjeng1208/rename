# -*- coding: utf-8 -*-
"""
現代化UI主題系統
"""

class ModernTheme:
    """現代化UI主題"""
    
    # 淺色主題配色（Material Design風格）
    LIGHT_THEME = {
        # 主色調
        'primary': '#2196F3',  # 藍色
        'primary_dark': '#1976D2',
        'primary_light': '#BBDEFB',
        
        # 背景色
        'bg_primary': '#FFFFFF',
        'bg_secondary': '#F5F5F5',
        'bg_tertiary': '#FAFAFA',
        
        # 文字顏色
        'text_primary': '#212121',
        'text_secondary': '#757575',
        'text_hint': '#BDBDBD',
        
        # 邊框和分隔線
        'divider': '#E0E0E0',
        'border': '#BDBDBD',
        
        # 狀態顏色
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336',
        'info': '#2196F3',
        
        # 卡片
        'card_bg': '#FFFFFF',
        'card_shadow': '#E0E0E0',
        
        # 按鈕
        'button_bg': '#2196F3',
        'button_hover': '#1976D2',
        'button_text': '#FFFFFF',
        'button_secondary_bg': '#E0E0E0',
        'button_secondary_hover': '#BDBDBD',
        'button_secondary_text': '#212121',
    }
    
    # 深色主題配色
    DARK_THEME = {
        # 主色調
        'primary': '#64B5F6',  # 淺藍色
        'primary_dark': '#42A5F5',
        'primary_light': '#90CAF9',
        
        # 背景色
        'bg_primary': '#121212',
        'bg_secondary': '#1E1E1E',
        'bg_tertiary': '#2D2D2D',
        
        # 文字顏色
        'text_primary': '#FFFFFF',
        'text_secondary': '#B0B0B0',
        'text_hint': '#707070',
        
        # 邊框和分隔線
        'divider': '#3D3D3D',
        'border': '#4D4D4D',
        
        # 狀態顏色
        'success': '#66BB6A',
        'warning': '#FFA726',
        'error': '#EF5350',
        'info': '#42A5F5',
        
        # 卡片
        'card_bg': '#1E1E1E',
        'card_shadow': '#000000',
        
        # 按鈕
        'button_bg': '#42A5F5',
        'button_hover': '#64B5F6',
        'button_text': '#FFFFFF',
        'button_secondary_bg': '#3D3D3D',
        'button_secondary_hover': '#4D4D4D',
        'button_secondary_text': '#FFFFFF',
    }
    
    # 字體配置
    FONTS = {
        'heading': ('Microsoft YaHei UI', 14, 'bold'),
        'subheading': ('Microsoft YaHei UI', 12, 'bold'),
        'body': ('Microsoft YaHei UI', 10),
        'caption': ('Microsoft YaHei UI', 9),
        'button': ('Microsoft YaHei UI', 10, 'bold'),
    }
    
    # 間距配置
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 12,
        'lg': 16,
        'xl': 24,
        'xxl': 32,
    }
    
    # 圓角配置
    RADIUS = {
        'sm': 4,
        'md': 8,
        'lg': 12,
        'xl': 16,
    }
    
    @staticmethod
    def get_theme(is_dark=False):
        """獲取主題配色"""
        return ModernTheme.DARK_THEME if is_dark else ModernTheme.LIGHT_THEME
    
    @staticmethod
    def get_font(font_type='body'):
        """獲取字體配置"""
        return ModernTheme.FONTS.get(font_type, ModernTheme.FONTS['body'])
    
    @staticmethod
    def get_spacing(size='md'):
        """獲取間距"""
        return ModernTheme.SPACING.get(size, ModernTheme.SPACING['md'])
    
    @staticmethod
    def get_radius(size='md'):
        """獲取圓角"""
        return ModernTheme.RADIUS.get(size, ModernTheme.RADIUS['md'])

