import os.path
import re
import sys
from typing import Dict, List, Optional, Tuple

import keywords
import util


class CppConverter:
  def __init__(self):
    self._is_private = False
    self._is_in_class = False
    self._function_block_level = 0
    self._var_to_type: Dict[str, str] = {}

  def _convert_substr_to_substring(self, groups: Tuple[str, str, str]) -> str:
    var, start, end = groups
    tokens = end.split(' ')
    if len(tokens) == 1:
      if start == '0':
        return f'{var}.substring({end})'
      return f'{var}.substring({start}, {start} + {end})'
    if len(tokens) == 5 and tokens[1] == '-' and tokens[2] == start and \
            tokens[3] == '+' and tokens[4] == '1':
      return f'{var}.substring({start}, {tokens[0]})'
    return f'{var}.substring({start}, ???)'

  def _substitute(self, line: str, line_number: int) -> str:
    # If we meet 'private:' keyword, then any method we meet later should be
    # prefixed with 'private '.
    if 'private:' in line:
      self._is_private = True

    for access_modifier in ['public:', 'private:']:
      if access_modifier in line:
        return ''

    ########
    # Stmt #
    ########

    # Converts `struct` to `class`.
    """ -struct T {
        -  int i;
        -  int j;
        -  int val;
        -  T(int i, int j, int val) : i(i), j(j), val(val) {}
        -};
        +class T {
        +  public int i;
        +  public int j;
        +  public int val;
        +  public T(int i, int j, int val) {
        +    this.i = i;
        +    this.j = j;
        +    this.val = val;
        +  }
        +}
    }
    """
    match = re.search(r'^(\s*)struct (\w+) \{$', line)
    if match:
      spaces, class_name = match.groups()
      self._is_in_class = True
      return f'{spaces}class {class_name} ' + '{'
    match = re.search(r'^};$', line)
    if match:
      self._is_in_class = False
      return '}'
    match = re.search(r'^(\s*)(\w+)\((.*)\) : (.+) {}$', line)
    if match:
      spaces, class_name, params, initializer_list = match.groups()
      tokens = util.tokenize(params)
      types = [util.to_java_type(token.rsplit(' ', 1)[0]) for token in tokens]
      names = [token.rsplit(' ', 1)[1] for token in tokens]
      java_params = ', '.join([f'{type} {name}'
                               for type, name in zip(types, names)])
      assignments = [f'{spaces}  this.{name} = {name};' for name in names]
      access_modifier = 'public' if self._is_in_class else '???'
      if java_params:
        return \
            f'{spaces}{access_modifier} {class_name}({java_params}) ' + '{\n' \
            + f'\n'.join(assignments) + f'\n{spaces}' + '}'
    if self._is_in_class:
      match = re.search(r'^(\s*)(.*);$', line)
      if match:
        spaces, var_declaration = match.groups()
        return f'{spaces}public {var_declaration};'

    # Converts class constructor.
    """ -MyClass(const vector<int>& v1) {
        +MyClass(int[] v1) {
    """
    match = re.search(r'^(\s*)(\w+)\((.*)\) {$', line)
    if match:
      spaces, class_name, cpp_params = match.groups()
      access_modifier = 'private' if self._is_private else 'public'
      if cpp_params:
        return f'{spaces}{access_modifier} {class_name}({util.to_java_params(cpp_params)}) ' + '{'
      return line

    ############
    # Var Decl #
    ############

    # Converts C++ container to Java interface and implementation.
    for cpp_container, (java_interface, java_implementation) in keywords.data_structure.items():
      pattern = r'^(\s*)' + cpp_container + r'<(.*)> (\w+);$'
      match = re.search(pattern, line)
      if match:
        spaces, type, var = match.groups()
        object_type = util.to_object_type(type)
        full_type = f'{java_interface}<{object_type}>'
        self._var_to_type[var] = full_type
        return f'{spaces}{full_type} {var} = new {java_implementation}<>();'

    # Converts `std::unordered_map` to `HashMap`.
    """ -unordered_map<char, int> count;
        +Map<Character, Integer> count = new HashMap<>();
    """
    match = re.search(r'^(\s*)unordered_map<([^,]+), (.*)> (\w+);$', line)
    if match:
      spaces, key_type, value_type, var = match.groups()
      object_key_type = util.to_object_type(key_type)
      object_value_type = util.to_object_type(value_type)
      full_type = f'Map<{object_key_type}, {object_value_type}>'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new HashMap<>();'

    # Converts `std::map` to `TreeMap`.
    """ -map<char, int> count;
        +TreeMap<Character, Integer> count = new TreeMap<>();
    """
    match = re.search(r'^(\s*)map<([^,]+), ([^>]+)> (\w+);$', line)
    if match:
      spaces, key_type, value_type, var = match.groups()
      object_key_type = util.to_object_type(key_type)
      object_value_type = util.to_object_type(value_type)
      full_type = f'TreeMap<{object_key_type}, {object_value_type}>'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new TreeMap<>();'

    # Converts `std::priority_queue` minHeap to `PriorityQueue`.
    """ -priority_queue<pair<int, long>, vector<pair<int, long>>, greater<>> minHeap;
        +Queue<Pair<Integer, Long>> minHeap = new PriorityQueue<>();
    """
    match = re.search(
        r'^(\s*)priority_queue<(.*), vector<(?:.*)>, greater<>> (\w+);$',
        line)
    if match:
      spaces, type, var = match.groups()
      object_type = util.to_object_type(type)
      full_type = f'Queue<{object_type}>'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new PriorityQueue<>();'

    # Converts `std::priority_queue` maxHeap to `PriorityQueue`.
    """ -priority_queue<pair<int, int>> maxHeap;
        +Queue<Pair<Integer, Integer>> maxHeap = new PriorityQueue<>(Collections.reverseOrder());'
    """
    match = re.search(r'^(\s*)priority_queue<(.*)> (\w+);$', line)
    if match:
      spaces, type, var = match.groups()
      object_type = util.to_object_type(type)
      full_type = f'Queue<{object_type}>'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new PriorityQueue<>(Collections.reverseOrder());'

    # Converts `std::queue` with initializer list to `ArrayDeque`.
    """ -queue<pair<TreeNode*, int>> q{{{root, 1}, {node, 2}}};
        +Queue<Pair<TreeNode, Integer>> q = new ArrayDeque<>(Arrays.asList(new Pair<>(root, 1), new Pair<>(node, 2)));
    """
    match = re.search(r'^(\s*)queue<(.*)> (\w+){{(.*)}};$', line)
    if match:
      spaces, type, var, initializer_list = match.groups()
      object_type = util.to_object_type(type)
      full_type = f'Queue<{object_type}>'
      self._var_to_type[var] = full_type
      if object_type.startswith('Pair<'):
        java_initializer_list = util.to_java_initializer_list(initializer_list)
        return \
            f'{spaces}{full_type} {var} = new ArrayDeque<>' \
            f'(Arrays.asList({java_initializer_list}));'
      return \
          f'{spaces}{full_type} {var} = new ArrayDeque<>' \
          f'(Arrays.asList({initializer_list}));'

    # Converts 1D `std::vector` to `ArrayList`.
    """ -vector<int> A;
        +List<Integer> A = new ArrayList<>();
    """
    match = re.search(r'^(\s*)vector<([^>]+)> (\w+);$', line)
    if match:
      spaces, type, var = match.groups()
      object_type = util.to_object_type(type)
      full_type = f'List<{object_type}>'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new ArrayList<>();'

    # Converts 1D `std::vector` with initializer list to `ArrayList`.
    """ -vector<int> A{1, f(x)};
        +List<Integer> A = new ArrayList<>(Arrays.asList(1, f(x)));
    """
    match = re.search(r'^(\s*)vector<([^>]+)> (\w+)\{(.*)\};$', line)
    if match:
      spaces, type, var, initializer_list = match.groups()
      object_type = util.to_object_type(type)
      full_type = f'List<{object_type}>'
      self._var_to_type[var] = full_type
      return \
          f'{spaces}{full_type} {var} = new ArrayList<>' \
          f'(Arrays.asList({initializer_list}));'

    # Converts 1D `std::vector` with initialized size to 1D array.
    """ -vector<int> A(1 + B.size());
        +int[] A = new int[1 + B.size()];
    """
    match = re.search(r'^(\s*)vector<([^>]+)> (\w+)\((.*)\);$', line)
    if match:
      spaces, type, var, sz = match.groups()
      java_type = util.to_java_type(type)
      full_type = f'{java_type}[]'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new {java_type}[{sz}];'

    # Converts 2D `std::vector` with initialized sizes to 2D array.
    """ -vector<vector<long long>> A(m + 1, vector<long long>(n + 1));
        +long[][] A = new long[m + 1][n + 1];
    """
    match = re.search(
        r'^(\s*)vector<vector<([^>]+)>> (\w+)\((.+), vector<[^>]+>\((\w+|.*?)\)\);$',
        line)
    if match:
      spaces, type, var, sz1, sz2 = match.groups()
      java_type = util.to_java_type(type)
      full_type = f'{java_type}[][]'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new {java_type}[{sz1}][{sz2}];'

    # Converts 2D `std::vector` with initialized size to 2D array.
    """ -vector<vector<int>> graph(n);
        +List<Integer>[] graph = new List[n];
        +
        +for (int i = 0; i < n; ++i)
        +  graph[i] = new ArrayList<>();
    
        -vector<vector<pair<int, long>>> graph(n);
        +List<Pair<Integer, Long>>[] graph = new List[n];
        +
        +for (int i = 0; i < n; ++i)
        +  graph[i] = new ArrayList<>();
    """
    match = re.search(
        r'^(\s*)vector<vector<(.*)>> (\w+)\((.*)\);$',
        line)
    if match:
      spaces, type, var, sz = match.groups()
      object_type = util.to_object_type(type)
      full_type = f'List<{object_type}>[]'
      self._var_to_type[var] = full_type
      return \
          f'{spaces}{full_type} {var} = new List[{sz}];\n\n' \
          f'{spaces}for (int i = 0; i < {sz}; ++i)\n' \
          f'{spaces}  {var}[i] = new ArrayList<>();'

    # Converts class var declaration.
    """ -UF uf(m * n);
        +UF uf = new UF(m * n);
    """
    match = re.search(r'^(\s*)(\w+) (\w+)\((.*)\);$', line)
    if match:
      spaces, class_name, var, arguments = match.groups()
      return f'{spaces}{class_name} {var} = new {class_name}({arguments});'

    # Converts `std::string` var declaration.
    """ -string s;
        +StringBuilder s = new StringBuilder();
    """
    match = re.search(r'^(\s*)string (\w+);$', line)
    if match:
      spaces, var = match.groups()
      full_type = 'StringBuilder'
      self._var_to_type[var] = full_type
      return f'{spaces}{full_type} {var} = new StringBuilder();'

    # TODO: More work on string concatenation, need to find them semantically.

    #############
    # Func Decl #
    #############

    # Converts function declaration.
    """ -long long myFunc(const string& param1, bool param2) {
        +public long myFunc(final String param1, boolean param2) {
    """
    match = re.search(r'^(\s*)(.*) (\w+)\((.*)\) {$', line)
    if match:
      self._is_in_function = True
      spaces, return_type, func_name, params = match.groups()
      tokens = util.tokenize(params)
      types = [util.to_java_type(token.rsplit(' ', 1)[0]) for token in tokens]
      names = [token.rsplit(' ', 1)[1] for token in tokens]
      java_params = ', '.join([f'{type} {name}'
                               for type, name in zip(types, names)])
      access_modifier = 'private' if self._is_private else 'public'
      java_return_type = util.to_java_type(return_type)
      for type, name in zip(types, names):
        self._var_to_type[name] = type
      return \
          f'{spaces}{access_modifier} ' \
          f'{java_return_type} {func_name}({java_params}) ' + '{'

    # Converts range-based for loop.
    """ -for (const vector<int>& edge : edges)
        +for (int[] edge : edges)
    """
    match = re.search(
        r'^(\s*)for \((.*) (\w+) : (\S+)\)( {)?', line)
    if match:
      spaces, type, var, iterable, left_bracket = match.groups()
      java_type = util.to_java_type(type)
      return \
          f'{spaces}for ({java_type} {var} : {iterable})' \
          f'{left_bracket if left_bracket else ""}'

    # Converts structured binding range-based for loop.
    # Assume
    #
    # var_to_type = {
    #   'graph': 'List<Pair<Integer, Long>>[]',
    #   'count': 'Map<String, Integer>'
    # }
    """ -for (const auto& [v, w] : graph[u])
        +for (Pair<Integer, Long> pair : graph[u]) {
        +  final int v = pair.getKey();
        +  final long w = pair.getValue();

        -for (const auto& [key, value] : count)
        +for (Map.Entry<String, Integer> entry : count.entrySet()) {
        +  final String key = entry.getKey();
        +  final int key = entry.getValue();

        -for (const auto& [_, value] : count)
        +for (final int value : count.values())

        -for (const auto& [key, _] : count)
        +for (final String key : count.keySet())
    """

    match = re.search(
        r'^(\s*)for \((?:const )auto(?:&) \[(\w+), (\w+)\] : ([^)]+)\)( {)?', line)
    if match:
      spaces, key, value, iterable, left_bracket = match.groups()
      var = iterable.split('[')[0]  # 'graph[u]' -> 'graph'
      type: str = self._var_to_type.get(var, 'UNKNOWN_TYPE')

      def get_key_value_types_in_angle_brackets(type: str) -> \
              Optional[Tuple[str, str, str, str]]:
        match = re.search(
            r'(?:List<Pair|Map)<([^,]+), ([^>]+)>', type)
        if not match:
          return None
        key_object_type, value_object_type = match.groups()
        return (util.to_java_type(key_object_type),
                util.to_java_type(value_object_type),
                key_object_type,
                value_object_type)

      types = get_key_value_types_in_angle_brackets(type)
      if not types:
        print(f"Failed to parse '{type}' in line {line_number}: {line}")
        return line
      key_type, value_type, object_key_type, object_value_type = types
      if type.startswith('List<Pair<'):
        return \
            f'{spaces}for (Pair<{object_key_type}, {object_value_type}> ' \
            f'pair : {iterable}) ' + '{\n' \
            f'{spaces}  final {key_type} {key} = pair.getKey();\n' \
            f'{spaces}  final {value_type} {value} = pair.getValue();'
      elif type.startswith('Map<'):
        if key == '_':
          # Don't care about keys -> iterates values.
          return \
              f'{spaces}for (final {value_type} {value} : {iterable}.values())' \
              f'{left_bracket if left_bracket else ""}'
        elif value == '_':
          # Don't care about values -> iterates keys.
          return \
              f'{spaces}for (final {key_type} {key} : {iterable}.keySet())' \
              f'{left_bracket if left_bracket else ""}'
        else:
          # Iterator both values and keys.
          return \
              f'{spaces}for (Map.Entry<{object_key_type}, {object_value_type}> ' \
              f'entry : {iterable}.entrySet()) ' + '{\n' \
              f'{spaces}  final {key_type} {key} = entry.getKey();\n' \
              f'{spaces}  final {value_type} {value} = entry.getValue();'

      print(f"'{type}' not found in line {line_number}: {line}")
      return ''

    # Converts `std::sort` to `Arrays.sort`.
    """ -sort(begin(A), end(A));
        +Arrays.sort(A);
    """
    match = re.search(r'^(\s*)sort\(begin\((\S+)\), end\((?:\S+)\);$', line)
    if match:
      spaces, var = match.groups()
      return f'{spaces}Arrays.sort({var});'

    # Converts `std::sort` to `Arrays.sort` (descendingly).
    """ -sort(begin(A), end(A), greater<>());
        +Arrays.sort(A, (a, b) -> b - a);
    """
    match = re.search(
        r'^(\s*)sort\(begin\((\S+)\), end\((?:\S+), greater<>\(\)\);$', line)
    if match:
      spaces, var = match.groups()
      return f'{spaces}Arrays.sort({var}, (a, b) -> b - a);'

    ########
    # Expr #
    ########

    # Only one group to be captured.
    for cpp_func_name, java_func_name in keywords.func_name.items():
      pattern = cpp_func_name + r'\((\w+|.*?[)\]}"]+)\)'
      line = re.sub(pattern, java_func_name + r'(\1)'
                    if java_func_name else r'\1', line)

    # String
    """ -s.substr(start, end - start + 1)
        +s.substring(start, end)
    """
    line = re.sub(r'(\S+)\.substr\(([^,]+), ([^)]+)\)',
                  lambda m: self._convert_substr_to_substring(m.groups()), line)

    """ -s.substr(start)
        +s.substring(start)
    """
    line = re.sub(r'(\S+)\.substr\(([^)]+)\)', r'\1.substring(\2)', line)

    """ -maxHeap.top(), maxHeap.pop();
        +maxHeap.poll();

        -q.front(), q.pop();
        +q.poll();

        -stack.top(), stack.pop();
        +stack.pop();
    """
    match = re.search(r'(.*?)(\w+)\.(?:top|front)\(\), \w+\.pop\(\);$', line)
    if match:
      anything, var = match.groups()
      type: str = self._var_to_type[var]
      if type.startswith('Queue<'):
        return f'{anything}{var}.poll();'
      if type.startswith('Deque<'):
        return f'{anything}{var}.pop();'
      print(f"'{type}' not found in line {line_number}: {line}")
      return ''

    # Converts .size() to .length if needed
    # Assume
    #
    # var_to_type = {
    #   'A': 'int[]',
    #   'B': 'List<Integer>'
    # }
    """ -A.size()
        +A.length

        -B.size()
        +B.size()
    """
    match = re.search(r'(\S+).size\(\)', line)
    if match:
      name = match.groups()[0]
      var = name.split('[')[0]  # 'grid[0]' -> 'grid'
      type: str = self._var_to_type.get(var, 'UNKNOWN_TYPE')
      if '[]' in type:
        line = re.sub(r'(\S+).size\(\)', f'{name}.length', line)

    """ -ListNode*
        +ListNode
    """
    line = re.sub(r'(\S+)\*', r'\1', line)

    """ -curr->next->next
        +curr.next.next
    """
    line = re.sub(r'(\S+)->(\S+)->(\S+)', r'\1.\2.\3', line)

    """ -curr->next
        +curr.next
    """
    line = re.sub(r'(\S+)->(\S+)', r'\1.\2', line)

    """ -*min_element(begin(A), end(A));
        +Arrays.stream(A).min().getAsInt();

        -*max_element(begin(A), end(A));
        +Arrays.stream(A).max().getAsInt();
    """
    line = re.sub(r'\*(min|max)_element\(begin\((\S+)\), end\((\S+)\)\)',
                  r'Arrays.stream(\2).\1().getAsInt()', line)

    """ -accumulate(begin(A), end(A), 0);
        +Arrays.stream(A).sum();
    """
    line = re.sub(r'accumulate\(begin\((.*)\), end\((\w|.)+\), [^)]*\);',
                  r'Arrays.stream(\1).sum();', line)

    """ -graph[u].emplace_back(v, vals[v]);
        +graph[u].add(new Pair<>(v, vals[v]));
    """
    line = re.sub(r'(\w+)\[(\w+)\]\.emplace_back\(([^,]+), ([^)]+)\);',
                  r'\1[\2].add(new Pair<>(\3, \4));', line)

    for k, v in keywords.replaced_end.items():
      line = line.replace(k, v)

    return line

  def to_java(self, lines: List[str]) -> List[str]:
    return [self._substitute(line, i + 1)
            for i, line in enumerate(lines)]


if __name__ == '__main__':
  if len(sys.argv) != 2:
    sys.exit(-1)

  if not os.path.isfile(sys.argv[1]):
    print('Not a file or directory', sys.argv[1], file=sys.stderr)
    sys.exit(-1)

  in_filename: str = sys.argv[1]  # 'abc123.cpp'
  out_filename: str = in_filename.replace('.cpp', '.java')

  with open(in_filename, 'r', encoding='utf-8') as f:
    cpp_lines = f.readlines()

  java_lines = CppConverter().to_java(cpp_lines)

  with open(out_filename, 'w+', encoding='utf-8') as f:
    for java_line in java_lines:
      if java_line:
        f.write(java_line)
        if java_line[-1] != '\n':
          f.write('\n')

    # f.write(''.join(java_lines))
