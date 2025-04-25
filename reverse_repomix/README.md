# Reverse Repomix

A tool to convert XML files created by [Repomix](https://repomix.com) back into the original file structure and directories.

## Description

Repomix is a tool that converts codebases into a single XML file for easier analysis by AI models. This tool performs the reverse conversion: from XML format back to the original file and directory structure.

Supported features:
- Restoration of files and directories from XML
- Support for binary files encoded in base64
- Extraction of project metadata
- Saving project structure in JSON format
- Restoration of file access permissions (for Unix systems)

## Language Support

Reverse Repomix is language-agnostic and supports projects in any programming language, including but not limited to:
- Python
- JavaScript/TypeScript
- Java
- C/C++
- C#
- Go
- Ruby
- PHP
- Rust
- Swift
- Kotlin

The tool works at the file level rather than code level, so it can restore any type of file regardless of content.

## Requirements

- Python 3.6 or higher
- Modules from Python standard library:
  - xml.etree.ElementTree
  - base64
  - os
  - sys
  - json
  - re
  - argparse
  - pathlib

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/reverse_repomix.git
cd reverse_repomix

# Make files executable (for Unix)
chmod +x reverse_repomix.py
```

## Usage

### Basic Usage

```bash
python reverse_repomix.py path/to/file.xml -o output/directory
```

### Command Line Options

```
usage: reverse_repomix.py [-h] [-o OUTPUT_DIR] [-v] [-s STRUCTURE] [-m] [-d] [-f] [--no-git] [--keep-empty-dirs] input_file

Reverse converter for repomix: restores files from XML format

positional arguments:
  input_file            Path to XML file to process

optional arguments:
  -h, --help            Show help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: "output")
  -v, --verbose         Verbose output
  -s STRUCTURE, --structure STRUCTURE
                        Save project structure to JSON file
  -m, --metadata        Show project metadata
  -d, --directory-structure
                        Show directory structure
  -f, --force           Force overwrite existing files
  --no-git              Do not restore git files
  --keep-empty-dirs     Create empty directories from structure
```

### Usage Examples

1. Restore files to "project" directory:
   ```bash
   python reverse_repomix.py repomix-output.xml -o project
   ```

2. Verbose output and save structure to JSON:
   ```bash
   python reverse_repomix.py repomix-output.xml -v -s project_structure.json
   ```

3. Show project metadata without restoring files:
   ```bash
   python reverse_repomix.py repomix-output.xml -m -o /dev/null
   ```

4. Restore with overwriting existing files:
   ```bash
   python reverse_repomix.py repomix-output.xml -o project -f
   ```

5. Restore and create empty directories:
   ```bash
   python reverse_repomix.py repomix-output.xml -o project --keep-empty-dirs
   ```

## XML Format

The tool supports the following input file formats:

1. Repomix XML Format:
   ```xml
   <repomix>
     <file_summary>...</file_summary>
     <directory_structure>...</directory_structure>
     <files>
       <file path="path/to/file">file content</file>
       <!-- Other files -->
     </files>
   </repomix>
   ```

2. Project XML Format:
   ```xml
   <project>
     <metadata>
       <name>Project Name</name>
       <!-- Other metadata -->
     </metadata>
     <files>
       <file path="path/to/file" type="file/type" encoding="utf-8" binary="false">
         file content
       </file>
       <!-- Other files -->
     </files>
   </project>
   ```

3. Text Format with Tags (non-strict XML):
   ```
   This file is a merged representation of the entire codebase...
   
   <file_summary>
   ...
   </file_summary>
   
   <directory_structure>
   src/
     index.js
     utils/
       helper.js
   </directory_structure>
   
   <file path="src/index.js">
   // File content
   </file>
   
   <file path="src/utils/helper.js">
   // File content
   </file>
   ```

## License

This project is distributed under the MIT License. 