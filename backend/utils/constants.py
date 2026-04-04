import re

SUPPORTED_EXTENSIONS = {
    '.zip', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.txt', '.js', '.ts', '.jsx', '.tsx', '.css',
    '.html', '.htm', '.py', '.json', '.xml', '.csv', '.md',
    '.c', '.cpp', '.cs', '.go', '.java', '.rb', '.php',
    '.ppt', '.pptx', '.odt', '.ods', '.odp', '.rtf',
    '.sh', '.bash', '.yaml', '.yml', '.toml',
}

TABULAR_EXTS = {'.xlsx', '.xls', '.csv', '.tsv', '.ods'}

CODE_EXTS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.css',
    '.html', '.htm', '.xml', '.json', '.java',
    '.c', '.cpp', '.cs', '.go', '.rb', '.php',
    '.sh', '.bash', '.yaml', '.yml', '.toml',
}

FILE_EXT_RE = re.compile(
    r'\b([\w\-]+\.(?:xlsx?|csv|tsv|docx?|pptx?|pdf|html?|js|ts|jsx|tsx|'
    r'css|txt|py|json|xml|md|odt|ods|odp|rtf|c|cpp|cs|go|java|rb|php|'
    r'sh|bash|yaml|yml|toml))\b',
    re.IGNORECASE,
)
