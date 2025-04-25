#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from xml_parser import RepomixXmlParser

def parse_arguments():
    parser = argparse.ArgumentParser(description='Reverse converter for repomix: restores files from XML format')
    parser.add_argument('input_file', help='Path to XML file to process')
    parser.add_argument('-o', '--output-dir', default='output', help='Output directory (default: "output")')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-s', '--structure', help='Save project structure to JSON file')
    parser.add_argument('-m', '--metadata', action='store_true', help='Show project metadata')
    parser.add_argument('-d', '--directory-structure', action='store_true', help='Show directory structure')
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite existing files')
    parser.add_argument('--no-git', action='store_true', help='Do not restore git files')
    parser.add_argument('--keep-empty-dirs', action='store_true', help='Create empty directories from structure')
    return parser.parse_args()

def setup_output_directory(output_dir, force=False):
    if os.path.exists(output_dir):
        if not force and os.listdir(output_dir):
            print(f"Warning: directory {output_dir} is not empty. Use --force to overwrite.")
            return False
    else:
        os.makedirs(output_dir, exist_ok=True)
    return True

def create_empty_directories(directory_structure, output_dir):
    if not directory_structure:
        return 0
    count = 0
    lines = directory_structure.strip().split("\n")
    for line in lines:
        if not line.strip() or "/" not in line:
            continue
        path = line.strip()
        if path.endswith("/"):
            dir_path = os.path.join(output_dir, path)
            os.makedirs(dir_path, exist_ok=True)
            count += 1
    return count

def main():
    args = parse_arguments()
    if not os.path.exists(args.input_file):
        print(f"Error: input file not found: {args.input_file}")
        return 1
    if not setup_output_directory(args.output_dir, args.force):
        return 1
    parser = RepomixXmlParser(args.input_file, args.verbose)
    if not parser.parse():
        print("Error parsing XML file")
        return 1
    if args.metadata:
        print("\nProject metadata:")
        if parser.metadata:
            for key, value in parser.metadata.items():
                print(f"  {key}: {value}")
        else:
            print("  No metadata found")
    if args.directory_structure:
        dir_structure = parser.extract_directory_structure()
        if dir_structure:
            print("\nDirectory structure:")
            print(dir_structure)
        else:
            print("\nNo directory structure found")
    if args.keep_empty_dirs:
        dir_structure = parser.extract_directory_structure()
        if dir_structure:
            dir_count = create_empty_directories(dir_structure, args.output_dir)
            if args.verbose and dir_count > 0:
                print(f"Created empty directories: {dir_count}")
    file_count = parser.extract_files(args.output_dir)
    if args.structure:
        if parser.save_project_structure(args.structure):
            print(f"Project structure saved to {args.structure}")
        else:
            print(f"Error saving project structure")
    print(f"\nProcessing complete. Restored files: {file_count}")
    print(f"Files restored to directory: {args.output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 