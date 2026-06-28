import re
from pathlib import Path
from typing import List, Dict, Any, NamedTuple
import yaml

class OKFDocument(NamedTuple):
    concept_id: str
    layer: int
    dependencies: List[str]
    body: str

def parse_okf_file(file_path: Path) -> OKFDocument:
    """Parses a Google Open Knowledge Format (OKF v0.1) Markdown file with YAML frontmatter.
    
    Args:
        file_path: Path to the OKF markdown file.
        
    Returns:
        An OKFDocument dataclass/NamedTuple representation of the parsed file.
        
    Raises:
        ValueError: If frontmatter is missing, malformed, or missing required fields.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Failed to read file: {e}")

    # Regex to extract frontmatter: matches between --- and --- at the start
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        raise ValueError("Missing or malformed frontmatter block delimited by '---'")
        
    frontmatter_str, body = match.groups()
    
    try:
        metadata: Dict[str, Any] = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error in frontmatter: {e}")
        
    if not isinstance(metadata, dict):
        raise ValueError("Frontmatter YAML is not a valid dictionary structure")

    # Required fields
    concept_id = metadata.get("concept_id")
    layer = metadata.get("layer")
    dependencies = metadata.get("dependencies", [])

    if concept_id is None:
        raise ValueError("Missing required field 'concept_id' in frontmatter")
    if layer is None:
        raise ValueError("Missing required field 'layer' in frontmatter")

    try:
        layer_int = int(layer)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid 'layer' value '{layer}': must be an integer")

    if not isinstance(dependencies, list):
        raise ValueError(f"Invalid 'dependencies' value: must be a list of strings")

    # Ensure all dependencies are strings
    dependencies_str: List[str] = [str(d) for d in dependencies]

    return OKFDocument(
        concept_id=str(concept_id),
        layer=layer_int,
        dependencies=dependencies_str,
        body=body
    )

class OKFIndexer:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.documents: Dict[str, OKFDocument] = {}
        self.load_directory()

    def load_directory(self) -> None:
        if not self.directory.exists() or not self.directory.is_dir():
            return
        for file_path in self.directory.glob("*.md"):
            try:
                doc = parse_okf_file(file_path)
                self.documents[doc.concept_id] = doc
            except ValueError:
                # Skip invalid OKF files in the directory
                continue

    def search(self, query: str) -> List[OKFDocument]:
        # Exact match on concept_id
        if query in self.documents:
            return [self.documents[query]]
            
        # Case-insensitive keyword search in concept_id and body
        query_lower = query.lower()
        results = []
        for doc in self.documents.values():
            if query_lower in doc.concept_id.lower() or query_lower in doc.body.lower():
                results.append(doc)
        return results

