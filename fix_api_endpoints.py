#!/usr/bin/env python3
"""
Script to fix all API endpoints in the frontend to include /api prefix
"""

import os
import re

def fix_api_endpoints(file_path):
    """Fix API endpoints in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match fetch calls that don't already have /api
        # Avoid matching URLs that already have /api in them
        pattern = r'fetch\(`\${BACKEND_URL}/(?!api/)([^`]+)`'
        replacement = r'fetch(`${BACKEND_URL}/api/\1`'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Fixed API endpoints in {file_path}")
            return True
        else:
            print(f"ℹ️ No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all frontend files"""
    frontend_dir = "/app/frontend/app/(tabs)"
    
    # Files to fix
    files_to_fix = [
        "ai-assistant.tsx",
        "challenges.tsx", 
        "settings.tsx",
        "properties.tsx"
    ]
    
    fixed_count = 0
    
    for file_name in files_to_fix:
        file_path = os.path.join(frontend_dir, file_name)
        if os.path.exists(file_path):
            if fix_api_endpoints(file_path):
                fixed_count += 1
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"\n🎉 Fixed {fixed_count} files total")

if __name__ == "__main__":
    main()