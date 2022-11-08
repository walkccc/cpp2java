import unittest
import cpp2java


class CppToJavaTestCase(unittest.TestCase):
  def setUp(self) -> None:
    self.cpp_converter = cpp2java.CppConverter()

  def test_empty_line(self):
    self.assertEqual(self.cpp_converter.to_java(['\n', '']), ['\n', ''])

  def test_struct_to_class(self):
    cpp_lines = [
        'struct T {',
        '  int i;',
        '  int j;',
        '  int val;',
        '  T(int i, int j, int val) : i(i), j(j), val(val) {}',
        '};',
    ]
    java_lines = [
        'class T {',
        '  public int i;',
        '  public int j;',
        '  public int val;',
        '  public T(int i, int j, int val) {\n'
        '    this.i = i;\n'
        '    this.j = j;\n'
        '    this.val = val;\n'
        '  }',
        '}',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_class_constructor(self):
    cpp_lines = ['MyClass(const vector<int>& v1) {']
    java_lines = ['public MyClass(int[] v1) {']
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_container_one_group(self):
    cpp_lines = [
        'unordered_set<int> seen;',
        'set<bool> seen;',
        'stack<long long> stack;',
        'queue<pair<char, long>> q;',
    ]
    java_lines = [
        'Set<Integer> seen = new HashSet<>();',
        'Set<Boolean> seen = new TreeSet<>();',
        'Deque<Long> stack = new ArrayDeque<>();',
        'Queue<Pair<Character, Long>> q = new ArrayDeque<>();',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_container_two_groups(self):
    cpp_lines = [
        'unordered_map<char, int> count;',
        'map<char, int> count;',
    ]
    java_lines = [
        'Map<Character, Integer> count = new HashMap<>();',
        'TreeMap<Character, Integer> count = new TreeMap<>();',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_priority_queue_to_PriorityQueue(self):
    cpp_lines = [
        'priority_queue<pair<int, long>, vector<pair<int, long>>, greater<>> minHeap;',
        'priority_queue<pair<int, int>> maxHeap;',
    ]
    java_lines = [
        'Queue<Pair<Integer, Long>> minHeap = new PriorityQueue<>();',
        'Queue<Pair<Integer, Integer>> maxHeap = new PriorityQueue<>(Collections.reverseOrder());',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_queue_to_ArrayDeque(self):
    cpp_lines = [
        'queue<TreeNode*> q{{root}};',
        'queue<pair<TreeNode*, int>> q{{{root, 1}, {node, 2}}};',
    ]
    java_lines = [
        'Queue<TreeNode> q = new ArrayDeque<>(Arrays.asList(root));',
        'Queue<Pair<TreeNode, Integer>> q = new ArrayDeque<>(Arrays.asList(new Pair<>(root, 1), new Pair<>(node, 2)));',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_vector_to_ArrayList_or_array(self):
    cpp_lines = [
        'vector<int> A;',
        'vector<int> A{1, f(x)};',
        'vector<int> A(1 + B.size());',
        'vector<vector<long long>> A(m + 1, vector<long long>(n + 1));',
    ]
    java_lines = [
        'List<Integer> A = new ArrayList<>();',
        'List<Integer> A = new ArrayList<>(Arrays.asList(1, f(x)));',
        'int[] A = new int[1 + B.size()];',
        'long[][] A = new long[m + 1][n + 1];',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_vector_to_ArrayList_and_initialization(self):
    cpp_lines = [
        'vector<vector<int>> graph(n);',
        'vector<vector<pair<int, long>>> graph(n);',
    ]
    java_lines = [
        'List<Integer>[] graph = new List[n];\n'
        '\n'
        'for (int i = 0; i < n; ++i)\n'
        '  graph[i] = new ArrayList<>();',
        'List<Pair<Integer, Long>>[] graph = new List[n];\n'
        '\n'
        'for (int i = 0; i < n; ++i)\n'
        '  graph[i] = new ArrayList<>();',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_class_var_declaration(self):
    cpp_lines = [
        'UF uf(m * n);',
    ]
    java_lines = [
        'UF uf = new UF(m * n);',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_string_var_declaration(self):
    cpp_lines = [
        'string s;',
    ]
    java_lines = [
        'StringBuilder s = new StringBuilder();',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_func_declaraction(self):
    cpp_lines = [
        'long long myFunc(const string& param1, bool param2) {'
    ]
    java_lines = [
        'public long myFunc(final String param1, boolean param2) {'
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_for_statement(self):
    # TODO: Add range based for loop.
    cpp_lines = [
        'vector<vector<pair<int, long long>>> graph(n);',
        'unordered_map<string, int> count;',
        'for (const vector<int>& edge : edges)',
        'for (const int num : nums)',
        'for (const auto& [v, w] : graph[u])',
        'for (const auto& [key, value] : count)',
        'for (const auto& [_, value] : count)',
        'for (const auto& [key, _] : count)',
    ]
    java_lines = [
        'List<Pair<Integer, Long>>[] graph = new List[n];\n'
        '\n'
        'for (int i = 0; i < n; ++i)\n'
        '  graph[i] = new ArrayList<>();',
        'Map<String, Integer> count = new HashMap<>();',
        'for (int[] edge : edges)',
        'for (final int num : nums)',
        'for (Pair<Integer, Long> pair : graph[u]) {\n'
        '  final int v = pair.getKey();\n'
        '  final long w = pair.getValue();',
        'for (Map.Entry<String, Integer> entry : count.entrySet()) {\n'
        '  final String key = entry.getKey();\n'
        '  final int value = entry.getValue();',
        'for (final int value : count.values())',
        'for (final String key : count.keySet())',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_sort(self):
    cpp_lines = [
        'sort(begin(nums), end(nums));',
        'sort(begin(nums), end(nums), greater<>());',
        'sort(begin(matrix[0]), end(matrix[0]));',
    ]
    java_lines = [
        'Arrays.sort(nums);',
        'Arrays.sort(nums, (a, b) -> b - a);',
        'Arrays.sort(matrix[0]);',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_string_expression(self):
    cpp_lines = [
        's.substr(start, end - start + 1) + s.substr(start)'
    ]
    java_lines = [
        's.substring(start, end) + s.substring(start)'
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_queue_or_stack_peek_then_pop(self):
    cpp_lines = [
        'priority_queue<int> maxHeap;',
        'queue<int> q;',
        'stack<int> stack;',
        'ans += maxHeap.top(), maxHeap.pop();',
        'ans += q.front(), q.pop();',
        'ans += stack.top(), q.pop();',
    ]
    java_lines = [
        'Queue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());',
        'Queue<Integer> q = new ArrayDeque<>();',
        'Deque<Integer> stack = new ArrayDeque<>();',
        'ans += maxHeap.poll();',
        'ans += q.poll();',
        'ans += stack.pop();',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_size_to_length_if_needed(self):
    cpp_lines = [
        'void dfs(vector<vector<int>>& grid) {',
        '  const int m = grid.size();',
        '  const int n = grid[0].size();',
        '}',
    ]
    java_lines = [
        'public void dfs(int[][] grid) {',
        '  final int m = grid.length;',
        '  final int n = grid[0].length;',
        '}',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_remove_pointer(self):
    cpp_lines = [
        'TreeNode* curr = root;',
        'ListNode* node = getNode(root);',
    ]
    java_lines = [
        'TreeNode curr = root;',
        'ListNode node = getNode(root);',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_arrow_operator_to_dot(self):
    cpp_lines = [
        'ListNode* curr = node->next->next;',
        'ListNode* curr = node->next;',
    ]
    java_lines = [
        'ListNode curr = node.next.next;',
        'ListNode curr = node.next;',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_min_or_max_element(self):
    cpp_lines = [
        '*min_element(begin(A), end(A));',
        '*max_element(begin(A), end(A));',
    ]
    java_lines = [
        'Arrays.stream(A).min().getAsInt();',
        'Arrays.stream(A).max().getAsInt();',
    ]
    self.assertEqual(self.cpp_converter.to_java(cpp_lines), java_lines)

  def test_accumulate(self):
    pass

  def test_emplace_back(self):
    pass


if __name__ == '__main__':
  unittest.main()
