import re
from typing import List


def to_java_params(cpp_params: str) -> str:
  java_params: List[str] = []
  for cpp_param in tokenize(cpp_params):
    cpp_type, name = cpp_param.rsplit(' ', 1)
    java_params.append(f'{to_java_type(cpp_type)} {name}')
  return ', '.join(java_params)


def to_java_initializer_list(initializer_list: str) -> str:
  pairs = initializer_list.split('}, ')
  plain_pairs = [pair.lstrip('{').rstrip('}') for pair in pairs]
  return ', '.join(f"new Pair<>({pair})" for pair in plain_pairs)


def to_object_type(cpp_type: str) -> str:
  if cpp_type == 'char':
    return 'Character'
  if cpp_type == 'bool':
    return 'Boolean'
  if cpp_type == 'int':
    return 'Integer'
  if cpp_type in ('long', 'long long'):
    return 'Long'
  if cpp_type == 'string':
    return 'String'
  if cpp_type.endswith('*'):  # Remove pointer
    return cpp_type.rstrip('*')
  if cpp_type.startswith('pair'):
    match = re.search(r'pair<([^,]+), ([^>]+)>', cpp_type)
    if not match:
      return 'Pair<???, ???>'
    key_type, value_type = match.groups()
    object_key_type = to_object_type(key_type)
    object_value_type = to_object_type(value_type)
    return f'Pair<{object_key_type}, {object_value_type}>'
  return '???'


def to_java_type(type: str) -> str:
  if type == 'const vector<int>&':
    return 'int[]'
  if type == 'const int':
    return 'final int'
  if type == 'long long':
    return 'long'
  if type == 'bool':
    return 'boolean'
  if type in 'string':
    return 'String'
  if type in ('const string', 'const string&'):
    return 'final String'
  if type.startswith('deque<'):
    match = re.match('deque<(.*)>', type)
    sub_object_type = to_object_type(match.group(1))
    return f'Deque<{sub_object_type}>'
  if type.startswith('vector<vector<vector<'):
    match = re.match('vector<vector<vector<(.*)>>>', type)
    sub_java_type = to_java_type(match.group(1))
    return f'{sub_java_type}[][][]'
  if type.startswith('vector<vector<'):
    match = re.match('vector<vector<(.*)>>', type)
    sub_java_type = to_java_type(match.group(1))
    return f'{sub_java_type}[][]'
  if type.startswith('vector<'):
    match = re.match('vector<(.*)>', type)
    sub_java_type = to_java_type(match.group(1))
    return f'{sub_java_type}[]'
  if 'unordered_map' in type:
    match = re.match('(?:const )?unordered_map<(.*), (.*)>', type)
    key_type, value_type = match.groups()
    object_key_type = to_object_type(key_type)
    object_value_type = to_object_type(value_type)
    return f'Map<{object_key_type}, {object_value_type}>'
  if 'unordered_set' in type:
    match = re.match('(?:const )?unordered_set<(.*)>', type)
    java_type = match.groups()[0]
    object_type = to_object_type(java_type)
    return f'Set<{object_type}>'
  if type.endswith('*'):  # Remove pointer
    return f'{to_java_type(type[:-1])}'
  # Type that are same in C++ and Java.
  return type


#    tokenize('vector<vector<pair<int, int>>>, int num')
# -> ['vector<vector<pair<int>>>', 'int num']
def tokenize(cpp_params: str) -> List[str]:
  if not cpp_params:
    return []
  tokens: List[str] = []
  bracket_count = 0
  prev = 0
  for i, c in enumerate(cpp_params):
    if c == '<':
      bracket_count += 1
    elif c == '>':
      bracket_count -= 1
    elif c == ',' and bracket_count == 0:
      tokens.append(cpp_params[prev:i])
      prev = i + 2
  return tokens + [cpp_params[prev:]]
