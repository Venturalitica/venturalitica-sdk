import ast
import os
from typing import Dict, Any, List, Optional

class ASTCodeScanner:
    """
    Parses Python code to extract semantic context for compliance documentation.
    """
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scans a single Python file for docstrings, imports, and specific calls.
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
            
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {"error": "Syntax Error"}
            
        context = {
            "docstring": ast.get_docstring(tree),
            "imports": [],
            "calls": [],
            "functions": [],
            "raw_source": source
        }
        
        for node in ast.walk(tree):
            # Extract Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    context["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    context["imports"].append(f"{module}.{alias.name}")
                    
            # Extract Function Defs & Docstrings
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "lineno": node.lineno
                }
                context["functions"].append(func_info)
                
            # Extract specific interesting calls (e.g., .fit(), .train())
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # obj.method()
                    method_name = node.func.attr
                    if method_name in ["fit", "train", "log_metric", "log_param"]:
                        # Try to get the object name
                        obj_name = "unknown"
                        if isinstance(node.func.value, ast.Name):
                            obj_name = node.func.value.id
                        
                        context["calls"].append({
                            "object": obj_name,
                            "method": method_name,
                            "lineno": node.lineno
                        })
                        
        return context

    def scan_directory(self, dir_path: str) -> Dict[str, Any]:
        """
        Scans all python files in a directory (non-recursive for now).
        """
        results = {}
        if not os.path.exists(dir_path):
            return results
            
        for file in os.listdir(dir_path):
            if file.endswith(".py") and not file.startswith("."):
                full_path = os.path.join(dir_path, file)
                results[file] = self.scan_file(full_path)
                
        return results
