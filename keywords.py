from typing import Dict, List

# Maps C++ func name to Java func name.
""" -move(A)
    +A

    -to_string(s)
    +String.valueOf(s)

    ...
"""
func_name: Dict[str, str] = {
    'move': '',
    'to_string': 'String.valueOf',
    'stoi': 'Integer.valueOf',
    'stol': 'Long.valueOf',
    'stoll': 'Long.valueOf',
}

# Maps C++ container to Java interface and implementation.
""" -unordered_set<int> seen;
    +Set<Integer> seen;

    -stack<char> stack;
    +Deque<Character> stack = new ArrayDeque<>();
"""
data_structure: Dict[str, str] = {
    'unordered_set': ('Set', 'HashSet'),
    'set': ('Set', 'TreeSet'),
    'stack': ('Deque', 'ArrayDeque'),
    'queue': ('Queue', 'ArrayDeque'),
}

replaced_end: Dict[str, str] = {
    'constexpr': 'final',
    'const': 'final',
    '1\'000\'000\'007': '1_000_000_007',
    '.top()': '.peek()',
    '.pop(': '.poll(',
    'bool': 'boolean',
    'const string& ': 'final String ',
    'string ': 'String ',
    'string& ': 'String ',
    '.push(': '.offer(',
    '.push_back(': '.add(',
    '.emplace(': '.add(',
    '.pop_front(': '.pollFirst(',
    '.pop_back(': '.pollLast(',
    '.insert(': '.add(',
    '.erase(': '.remove(',
    '.count(': '.contains(',
    '.empty()': '.isEmpty()',
    '.front()': '[0]',
    '.back()': '[n - 1]',
    'min(': 'Math.min(',
    'max(': 'Math.max(',
    'abs(': 'Math.abs(',
    'INT_MIN': 'Integer.MIN_VALUE',
    'INT_MAX': 'Integer.MAX_VALUE',
    'LONG_MIN': 'Long.MIN_VALUE',
    'LONG_MAX': 'Long.MAX_VALUE',
    'LLONG_MIN': 'Long.MIN_VALUE',
    'LLONG_MAX': 'Long.MAX_VALUE',
    'long long': 'long',
    'nullptr': 'null',
}
