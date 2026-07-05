# ReplaceLine Comprehensive Examples

Complete multi-language examples for ReplaceLine tool testing.

## Languages Covered (10 languages)

| Language | Files | Key Features Tested |
|----------|-------|-------------------|
| **Python** | 5 files | Indentation, decorators, f-strings, unicode, blocks |
| **PHP** | 3 files | Mixed HTML/PHP, opening/closing tags, variables |
| **JavaScript** | 3 files | Imports, async/arrow functions, exports, template literals |
| **Java** | 3 files | Package, imports, annotations, generics, methods |
| **Rust** | 1 file | `use`, ownership syntax, `mod` |
| **Go** | 1 file | Package, imports, goroutines, channels |
| **C++** | 1 file | `#include`, templates, `#define`, namespaces |
| **Ruby** | 1 file | `require`, blocks, symbols, `attr_reader` |
| **TypeScript** | 1 file | Type imports, interfaces, generics, decorators |
| **C#** | 1 file | `using`, `async Task`, LINQ, properties |

## Scenarios Per Language

### 1. Beginning of File
- **Python**: Shebang `#!/usr/bin/env python3`
- **PHP**: `<?php` opening tag
- **JS**: `import` statements
- **Java**: `package` and `import`
- **Rust**: `use` statements
- **Go**: `package` and `import`
- **C++**: `#include` headers
- **Ruby**: `require` gems
- **TS**: `import type` statements
- **C#**: `using` directives

### 2. Middle of File
- **Python**: Nested function with 4-space indent
- **PHP**: Line in HTML/PHP mix
- **JS**: Async function → arrow function
- **Java**: Method with `@Override`
- **All**: Single line replacement preserving context

### 3. End of File
- **Python**: `if __name__ == "__main__":` block
- **PHP**: Closing `?>` and HTML footer
- **JS**: `module.exports` with graceful shutdown
- **Java**: Class closing brace

### 4. Multi-Line Block
- **Python**: Entire function/class replacement
- **All**: 5-10 line blocks replaced with new implementation

### 5. Special Characters
- **Python**: Decorators `@staticmethod`, f-strings, emoji
- **PHP**: `$variables`, heredoc
- **JS**: Template literals `` `${expr}` ``
- **Java**: Generics `<T>`, annotations
- **Rust**: Lifetimes `'a`, `&str`
- **All**: Unicode, special symbols

## Edge Cases

| File | Test |
|------|------|
| `test_empty.py` | Empty file handling |
| `test_unicode.py` | CJK, emoji, RTL text |
| `test_xml_chars.py` | `< > &` XML entities |
| `test_long_line.py` | 1000+ character line |

## Directory Structure

```
replace_examples/
├── python/          # 5 files
├── php/             # 3 files
├── js/              # 3 files
├── java/            # 3 files
├── rust/            # 1 file
├── go/              # 1 file
├── cpp/             # 1 file
├── ruby/            # 1 file
├── ts/              # 1 file
├── cs/              # 1 file
├── edge/            # 4 files
├── workflow/        # 1 file
└── README.md        # This file
```

## Usage

```bash
# Run all ReplaceLine examples
python -m replace_examples.run_tests

# Or test specific language
python replace_examples/python/test_python_begin.py
```

## Total: 25+ example files