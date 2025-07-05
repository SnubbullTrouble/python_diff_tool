import os
import re
import ast
import sys, os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Union

SESSIONDATA_FILE = './sessiondata.py'

class UnusedPropertyError(Exception):
    def __init__(self, message):
        super().__init__(message)

class ConflictingPropertyTypeError(Exception):
    def __init__(self, message):
        super().__init__(message)

def validate_session_variables() -> bool:
    """
    Validates session variables used in the code against the declared
    attributes in the SessionData dataclass.

    - Raises UnusedPropertyError if there are declared attributes that are not used.
    - Raises ConflictingPropertyTypeError if any used attribute has a different type.
    - Appends any missing attributes to the SessionData class with their inferred types.
    - Saves the updated sessiondata.py file.

    Returns:
        bool: If changes were made
    """
    # Step 1: Get existing class lines
    header, values, trailer = get_sessiondata_data()
    reshaped_values: List[Tuple[str, str]] = [
        (line.split(':')[0].strip(), line.split(':')[1].strip())
        for line in values
    ]

    # Step 2: Gather actual usage references from code
    references: List[Tuple[str, str]] = extract_first_two_items(find_sessiondata_attribute_assignments())

    # Step 3: Find unused declared properties
    declared_names = {n for (n, _) in reshaped_values}
    used_names = {n for (n, _) in references}
    unused_values = [pair for pair in reshaped_values if pair[0] not in used_names]

    #if unused_values:
    #    raise UnusedPropertyError(unused_values)

    # Step 4: Check for type conflicts
    conflicting_values = []
    for name, inferred_type in references:
        existing_type = next((t for (n, t) in reshaped_values if n == name), None)
        if existing_type and existing_type != str(inferred_type):
            conflicting_values.append((name, inferred_type))

    if conflicting_values:
        raise ConflictingPropertyTypeError(conflicting_values)

    changed = False

    # Step 5: Append missing references to the value list
    existing_names = {n for (n, _) in reshaped_values}
    for name, val_type in references:
        if name not in existing_names:
            values.append(f"    {name}: {val_type}\n")
            changed = True

    # Step 6: Write back to file
    write_file(header + values + trailer)

    if changed:
        os.execv(sys.executable, [sys.executable] + sys.argv)

def write_file(contents: List[str]) -> None:
    """
    Writes a list of lines to the SESSIONDATA_FILE.

    Args:
        contents (List[str]): The lines to write.
    """
    with open(SESSIONDATA_FILE, 'w', encoding='utf-8') as file:
        file.writelines(contents)
    
def extract_first_two_items(data: Dict[str, List[Tuple[Any, ...]]]) -> List[Tuple[Any, Any]]:
    """
    Extracts the first two items from each list of tuples in the given dictionary,
    and combines them into a single list of tuples.

    Each tuple in the input lists is expected to have multiple elements, but only
    the first two elements of each tuple are retained in the output.

    Args:
        data (dict[str, list[tuple]]): A dictionary where keys are strings and
            values are lists of tuples.

    Returns:
        list[tuple]: A list containing the first two elements of the first two
            tuples from each list in the dictionary.
    """
    result = []
    for entries in data.values():
        for entry in entries:
            # Take only first two elements from each tuple
            result.append(entry[:2])
    return result

def get_sessiondata_data() -> Tuple[List[str], List[str], List[str]]:
    """
    Reads the 'sessiondata.py' file and splits its contents into three parts:
    1. Header lines up to and including the 'class SessionData' declaration line.
    2. Consecutive attribute declaration lines (matching the pattern `name: type`) following the class declaration.
    3. All remaining lines after the attribute declarations (methods, other code, etc.).

    Returns:
        Tuple containing three lists of strings:
        - header_lines: Lines before and including the class declaration.
        - value_lines: Lines declaring data members in the form 'name: type'.
        - trailing_lines: Remaining lines after the attribute declarations.
    """
    # Read the lines
    with open(SESSIONDATA_FILE, 'r') as file:
        session_data_lines = file.readlines()

    # Find the line where the class SessionData is defined
    class_indicator_line = next(
        (i for i, line in enumerate(session_data_lines) if 'class SessionData' in line),
        None
    )
    if class_indicator_line is None:
        raise ValueError("No class named 'SessionData' found.")

    # Header lines: up to and including the class declaration line
    header_lines = session_data_lines[:class_indicator_line + 1]

    # Pattern to match lines like: "    attr_name: attr_type"
    pattern = re.compile(r'^[ \t]*\w+[ \t]*:[ \t]*\w+[ \t]*$')

    # Collect lines after the class declaration that match the pattern
    value_lines = []
    for line in session_data_lines[class_indicator_line + 1:]:
        if pattern.match(line):
            value_lines.append(line)
        else:
            # Stop once a non-matching line is found (end of dataclass attributes)
            break

    # Trailing lines: the rest of the file after the last matched value_line
    if value_lines:
        last_value_index = session_data_lines.index(value_lines[-1])
        trailing_lines = session_data_lines[last_value_index + 1 :]
    else:
        trailing_lines = session_data_lines[class_indicator_line + 1 :]

    return header_lines, value_lines, trailing_lines

def get_value_type_or_value(value_str: str) -> Union[str, type]:
    """
    Attempt to parse a string as a Python literal and return the type name of the parsed value.
    If parsing fails, return the original string stripped of leading and trailing whitespace.

    Args:
        value_str (str): The string representation of the value to evaluate.

    Returns:
        Union[str, type]: The name of the type of the evaluated literal (e.g., 'int', 'str', 'list'), 
                          or the original string if evaluation fails.
    """
    try:
        value = ast.literal_eval(value_str)
        return type(value).__name__
    except Exception:
        return value_str.strip()

def find_sessiondata_attribute_assignments() -> Dict[str, List[Tuple[str, str, str, int]]]:
    """
    Finds all assignments matching the pattern:
        [optional 'self.']<object>.session_data.<attribute> = <value>

    Assumes all values are of type 'str'.

    Returns:
        Dict[str, List[Tuple[str, str, str, int]]]:
            Maps the object name to a list of tuples:
            (attribute name, 'str', filename, line number)
    """
    pattern = re.compile(r'(?:self\.)?(\w+)\.session_data\.(\w+)\s*=\s*.+')
    results: Dict[str, List[Tuple[str, str, str, int]]] = {}

    for filepath in Path('.').glob('*.py'):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for lineno, line in enumerate(lines, 1):
            match = pattern.search(line)
            if match:
                obj_name = match.group(1)    # object name (e.g., 'session')
                attr_name = match.group(2)   # attribute name (e.g., 'app_name')

                if obj_name not in results:
                    results[obj_name] = []
                results[obj_name].append((attr_name, 'str', filepath.name, lineno))

    return results



                        
