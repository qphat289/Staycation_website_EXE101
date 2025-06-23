import re

def clean_email(email):
    """
    Clean email by removing icons, emojis, and HTML entities
    
    Args:
        email (str): Email address to clean
        
    Returns:
        str: Cleaned email address
    """
    if not email:
        return email
    
    # Pattern để tìm và xóa:
    # - Emoji icons (📧✉️📩📬📭📮🔔🔕💌)
    # - HTML entities (&#123; &amp;)
    # - Other unicode symbols
    patterns_to_remove = [
        r'[📧✉️📩📬📭📮🔔🔕💌🎯🔥⭐️✨🌟💫⚡️🎉🎊🎈]',  # Email và general icons
        r'&#\d+;',  # HTML numeric entities
        r'&[a-zA-Z]+;',  # HTML named entities
        r'[\u2600-\u26FF]',  # Miscellaneous symbols
        r'[\u2700-\u27BF]',  # Dingbats
        r'[\U0001F600-\U0001F64F]',  # Emoticons
        r'[\U0001F300-\U0001F5FF]',  # Symbols & pictographs
        r'[\U0001F680-\U0001F6FF]',  # Transport & map symbols
        r'[\U0001F1E0-\U0001F1FF]',  # Flags
    ]
    
    cleaned_email = email
    
    # Áp dụng tất cả patterns
    for pattern in patterns_to_remove:
        cleaned_email = re.sub(pattern, '', cleaned_email)
    
    # Xóa khoảng trắng thừa
    cleaned_email = cleaned_email.strip()
    
    return cleaned_email

def validate_email_format(email):
    """
    Validate email format
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def process_email(email):
    """
    Process email: clean and validate
    
    Args:
        email (str): Email to process
        
    Returns:
        tuple: (cleaned_email, is_valid)
    """
    if not email:
        return email, False
    
    # Clean email first
    cleaned_email = clean_email(email)
    
    # Validate cleaned email
    is_valid = validate_email_format(cleaned_email)
    
    return cleaned_email, is_valid 