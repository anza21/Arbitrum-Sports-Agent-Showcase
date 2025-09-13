#!/usr/bin/env python3
"""
Script to fix all import paths in agent directory
Replaces 'from src.' with 'from agent.src.' in all Python files
"""

import os
import glob

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace all 'from src.' with 'from agent.src.'
        original_content = content
        content = content.replace('from src.', 'from agent.src.')
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all Python files"""
    print("🔧 Starting import path fixes...")
    
    # Find all Python files in agent directory
    patterns = [
        "agent/src/**/*.py",
        "agent/scripts/*.py", 
        "agent/tests/**/*.py"
    ]
    
    python_files = []
    for pattern in patterns:
        python_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates
    python_files = list(set(python_files))
    
    print(f"📁 Found {len(python_files)} Python files to process")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎯 Summary:")
    print(f"   Total files processed: {len(python_files)}")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Files unchanged: {len(python_files) - fixed_count}")
    
    if fixed_count > 0:
        print(f"\n✅ Import paths have been fixed! Please rebuild and restart.")
    else:
        print(f"\n⏭️  No import paths needed fixing.")

if __name__ == "__main__":
    main()
