import os
import re

file_path = "/home/aashrith/Dev/synapse/frontend/src/app/workspace/[organizationId]/meeting/[meetingId]/intelligence/page.tsx"

with open(file_path, 'r') as f:
    content = f.read()

# 1. Remove unused imports: ChevronLeft, ChevronRight (keep only Zap)
content = content.replace("import { ChevronLeft, ChevronRight, Zap } from 'lucide-react';", "import { Zap } from 'lucide-react';")

# 4. Add typeof window !== 'undefined' check for localStorage
# Original: const token = localStorage.getItem('token');
content = content.replace(
    "const token = localStorage.getItem('token');",
    "const [token, setToken] = useState<string | null>(null);\n\n  useEffect(() => {\n    if (typeof window !== 'undefined') {\n      setToken(localStorage.getItem('token'));\n    }\n  }, []);"
)

# 2. Change all fetch functions to useCallback
# Add useCallback to React imports if not there
if 'useCallback' not in content:
    content = content.replace("import React, { useEffect, useState } from 'react';", "import React, { useEffect, useState, useCallback } from 'react';")

def wrap_with_usecallback(text, func_name, dependencies):
    start_pattern = rf'const {func_name} = async \(\) => \{{'
    match = re.search(start_pattern, text)
    if not match:
        return text
    
    start_idx = match.start()
    
    brace_count = 0
    end_idx = -1
    for i in range(match.end() - 1, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx != -1:
        func_body = text[match.end():end_idx-1]
        new_func = f"const {func_name} = useCallback(async () => {{{func_body}}}, [{dependencies}]);"
        return text[:start_idx] + new_func + text[end_idx:]
    return text

content = wrap_with_usecallback(content, 'fetchGraphData', 'token, meetingId, API_BASE')
content = wrap_with_usecallback(content, 'fetchEntities', 'token, meetingId, API_BASE')
content = wrap_with_usecallback(content, 'fetchExecutionSummary', 'token, organizationId, API_BASE, entities')
content = wrap_with_usecallback(content, 'fetchSegmentation', 'token, meetingId, API_BASE')
content = wrap_with_usecallback(content, 'triggerExtraction', 'token, meetingId, API_BASE, fetchEntities')

# 3. Fix useEffect dependency array to include all dependencies
content = re.sub(
    r'useEffect\(\(\) => \{(\s+if \(tab === \'graph\'\).+?)\}, \[tab\]\);',
    r'useEffect(() => {\1}, [tab, fetchGraphData, fetchEntities, fetchExecutionSummary, fetchSegmentation]);',
    content,
    flags=re.DOTALL
)

with open(file_path, 'w') as f:
    f.write(content)
