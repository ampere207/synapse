import re

file_path = "src/components/IntelligenceGraph.tsx"

with open(file_path, 'r') as f:
    content = f.read()

# Fix the GraphEdge interface
content = re.sub(
    r'export interface GraphEdge \{\s*id: string;\s*source: string;\s*target: string;',
    'export interface GraphEdge {\n  id: string;\n  source_node_id: string;\n  target_node_id: string;',
    content
)

with open(file_path, 'w') as f:
    f.write(content)

print("Fixed GraphEdge interface")
