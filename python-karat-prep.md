# Karat — Thrilling Teleporters (60 minutes)

---

## Question 1 — Python Output (Mutable Default Argument)

**Score: 5 points**

### Problem

```python
def add(val, lst=[]):
    lst.append(val)
    return lst

print(add(1))
print(add(2))
print(add(3))
```

What is the output?

### Answer

```
[1]
[1, 2]
[1, 2, 3]
```

### Explanation

Python evaluates default argument values **once** at function definition time, not on each call. The list `lst=[]` is created once and reused across all calls. Each `append` mutates the same list object, so successive calls accumulate values.

- `add(1)` → appends `1` → `[1]`
- `add(2)` → appends `2` to the same list → `[1, 2]`
- `add(3)` → appends `3` → `[1, 2, 3]`

**Fix:** Use `None` as the sentinel default:

```python
def add(val, lst=None):
    if lst is None:
        lst = []
    lst.append(val)
    return lst
```

---

## Question 2 — Find the Missing Number

**Score: 30 points**

### Problem

Given an array containing `n` distinct numbers taken from `0, 1, 2, …, n`, one number is missing. Find it.

**Function:** `find_missing_number(arr: list[int]) -> int`

### Solution

```python
def find_missing_number(arr):
    n = len(arr)
    expected_sum = n * (n + 1) // 2
    return expected_sum - sum(arr)
```

### Explanation

The sum of integers `0` through `n` is `n*(n+1)/2`. Subtracting the actual array sum gives the missing number in **O(n)** time and **O(1)** space.

### Examples

```python
find_missing_number([3, 0, 1])      # → 2
find_missing_number([9,6,4,2,3,5,7,0,1])  # → 8
find_missing_number([0])            # → 1
```

---

## Question 3 — Group Anagrams

**Score: 20 points**

### Problem

Given an array of strings, group the anagrams together. Return as a formatted string.

**Function:** `group_anagrams(words: list[str]) -> str`

### Solution

```python
from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)
    for word in words:
        key = tuple(sorted(word))
        groups[key].append(word)
    result = sorted([sorted(g) for g in groups.values()])
    return str(result)
```

### Explanation

- Sort each word's characters to form a canonical key (`"eat"` → `('a','e','t')`).
- Words sharing the same key are anagrams; group them in a `defaultdict`.
- Sort groups for deterministic output.

**Time:** O(N · K log K) where N = number of words, K = max word length.  
**Space:** O(N · K)

### Examples

```python
group_anagrams(["eat","tea","tan","ate","nat","bat"])
# → [['ate', 'eat', 'tea'], ['bat'], ['nat', 'tan']]

group_anagrams([""])
# → [['']]

group_anagrams(["a"])
# → [['a']]
```

---

## Question 4 — Remove Even Numbers from a List

**Score: 30 points**

### Problem

Given a list of integers, remove all even numbers and return only the odd ones.

**Function:** `remove_evens(nums: list[int]) -> list[int]`

### Solution

```python
def remove_evens(nums):
    return [n for n in nums if n % 2 != 0]
```

### Explanation

A single list comprehension filters out every element where `n % 2 == 0`. This runs in **O(n)** time and **O(n)** output space (no in-place mutation needed).

### Examples

```python
remove_evens([1, 2, 3, 4, 5, 6])   # → [1, 3, 5]
remove_evens([2, 4, 6])             # → []
remove_evens([1, 3, 5])             # → [1, 3, 5]
remove_evens([])                    # → []
```

---

## Question 5 — Thrilling Teleporters

**Score: 50 points**

### Problem

The board is tiles `0` through `N` (inclusive). A player on `start_tile` rolls a die with `die_sides` faces (labeled `1 … die_sides`):

1. Move forward by the rolled value; if that exceeds `N`, stop at `N`.
2. If the landed tile has a teleporter `"from,to"`, move to `to` (apply **at most once**).

Return all **distinct** tiles reachable after exactly one roll.

**Function:** `destinations(teleporters, die_sides, start_tile, N) -> list[int]`

### Solution

```python
def destinations(teleporters, die_sides, start_tile, N):
    # Build teleporter map in O(T)
    tele_map = {}
    for t in teleporters:
        f, to = t.split(",")
        tele_map[int(f)] = int(to)

    result = set()
    for roll in range(1, die_sides + 1):
        tile = min(start_tile + roll, N)   # hard cap at N
        tile = tele_map.get(tile, tile)    # single teleport if applicable
        result.add(tile)

    return sorted(result)
```

### Complexity

- **Time:** O(die_sides + T) — build map once in O(T), one pass over rolls in O(die_sides).
- **Space:** O(T) for the teleporter map + O(die_sides) for output in the worst case.

### Walkthrough Example

```
teleporters = ["3,1", "4,2", "5,10"]
die_sides = 6, start_tile = 0, N = 12

Roll | Land | Teleport | Final
  1  |   1  |    no    |   1
  2  |   2  |    no    |   2
  3  |   3  |  → 1     |   1
  4  |   4  |  → 2     |   2
  5  |   5  |  → 10    |  10
  6  |   6  |    no    |   6

Distinct finals (sorted): [1, 2, 6, 10]
```

### Additional Examples

```python
# No teleporters
destinations([], 3, 0, 10)
# rolls land on 1, 2, 3 → [1, 2, 3]

# Cap at N
destinations([], 6, 9, 12)
# rolls: 10, 11, 12, 12, 12, 12 → [10, 11, 12]

# Teleporter loop (no second hop)
destinations(["3,5", "5,7"], 3, 0, 10)
# roll 3 → tile 3 → teleport to 5 (stop, no second hop)
# → [1, 2, 5]
```

---

## Question 6 — Singable Song (Vocal Range)

**Score: 100 points**

### Problem

Notes are strings like `"C5"`, `"A3"`, `"B7"`. Octave dominates pitch; within the same octave, pitch order is `C < D < E < F < G < A < B`.

Given `song` (list of notes), `low`, and `high` (inclusive vocal range), return `True` iff every note in `song` satisfies `low ≤ note ≤ high`.

**Function:** `singable(song, low, high) -> bool`

### Solution

```python
def singable(song, low, high):
    PITCH_ORDER = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}

    def rank(note):
        # note = pitch_letter + octave_digits  e.g. "C5", "B7"
        pitch = note[0]
        octave = int(note[1:])
        return octave * 7 + PITCH_ORDER[pitch]

    low_rank = rank(low)
    high_rank = rank(high)

    for note in song:
        r = rank(note)
        if r < low_rank or r > high_rank:
            return False
    return True
```

### Complexity

- **Time:** O(N) — one pass over the song; `rank()` is O(1).
- **Space:** O(1) — only a fixed-size pitch map and a few integers.

### Key Insight

Map each note to an integer rank in `[0, 55]`:

```
rank(note) = octave * 7 + index(pitch_letter)
```

With 8 octaves (0–7) × 7 letters = 56 distinct ranks: `C0 = 0`, `B7 = 55`.

### Examples

```python
singable(["C4", "F4", "B4"], "C4", "B4")   # → True  (all within range)
singable(["C4", "C5"],       "C4", "B4")   # → False (C5 > B4)
singable(["A3", "G3"],       "C3", "B3")   # → True  (A3 and G3 both in octave 3)
singable(["B3", "C4"],       "C3", "B4")   # → True  (B3 < C4, both in range)
singable([],                 "C0", "B7")   # → True  (empty song)
singable(["C0"],             "C1", "B7")   # → False (C0 below range)
```

---

---

# Karat — Build Your Own Story (60 minutes)

---

## Question 1 — Fix the Out-of-Order Event Counter

**Score: 10 points**

### Problem

Given a stream of events `(id, timestamp)` that may arrive out of order, count how many events are **late** — i.e., their timestamp is strictly less than the maximum timestamp seen so far.

### Broken Implementation

```python
def count_late_events(events):
    max_ts = 0
    late = 0
    for id, ts in events:
        if ts < max_ts:   # BUG: max_ts is never updated
            late += 1
    return late
```

### Fixed Implementation

```python
def count_late_events(events):
    max_ts = 0
    late = 0
    for event_id, ts in events:
        if ts < max_ts:
            late += 1
        else:
            max_ts = ts   # update running maximum
    return late
```

### Explanation

The original code never updates `max_ts`, so every event compares against `0` — it always returns `0`. The fix updates `max_ts` whenever a non-late event arrives (i.e., `ts >= max_ts`).

**Time:** O(N) · **Space:** O(1)

### Examples

```python
events = [(1, 10), (2, 5), (3, 20), (4, 15), (5, 25)]
count_late_events(events)
# ts=10 → max=10; ts=5 < 10 → late; ts=20 → max=20; ts=15 < 20 → late; ts=25 → max=25
# → 2

count_late_events([(1, 1), (2, 2), (3, 3)])  # → 0 (monotonically increasing)
count_late_events([(1, 3), (2, 2), (3, 1)])  # → 2 (all after the first are late)
```

---

## Question 2 — Fix the Concurrent Request Counter

**Score: 10 points**

### Problem

Given requests as `(start, end)` time pairs, return the maximum number of concurrent (overlapping) requests at any point in time.

### Broken Implementation

```python
def max_concurrent(requests):
    events = []
    for start, end in requests:
        events.append((start, 1))
        events.append((end, 1))   # BUG: end should decrement, not increment
    events.sort()
    max_c = cur = 0
    for _, delta in events:
        cur += delta
        max_c = max(max_c, cur)
    return max_c
```

### Fixed Implementation

```python
def max_concurrent(requests):
    events = []
    for start, end in requests:
        events.append((start, 1))    # request starts: +1
        events.append((end, -1))     # request ends:   -1
    # Sort by time; on tie, process ends (-1) before starts (+1) so they don't overlap
    events.sort(key=lambda x: (x[0], x[1]))
    max_c = cur = 0
    for _, delta in events:
        cur += delta
        max_c = max(max_c, cur)
    return max_c
```

### Explanation

The sweep-line technique: mark each start as `+1` and each end as `-1`. Sort all events by time and run a running counter. The maximum value reached is the peak concurrency. The original used `+1` for ends too, so `cur` only grew and never decreased.

**Time:** O(N log N) · **Space:** O(N)

### Examples

```python
max_concurrent([(1, 4), (2, 5), (3, 6)])   # → 3 (all overlap at t=3)
max_concurrent([(1, 2), (3, 4)])            # → 1 (no overlap)
max_concurrent([(1, 10), (2, 3), (4, 5)])  # → 2
```

---

## Question 3 — Fix the LFU Cache Eviction

**Score: 10 points**

### Problem

Implement an **LFU (Least Frequently Used)** cache. On eviction, remove the least frequently used key. On a tie in frequency, remove the least recently used (LRU) among those.

### Broken Implementation

```python
from collections import defaultdict

class LFUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.key_val = {}
        self.key_freq = {}
        self.freq_keys = defaultdict(list)  # BUG: list doesn't preserve LRU order on tie

    def get(self, key):
        if key not in self.key_val:
            return -1
        self.key_freq[key] += 1             # BUG: min_freq not tracked/updated
        return self.key_val[key]

    def put(self, key, value):
        if self.cap == 0:
            return
        if key in self.key_val:
            self.key_val[key] = value
            self.get(key)
            return
        if len(self.key_val) >= self.cap:
            evict = self.freq_keys[min(self.key_freq.values())].pop(0)  # BUG: O(n) pop
            del self.key_val[evict]
            del self.key_freq[evict]
        self.key_val[key] = value
        self.key_freq[key] = 1
        self.freq_keys[1].append(key)
```

### Fixed Implementation

```python
from collections import defaultdict, OrderedDict

class LFUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.key_val = {}                          # key → value
        self.key_freq = {}                         # key → frequency
        self.freq_keys = defaultdict(OrderedDict)  # freq → OrderedDict of keys (LRU order)
        self.min_freq = 0

    def _update_freq(self, key):
        freq = self.key_freq[key]
        del self.freq_keys[freq][key]
        if not self.freq_keys[freq] and freq == self.min_freq:
            self.min_freq += 1
        self.key_freq[key] = freq + 1
        self.freq_keys[freq + 1][key] = None

    def get(self, key):
        if key not in self.key_val:
            return -1
        self._update_freq(key)
        return self.key_val[key]

    def put(self, key, value):
        if self.cap == 0:
            return
        if key in self.key_val:
            self.key_val[key] = value
            self._update_freq(key)
            return
        if len(self.key_val) >= self.cap:
            # Evict LRU among min-frequency keys (first item in OrderedDict)
            evict, _ = self.freq_keys[self.min_freq].popitem(last=False)
            del self.key_val[evict]
            del self.key_freq[evict]
        self.key_val[key] = value
        self.key_freq[key] = 1
        self.freq_keys[1][key] = None
        self.min_freq = 1
```

### Explanation

Key fixes:
- **`OrderedDict` per frequency bucket** — preserves insertion/access order so LRU-among-ties is O(1) via `popitem(last=False)`.
- **`min_freq` tracking** — maintained in `_update_freq`; reset to `1` on every new insert.
- **O(1) eviction** — `popitem(last=False)` on the min-freq bucket is O(1).

**Time:** O(1) per `get`/`put` · **Space:** O(capacity)

### Examples

```python
cache = LFUCache(2)
cache.put(1, 1)
cache.put(2, 2)
cache.get(1)      # → 1  (freq[1]=2, freq[2]=1)
cache.put(3, 3)   # evicts key 2 (LFU, freq=1)
cache.get(2)      # → -1 (evicted)
cache.get(3)      # → 3
cache.put(4, 4)   # evicts key 3 (LFU, freq=1 vs key1 freq=2)
cache.get(1)      # → 1
cache.get(3)      # → -1 (evicted)
cache.get(4)      # → 4
```

---

## Question 4 — Fix the Longest Substring with K Distinct Characters

**Score: 10 points**

### Problem

Given a string `s` and integer `k`, return the length of the longest substring containing **at most `k` distinct characters**.

### Broken Implementation

```python
def longest_k_distinct(s, k):
    counts = {}
    left = max_len = 0
    for right, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        while len(counts) > k:
            left_ch = s[left]
            counts[left_ch] -= 1
            if counts[left_ch] == 0:
                del counts[left_ch]
            # BUG: left never incremented — infinite loop
        max_len = max(max_len, right - left)  # BUG: off-by-one, should be right - left + 1
    return max_len
```

### Fixed Implementation

```python
def longest_k_distinct(s, k):
    if k == 0:
        return 0
    counts = {}
    left = max_len = 0
    for right, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        while len(counts) > k:
            left_ch = s[left]
            counts[left_ch] -= 1
            if counts[left_ch] == 0:
                del counts[left_ch]
            left += 1          # fix: advance left pointer
        max_len = max(max_len, right - left + 1)   # fix: +1 for inclusive length
    return max_len
```

### Explanation

Sliding window: expand `right`, shrink from `left` when distinct count exceeds `k`.
- Bug 1: `left` was never incremented → infinite `while` loop.
- Bug 2: `right - left` gives the window size minus 1; the correct inclusive length is `right - left + 1`.

**Time:** O(N) · **Space:** O(k)

### Examples

```python
longest_k_distinct("eceba", 2)    # → 3  ("ece")
longest_k_distinct("aa", 1)       # → 2  ("aa")
longest_k_distinct("aabbcc", 1)   # → 2  ("aa" or "bb" or "cc")
longest_k_distinct("aabbcc", 2)   # → 4  ("aabb" or "bbcc")
longest_k_distinct("abc", 0)      # → 0
```

---

## Question 5 — Build Your Own Story

**Score: 60 points**

### Problem

A reader starts on page `1` and navigates a choose-your-own-adventure book:

- **endings** — sorted list of page numbers where the story ends (return that page).
- **choices** — list of `[current_page, dest_option1, dest_option2]`; on a choice page, jump to the destination matching `option_to_take`.
- **Otherwise** — move forward to `current_page + 1`.
- **Infinite loop** — if any page is revisited before reaching an ending, return `-1`.

**Function:** `stories(endings, choices, option_to_take) -> int`

### Solution

```python
def stories(endings, choices, option_to_take):
    endings_set = set(endings)
    # Build choice map: page → destination for the chosen option
    choice_map = {}
    for row in choices:
        page, dest1, dest2 = row
        choice_map[page] = dest1 if option_to_take == 1 else dest2

    visited = set()
    page = 1

    while True:
        if page in visited:
            return -1          # infinite loop detected
        visited.add(page)

        if page in endings_set:
            return page        # story ends here

        if page in choice_map:
            page = choice_map[page]   # jump via choice
        else:
            page += 1                 # read forward
```

### Complexity

- **Time:** O(steps + C + E) where C = `len(choices)`, E = `len(endings)`; steps bounded by pages visited before repeat or ending.
- **Space:** O(C + E + steps) for the maps and visited set.

### Walkthrough

```
endings1 = [6, 15, 21, 30]
choices1_1 = [[3, 7, 8], [9, 4, 2]]

stories(endings1, choices1_1, 1):
  1 → 2 → 3 →(choice1)→ 7 → 8 → 9 →(choice1)→ 4 → 5 → 6 (ending) → returns 6

stories(endings1, choices1_1, 2):
  1 → 2 → 3 →(choice2)→ 8 → 9 →(choice2)→ 2 (already visited!) → returns -1
```

### Additional Examples

```python
stories([3], [], 1)               # → 3  (1 → 2 → 3, ending)
stories([5], [[2, 4, 10]], 1)     # → 5  (1 → 2 →(ch1)→ 4 → 5, ending)
stories([5], [[2, 2, 10]], 1)     # → -1 (1 → 2 →(ch1)→ 2, loop)
```

---

## Question 6 — Generalized Sudoku Validator

**Score: 70 points**

### Problem

Validate an N×N grid as a generalized Sudoku. Return `True` iff **all** hold:

1. **N is a perfect square** — `floor(√N)² == N`.
2. **Every row** contains each integer `1…N` exactly once.
3. **Every column** contains each integer `1…N` exactly once.
4. **Every √N × √N sub-box** contains each integer `1…N` exactly once.
5. **Untrusted input** — cells with zero, negatives, values `> N`, or non-integer types (including `bool`) → `False`.

**Function:** `validateSudoku(grid) -> bool`

### Solution

```python
import math

def validateSudoku(grid):
    N = len(grid)
    box_size = int(math.isqrt(N))
    if box_size * box_size != N:
        return False           # N must be a perfect square

    valid_set = set(range(1, N + 1))

    # Validate all cells and collect columns / boxes while checking rows
    cols = [[] for _ in range(N)]
    boxes = [[[] for _ in range(box_size)] for _ in range(box_size)]

    for r, row in enumerate(grid):
        if len(row) != N:
            return False       # ragged row
        for c, v in enumerate(row):
            # Reject booleans explicitly (bool is subclass of int in Python)
            if type(v) is not int or v < 1 or v > N:
                return False
            cols[c].append(v)
            boxes[r // box_size][c // box_size].append(v)
        if set(row) != valid_set or len(row) != N:
            return False       # duplicate or wrong value in row

    for col in cols:
        if set(col) != valid_set:
            return False

    for box_row in boxes:
        for box in box_row:
            if set(box) != valid_set:
                return False

    return True
```

### Complexity

- **Time:** O(N²) — single pass over all cells, then O(N) checks for each of N columns and N boxes.
- **Space:** O(N²) for column/box accumulators (or O(N) if using reusable `seen` sets per pass).

### Key Details

| Check | How |
|-------|-----|
| Perfect square N | `isqrt(N) ** 2 == N` |
| Bool rejection | `type(v) is not int` (since `type(True) is bool`, not `int`) |
| Ragged rows | `len(row) != N` → `False` |
| Row validity | `set(row) == {1…N}` (implicitly checks duplicates + range) |
| Box indexing | `box_row = r // box_size`, `box_col = c // box_size` |

### Examples

```python
# Valid 4x4
validateSudoku([
    [1, 2, 3, 4],
    [3, 4, 1, 2],
    [2, 1, 4, 3],
    [4, 3, 2, 1],
])  # → True

# Invalid: N=2 is not a perfect square
validateSudoku([[1, 2], [2, 1]])  # → False

# Invalid: duplicate in row
validateSudoku([
    [1, 1, 3, 4],
    [3, 4, 1, 2],
    [2, 1, 4, 3],
    [4, 3, 2, 1],
])  # → False

# Invalid: boolean cell
validateSudoku([[True, 2, 3, 4], ...])  # → False

# Invalid: 0 in cell
validateSudoku([[0, 2, 3, 4], ...])     # → False
```

---

---

# Karat — Carpool Camping Trip (60 minutes)

---

## Question 1 — Fix the Distributed Job Scheduler

**Score: 10 points**

### Problem

Given jobs as `(job_id, start_time, duration)`, a worker processes one job at a time. Return the **maximum number of non-overlapping jobs** that can be completed.

### Broken Implementation

```python
def max_jobs(jobs):
    # BUG: sorts by start_time — greedy must sort by end_time
    jobs.sort(key=lambda x: x[1])
    count = 0
    last_end = 0
    for job_id, start, duration in jobs:
        end = start + duration
        if start >= last_end:
            count += 1
            last_end = end
            # BUG: last_end never updated when job is skipped — no else needed,
            # but the sort order is the real bug
    return count
```

### Fixed Implementation

```python
def max_jobs(jobs):
    # Greedy: always pick the job that finishes earliest
    jobs_sorted = sorted(jobs, key=lambda x: x[1] + x[2])  # sort by end_time = start + duration
    count = 0
    last_end = 0
    for job_id, start, duration in jobs_sorted:
        end = start + duration
        if start >= last_end:
            count += 1
            last_end = end
    return count
```

### Explanation

The classic **activity selection** greedy: always pick the job with the earliest finish time among those that start after the last chosen job ends. Sorting by `start_time` is wrong — it can pick long early jobs that block many later ones. Sorting by `end_time = start + duration` is correct.

**Time:** O(N log N) · **Space:** O(N) for the sorted copy

### Examples

```python
jobs = [(1, 0, 3), (2, 1, 1), (3, 3, 2), (4, 5, 1)]
# end times: 3, 2, 5, 6 → sorted: (2,1,1), (1,0,3), (3,3,2), (4,5,1)
# pick (2,1,1) end=2; pick (3,3,2) end=5; pick (4,5,1) end=6 → 3
max_jobs(jobs)  # → 3

max_jobs([(1, 0, 10), (2, 1, 2), (3, 3, 2)])  # → 2 (jobs 2 and 3)
max_jobs([(1, 0, 1), (2, 1, 1), (3, 2, 1)])   # → 3 (no overlap)
```

---

## Question 2 — Fix the API Request Retry Manager

**Score: 10 points**

### Problem

Given API request logs as `(request_id, timestamp, status)`, a failed request should be retried after **5 seconds**. Return all retry timestamps.

### Broken Implementation

```python
def retry_timestamps(logs):
    retries = []
    for request_id, timestamp, status in logs:
        if status == "failed":
            retries.append(timestamp)   # BUG: appends original timestamp, not timestamp + 5
    return retries
```

### Fixed Implementation

```python
def retry_timestamps(logs):
    retries = []
    for request_id, timestamp, status in logs:
        if status == "failed":
            retries.append(timestamp + 5)   # retry 5 seconds after failure
    return retries
```

### Explanation

The fix is straightforward: the retry is scheduled 5 seconds *after* the failure, so the returned timestamp is `timestamp + 5`, not `timestamp`.

**Time:** O(N) · **Space:** O(N)

### Examples

```python
logs = [
    ("req1", 10, "success"),
    ("req2", 20, "failed"),
    ("req3", 25, "failed"),
    ("req4", 30, "success"),
]
retry_timestamps(logs)  # → [25, 30]

retry_timestamps([("r1", 0, "failed")])  # → [5]
retry_timestamps([("r1", 0, "success")]) # → []
```

---

## Question 3 — Fix the Real-Time Leaderboard

**Score: 10 points**

### Problem

Given score updates as `(player_id, score_change)`, return the **player_id with the highest cumulative score**.

### Broken Implementation

```python
def top_player(updates):
    scores = {}
    for player_id, score_change in updates:
        scores[player_id] = score_change   # BUG: overwrites instead of accumulating
    return max(scores, key=scores.get)
```

### Fixed Implementation

```python
def top_player(updates):
    scores = {}
    for player_id, score_change in updates:
        scores[player_id] = scores.get(player_id, 0) + score_change   # accumulate
    return max(scores, key=scores.get)
```

### Explanation

The original assigns `score_change` directly, discarding previous scores for the same player. The fix uses `scores.get(player_id, 0) + score_change` to accumulate all changes.

**Time:** O(N) · **Space:** O(P) where P = number of distinct players

### Examples

```python
updates = [("alice", 10), ("bob", 20), ("alice", 15), ("bob", -5)]
top_player(updates)
# alice: 10+15=25, bob: 20-5=15 → "alice"

top_player([("x", 5), ("y", 5), ("x", 1)])  # → "x" (6 vs 5)
top_player([("a", 100)])                      # → "a"
```

---

## Question 4 — Fix the Message Queue Processor

**Score: 10 points**

### Problem

Given queued messages as `(message_id, priority)`, process higher priority messages first. On equal priority, maintain **insertion order** (FIFO).

### Broken Implementation

```python
import heapq

def process_messages(messages):
    heap = []
    for i, (msg_id, priority) in enumerate(messages):
        heapq.heappush(heap, (priority, msg_id))   # BUG 1: min-heap, should be max-priority first
                                                    # BUG 2: no insertion index → tie order not preserved
    result = []
    while heap:
        _, msg_id = heapq.heappop(heap)
        result.append(msg_id)
    return result
```

### Fixed Implementation

```python
import heapq

def process_messages(messages):
    heap = []
    for i, (msg_id, priority) in enumerate(messages):
        # Negate priority for max-heap; use i as tiebreaker to preserve insertion order
        heapq.heappush(heap, (-priority, i, msg_id))
    result = []
    while heap:
        _, _, msg_id = heapq.heappop(heap)
        result.append(msg_id)
    return result
```

### Explanation

Two bugs:
- **Min-heap vs max-heap:** Python's `heapq` is a min-heap. Negate `priority` to simulate a max-heap (`-priority`).
- **FIFO tie-breaking:** without the insertion index `i`, equal-priority items may pop in undefined order. Including `i` as the second tuple element ensures lower `i` (earlier inserted) is popped first among equals.

**Time:** O(N log N) · **Space:** O(N)

### Examples

```python
messages = [("m1", 3), ("m2", 5), ("m3", 5), ("m4", 1)]
process_messages(messages)
# priority 5: m2 (inserted first), m3; then priority 3: m1; then priority 1: m4
# → ["m2", "m3", "m1", "m4"]

process_messages([("a", 1), ("b", 2), ("c", 1)])  # → ["b", "a", "c"]
```

---

## Question 5 — Shopping by Department

**Score: 40 points**

### Problem

Given a product catalog `[[product_name, department], …]` and an ordered `shopping_list`, return:

> **(visits following the list in order) − (minimum possible visits = distinct departments)**

**Function:** `shopping(products, shopping_list) -> int`

### Solution

```python
def shopping(products, shopping_list):
    # Build product → department map in O(len(products))
    dept_map = {name: dept for name, dept in products}

    # Count ordered visits: 1 + transitions between consecutive different departments
    ordered_visits = 1
    for i in range(1, len(shopping_list)):
        if dept_map[shopping_list[i]] != dept_map[shopping_list[i - 1]]:
            ordered_visits += 1

    # Minimum visits = number of distinct departments on the list
    distinct_depts = len({dept_map[name] for name in shopping_list})

    return ordered_visits - distinct_depts
```

### Complexity

- **Time:** O(len(products) + len(shopping_list)) — one pass to build the map, one pass over the list.
- **Space:** O(len(products)) for the map + O(L) for the distinct-department set.

### Walkthrough

```
Catalog: Blueberries→Produce, Milk→Dairy, Coffee→Pantry, Flour→Pantry, Cheese→Dairy, Carrots→Produce
Shopping list: ["Blueberries", "Milk", "Coffee", "Flour", "Cheese", "Carrots"]

Dept sequence:  Produce → Dairy → Pantry → Pantry → Dairy → Produce
Transitions:           ✓       ✓              ✗       ✓       ✓  = 4 transitions

Ordered visits = 1 + 4 = 5
Distinct depts = {Produce, Dairy, Pantry} = 3

Answer: 5 - 3 = 2
```

### Additional Examples

```python
products = [["Milk", "Dairy"], ["Eggs", "Dairy"], ["Bread", "Bakery"]]

shopping(products, ["Milk", "Eggs", "Bread"])
# Dairy → Dairy → Bakery: visits=2, distinct=2 → 0

shopping(products, ["Milk", "Bread", "Eggs"])
# Dairy → Bakery → Dairy: visits=3, distinct=2 → 1

shopping(products, ["Milk"])
# visits=1, distinct=1 → 0
```

---

## Question 6 — Carpool to Campground

**Score: 60 points**

### Problem

Two cars start simultaneously from `starts[0]` and `starts[1]`. Roads are a directed linear DAG (no branches, no loops). Each car walks its unique path toward Campground, picking up people at their home locations. The first car to arrive at a home picks up that person; on a tie, the car with the lower index in `starts` wins.

**Function:** `carpool(roads, starts, people) -> list[list[str]]`

### Solution

```python
from collections import defaultdict

def carpool(roads, starts, people):
    # Build adjacency map: origin → (destination, duration)
    adj = {}
    for origin, destination, duration in roads:
        adj[origin] = (destination, int(duration))

    def path_times(start):
        """Walk the linear path from start, return {location: arrival_time}."""
        times = {}
        location = start
        t = 0
        while location is not None:
            times[location] = t
            if location in adj:
                dest, dur = adj[location]
                t += dur
                location = dest
            else:
                break
        return times

    times0 = path_times(starts[0])
    times1 = path_times(starts[1])

    passengers = [[], []]

    for name, home in people:
        t0 = times0.get(home)
        t1 = times1.get(home)

        if t0 is None and t1 is None:
            continue   # not reachable by either car
        elif t0 is None:
            passengers[1].append((t1, name))
        elif t1 is None:
            passengers[0].append((t0, name))
        elif t0 <= t1:
            passengers[0].append((t0, name))   # car 0 wins on tie
        else:
            passengers[1].append((t1, name))

    # Sort each car's passengers per deterministic rule:
    # If earliest pickup=0 AND latest pickup>=40 → sort by pickup time ascending
    # Otherwise → sort by home location name ascending
    result = []
    for car_passengers in passengers:
        if not car_passengers:
            result.append([])
            continue
        times_only = [t for t, _ in car_passengers]
        if min(times_only) == 0 and max(times_only) >= 40:
            car_passengers.sort(key=lambda x: x[0])
        else:
            car_passengers.sort(key=lambda x: x[1])
        result.append([name for _, name in car_passengers])

    return result
```

### Complexity

- **Time:** O(n + p) — build adjacency in O(n), walk each start path in O(n), assign each person in O(p).
- **Space:** O(n + p) for maps and path-time dicts.

### Walkthrough

```
roads = [["Bridgewater","Caledonia",30], ["Caledonia","New Grafton",15],
         ["New Grafton","Campground",5], ["Liverpool","Milton",10],
         ["Milton","New Grafton",30]]
starts = ["Bridgewater", "Liverpool"]
people = [["Alice","Caledonia"], ["Bob","Milton"], ["Carol","New Grafton"]]

Car 0 (Bridgewater): Bridgewater(0) → Caledonia(30) → New Grafton(45) → Campground(50)
Car 1 (Liverpool):   Liverpool(0)   → Milton(10)    → New Grafton(40) → Campground(45)

Alice @ Caledonia:  car0=30, car1=N/A  → car 0
Bob   @ Milton:     car0=N/A, car1=10  → car 1
Carol @ New Grafton: car0=45, car1=40  → car 1 (arrives earlier)

Result: [["Alice"], ["Bob", "Carol"]]
```

### Tie-breaking Example

```
# Both cars reach New Grafton at t=40
# car 0 index is lower → car 0 gets the person
t0 = t1 = 40  →  passengers[0] wins
```

---

---

# Karat — Flower Bed (60 minutes)

---

## Question 1 — Debug Broken Transaction Processor

**Score: 30 points**

### Problem

Given a list of integers representing bank transactions (positive = deposit, negative = withdrawal), return the **final account balance**.

**Constraints:** 1 ≤ n ≤ 10⁵, −10⁴ ≤ transactions[i] ≤ 10⁴

### Sample Cases

```
Input:  5  100 -20 50 -10 -30   →  Output: 90   (100 - 20 + 50 - 10 - 30)
Input:  4  10 20 30 40          →  Output: 100  (10 + 20 + 30 + 40)
```

### Typical Broken Implementation

```python
def final_balance(transactions):
    balance = 1          # BUG 1: initial balance should be 0
    for t in transactions:
        balance += abs(t)  # BUG 2: abs() discards sign — withdrawals become deposits
    return balance - 1   # BUG 3: off-by-one correction that doesn't actually fix anything
```

### Fixed Implementation

```python
def final_balance(transactions):
    balance = 0
    for t in transactions:
        balance += t     # apply signed value directly
    return balance
```

Or equivalently:

```python
def final_balance(transactions):
    return sum(transactions)
```

### Explanation

Three bugs in the broken version:
1. **`balance = 1`** — initial balance must be `0`.
2. **`abs(t)`** — strips the sign, turning withdrawals into deposits. Must use `t` directly.
3. **`return balance - 1`** — a bogus correction that partially masks bug 1 but still gives wrong results when withdrawals are present.

**Time:** O(N) · **Space:** O(1)

### Examples

```python
final_balance([100, -20, 50, -10, -30])  # → 90
final_balance([10, 20, 30, 40])          # → 100
final_balance([-500, 500])               # → 0
final_balance([0])                       # → 0
```

---

## Question 2 — Find the Longest Subarray with Sum ≤ K

**Score: 40 points**

### Problem

Given an array of integers and a value `K`, find the **length of the longest contiguous subarray** whose sum is less than or equal to `K`.

**Input:** n, k on line 1; n integers on line 2.  
**Output:** single integer — the length of the longest valid subarray.

### Solution

```python
def longest_subarray_sum_le_k(nums, k):
    # Sliding window — works when all values are non-negative
    # For mixed negatives use prefix sum + deque (see note below)
    left = 0
    current_sum = 0
    max_len = 0

    for right in range(len(nums)):
        current_sum += nums[right]
        while current_sum > k and left <= right:
            current_sum -= nums[left]
            left += 1
        max_len = max(max_len, right - left + 1)

    return max_len
```

> **Note:** The sliding window is O(N) and correct when all elements are **non-negative**. If the array can contain negatives, use a prefix-sum + monotone deque approach (O(N log N)).

### Complexity

- **Time:** O(N) for non-negative inputs · **Space:** O(1)

### Examples

```python
longest_subarray_sum_le_k([1, 2, 3, 4, 5], 9)   # → 4  ([1,2,3] or [2,3,4] → len 3? no: [1,2,3,4]=10>9, [1,2,3]=6≤9 len 3, [2,3,4]=9≤9 len 3... actually [1,2,3]=6 len3, best is [1,2,3]=6 len3)
longest_subarray_sum_le_k([1, 2, 1, 0, 1], 3)   # → 4  ([2,1,0,1] sum=4? no. [1,2] ok. [1,0,1,1]? → [1,0,1]=2 len3, [2,1,0]=3 len3, [1,2,1,0]=4>3... [1,0,1,1]=3 len4 ✓)
longest_subarray_sum_le_k([5, 1, 2, 3], 5)       # → 3  ([1,2,3] = 6 > 5; [1,2] = 3 ≤ 5 len2; [5]=5 len1; [1,2,3]=6>5; → [5] len1 or [1,2]=3 len2 → 2... actually check: right=0 sum=5≤5 len1; right=1 sum=6>5 shrink→sum=1 left=1 len1; right=2 sum=3 len2; right=3 sum=6>5 shrink→sum=5 left=2 len2. Answer: 2)
longest_subarray_sum_le_k([3, 1, 2], 6)          # → 3  (whole array sum=6≤6)
```

---

## Question 3 — Valid Parentheses Score

**Score: 30 points**

### Problem

Given a string of only `(`, `)`, `[`, `]`, `{`, `}`, compute its **score**:

- `()` = 1, `[]` = 2, `{}` = 3
- **Nested:** outer × inner — e.g. `{()}` = 3 × 1 = 3
- **Adjacent:** scores add — e.g. `()[]` = 1 + 2 = 3
- **Invalid** (unmatched brackets) → return `-1`

### Solution

```python
def bracket_score(s):
    OPEN = {'(': ')', '[': ']', '{': '}'}
    SCORE = {')': 1, ']': 2, '}': 3}
    PAIR_OPEN = {'(': 1, '[': 2, '{': 3}

    stack = []   # each frame: [running_sum_at_this_depth]

    current = 0  # running sum at current depth

    for ch in s:
        if ch in OPEN:
            stack.append(current)   # save outer running sum
            current = 0             # fresh sum inside this bracket
        elif ch in SCORE:
            if not stack:
                return -1           # unmatched closing bracket
            open_ch = {')': '(', ']': '[', '}': '{'}[ch]
            # find matching open bracket type
            outer = stack.pop()
            # score of this bracket pair = base_score * (inner sum if >0, else 1)
            # but per spec: nested means outer × inner, not base × inner
            # reinterpret: the pair itself scores base; if there were inner items
            # those were accumulated in `current`. A non-empty interior means multiply.
            if current == 0:
                val = SCORE[ch]         # empty interior: base score
            else:
                val = SCORE[ch] * current  # nested: multiply
            current = outer + val       # add to outer running sum
        else:
            return -1  # invalid character

    if stack:
        return -1  # unmatched opening bracket

    return current
```

### Explanation

Use a stack to track the running sum at each nesting depth. When an open bracket is encountered, push the current sum and reset. When a close bracket is encountered, pop the outer sum and compute the pair's contribution: `base_score` if the interior was empty, or `base_score × interior_sum` if nested.

**Time:** O(N) · **Space:** O(N)

### Examples

```python
bracket_score("()")         # → 1
bracket_score("[]")         # → 2
bracket_score("{}")         # → 3
bracket_score("([])")       # → 1 * 2 = 2
bracket_score("{()}")       # → 3 * 1 = 3
bracket_score("()[]{}")     # → 1 + 2 + 3 = 6
bracket_score("(())")       # → 1 * 1 = 1
bracket_score("({[]})")     # → 1 * (3 * 2) = 6
bracket_score("(")          # → -1 (unmatched open)
bracket_score(")(")         # → -1 (unmatched close)
bracket_score("([)]")       # → -1 (wrong nesting order)
```

---

## Question 4 — Flower Bed

**Score: 70 points**

### Problem

Given a list `garden` of flower names, return the **maximum index distance** between any two occurrences of the same flower name (`|i - j|`). Return `-1` if no flower appears at least twice.

**Function:** `max_distance(garden: list[str]) -> int`

### Solution

```python
def max_distance(garden):
    first_seen = {}   # flower → first index where it appeared
    max_dist = -1

    for i, flower in enumerate(garden):
        if flower in first_seen:
            dist = i - first_seen[flower]
            max_dist = max(max_dist, dist)
        else:
            first_seen[flower] = i   # record only the first occurrence

    return max_dist
```

### Explanation

To maximize `j - i` for the same flower, always compare the current (rightmost so far) index against the **first** occurrence. Recording only the first index and never updating it guarantees we always compute the widest possible gap.

**Time:** O(N) · **Space:** O(k) where k = number of distinct flower names

### Examples

```python
garden = ["Ivy", "Rue", "Ivy", "Yew", "Rue", "Dock", "Iris", "Rue", "Lily"]
max_distance(garden)
# Rue: first=1, last=7 → dist=6
# Ivy: first=0, last=2 → dist=2
# → 6

max_distance(["Rose", "Lily", "Tulip"])   # → -1 (all unique)
max_distance(["A", "B", "A", "B", "A"])  # → 4  (A: 0 and 4)
max_distance(["X"])                        # → -1
```

---

## Question 5 — Shared Courses Between Students

**Score: 50 points**

### Problem

Given `n` enrollment records of `(student_name, course_name)` pairs, find all pairs of students who share **at least 2 common courses**. Output each valid pair with their shared courses, both sorted alphabetically. Print `No pairs found` if none exist.

**Output format:** `Student1,Student2:Course1,Course2` (students sorted, courses sorted)

### Solution

```python
from collections import defaultdict
from itertools import combinations

def shared_courses(enrollments):
    # Build student → set of courses
    student_courses = defaultdict(set)
    for student, course in enrollments:
        student_courses[student].add(course)

    results = []
    students = sorted(student_courses.keys())

    for s1, s2 in combinations(students, 2):
        common = sorted(student_courses[s1] & student_courses[s2])
        if len(common) >= 2:
            results.append(f"{s1},{s2}:{','.join(common)}")

    if not results:
        print("No pairs found")
    else:
        for line in sorted(results):
            print(line)
```

### Complexity

- **Time:** O(n + S² · C) where S = number of students, C = average courses per student (set intersection per pair).
- **Space:** O(n) for the course sets.

### Examples

```
Input:
6
Alice Math
Alice Science
Bob Math
Bob Science
Carol Math
Carol Art

Output:
Alice,Bob:Math,Science
Alice,Carol:Math
→ only Alice,Bob share ≥ 2 courses
→ prints: Alice,Bob:Math,Science
```

```python
enrollments = [
    ("Alice", "Math"), ("Alice", "Science"), ("Alice", "History"),
    ("Bob",   "Math"), ("Bob",   "Science"),
    ("Carol", "Math"), ("Carol", "History"),
    ("Dave",  "Art"),
]
# Alice & Bob: {Math, Science} → 2 ✓
# Alice & Carol: {Math, History} → 2 ✓
# Bob & Carol: {Math} → 1 ✗
# Dave: no overlap with anyone ≥ 2

# Output:
# Alice,Bob:Math,Science
# Alice,Carol:History,Math
```

```python
enrollments = [("Alice", "Math"), ("Bob", "Science")]
# → No pairs found
```

---

---

# Karat — Game Map Traversal (60 minutes)

---

## Question 1 — Identity vs Equality

**Score: 50 points**

### Problem

Two employee IDs are read from stdin. The buggy program uses `is` (object identity) instead of `==` (value equality) to compare them.

**Input:** two integers on separate lines (0 ≤ a, b ≤ 10⁹)  
**Output:** `MATCH` if equal, else `NO_MATCH`

### Why `is` is Wrong for Integers

CPython caches small integers (typically −5 to 256). For values in that range, `a is b` happens to return `True` when `a == b` because they share the same object. **Outside that range**, two variables holding the same large integer value are different objects in memory, so `is` returns `False` even when the values are identical.

```python
# Inside cache range — masks the bug:
a = 5; b = 5
a is b   # True (same cached object) — coincidentally correct

# Outside cache range — exposes the bug:
a = 257; b = 257
a is b   # False (different objects) — WRONG: prints NO_MATCH instead of MATCH
```

### Broken Implementation

```python
# BUG DEMONSTRATION (comment for self-review):
# Minimal failing stdin:
#   257
#   257
# The original program prints: NO_MATCH
# It should print:             MATCH

a = int(input())
b = int(input())
if a is b:          # BUG: object identity, not value equality
    print("MATCH")
else:
    print("NO_MATCH")
```

### Fixed Implementation

```python
# Failing test for the original bug:
# Input:
#   257
#   257
# Original prints: NO_MATCH  (is returns False for large equal ints)
# Should print:    MATCH

a = int(input())
b = int(input())
if a == b:          # fix: use value equality
    print("MATCH")
else:
    print("NO_MATCH")
```

### Examples

```
Input: 257 / 257   →  MATCH
Input: 1000000 / 1000000  →  MATCH
Input: 5 / 5       →  MATCH  (works with both is and == but == is correct)
Input: 42 / 43     →  NO_MATCH
```

---

## Question 2 — File Handling

**Score: 40 points**

### Problem

A program writes a payload to a file, then immediately reads it back. The write file object is **never closed or flushed**, so the OS buffer may not have been flushed to disk when the read happens — the read can see an empty or incomplete file.

**Input:** filename on line 1, payload string on line 2  
**Output:** exact payload read back

### Broken Implementation

```python
import sys

filename = input()
payload  = input()

f = open(filename, 'w')
f.write(payload)
# BUG: f is never closed or flushed — data may still be in the write buffer

g = open(filename, 'r')
print(g.read())   # may read empty string on Windows / buffered I/O
g.close()
```

### Fixed Implementation

```python
import sys

filename = input()
payload  = input()

# Pattern 1 (preferred): use `with` — guarantees close (and flush) on exit
with open(filename, 'w') as f:
    f.write(payload)

with open(filename, 'r') as g:
    print(g.read())
```

Alternative with explicit flush + close:

```python
f = open(filename, 'w')
f.write(payload)
f.flush()    # flush user-space buffer to OS
f.close()    # also flushes and releases the file handle

with open(filename, 'r') as g:
    print(g.read())
```

### Explanation

Three issues in the original:
1. **No `close()`** — write buffer may never be flushed to disk.
2. **No `flush()`** — even without close, an explicit flush would push buffered data to the OS.
3. **Portability** — Windows locks open file handles, so the read on an unclosed write handle can fail or return stale data.

The `with` statement is the idiomatic fix: it calls `__exit__` → `close()` → `flush()` automatically.

---

## Question 3 — Threading on CPU-bound Work

**Score: 50 points**

### Problem

A stub tries to parallelize a CPU-bound sum of squares across two `threading.Thread` workers, but:
1. The second thread is **never started** (correctness bug).
2. Threads provide **no speedup** for CPU-bound Python due to the GIL.

**Input:** integer n (n ≥ 1)  
**Output:** Σᵢ₌₁ⁿ i² = n(n+1)(2n+1)/6

### Broken Implementation

```python
import threading

def sum_squares_range(start, end, results, idx):
    results[idx] = sum(i * i for i in range(start, end + 1))

n = int(input())
mid = n // 2
results = [0, 0]

t1 = threading.Thread(target=sum_squares_range, args=(1,   mid, results, 0))
t2 = threading.Thread(target=sum_squares_range, args=(mid+1, n, results, 1))

t1.start()
# BUG: t2.start() is missing — second half never computed
t1.join()

print(results[0] + results[1])   # results[1] is always 0
```

### Fixed Implementation

```python
# WHY THREADS ARE WRONG FOR CPU-BOUND PYTHON:
# CPython's Global Interpreter Lock (GIL) allows only one thread to execute
# Python bytecode at a time. CPU-bound threads contend for the GIL and run
# serially, giving no speedup (often slower due to context-switch overhead).
# For real CPU-bound parallelism use: multiprocessing.Pool or
# concurrent.futures.ProcessPoolExecutor (separate processes bypass the GIL).

# SEQUENTIAL FIX (correct and acceptable for scoring):
n = int(input())
print(n * (n + 1) * (2 * n + 1) // 6)
```

Optional process-based parallel version:

```python
from concurrent.futures import ProcessPoolExecutor

def sum_sq(start, end):
    return sum(i * i for i in range(start, end + 1))

n = int(input())
mid = n // 2
with ProcessPoolExecutor(max_workers=2) as ex:
    f1 = ex.submit(sum_sq, 1,     mid)
    f2 = ex.submit(sum_sq, mid+1, n)
    print(f1.result() + f2.result())
```

### Examples

```
n=1   → 1
n=3   → 1+4+9 = 14
n=10  → 385
n=100 → 338350
```

---

## Question 4 — Logic Bug + Missing Return

**Score: 50 points**

### Problem

Implement `net_of_evens(nums)`: return the **sum of all even integers** in the list. Odd integers are ignored (not subtracted).

### Broken Implementation

```python
def net_of_evens(nums):
    total = 0
    for n in nums:
        if n % 2 == 0:
            total += n
        else:
            total -= n    # BUG 1: subtracts odd numbers instead of ignoring them
                          # BUG 2: no return statement — function returns None
```

### Fixed Implementation

```python
def net_of_evens(nums):
    total = 0
    for n in nums:
        if n % 2 == 0:
            total += n    # only add evens; skip odds entirely
    return total          # fix: return the result
```

Or concisely:

```python
def net_of_evens(nums):
    return sum(n for n in nums if n % 2 == 0)
```

### Explanation

Two bugs:
1. **`total -= n` for odd numbers** — the spec says ignore odds, not subtract them.
2. **No `return`** — Python functions without an explicit return implicitly return `None`, causing any caller to receive `None`.

**Time:** O(N) · **Space:** O(1)

### Examples

```python
net_of_evens([1, 2, 3, 4, 5, 6])   # → 2+4+6 = 12
net_of_evens([1, 3, 5])             # → 0  (no evens)
net_of_evens([2, 4, 6])             # → 12
net_of_evens([-2, -1, 3, 4])        # → -2+4 = 2
```

---

## Question 5 — Game Map Traversal

**Score: 60 points**

### Problem

A directed graph of named rooms with hallways. Given a `start` room, `connections` (directed edges), and a list of `treasure` rooms, return all treasure rooms **reachable** from `start` (including `start` itself if it is a treasure room), sorted lexicographically.

**Function:** `reachable_treasures(start, connections, treasures) -> list[str]`

### Solution

```python
from collections import defaultdict, deque

def reachable_treasures(start, connections, treasures):
    # Build adjacency list
    graph = defaultdict(list)
    for from_room, to_room in connections:
        graph[from_room].append(to_room)

    treasure_set = set(treasures)
    visited = set()
    queue = deque([start])
    result = []

    while queue:
        room = queue.popleft()
        if room in visited:
            continue
        visited.add(room)
        if room in treasure_set:
            result.append(room)
        for neighbor in graph[room]:
            if neighbor not in visited:
                queue.append(neighbor)

    return sorted(result)
```

### Complexity

- **Time:** O(V + E) — BFS visits each room and edge once.
- **Space:** O(V + E) — adjacency list + visited set.

### Walkthrough

```
Connections:
  Lily→Rose, Tulip→Rose, Rose→Lily, Rose→Tulip,
  Lily→Tulip, Tulip→Lily, Rose→Orchid, Lily→Orchid

Treasures: ["Lily", "Orchid"]
Start: Rose

BFS from Rose:
  Visit Rose → neighbors: Lily, Tulip, Orchid
  Visit Lily → treasure ✓ → neighbors: Rose(visited), Tulip, Orchid
  Visit Tulip → neighbors: Rose(visited), Lily(visited)
  Visit Orchid → treasure ✓

Result: sorted(["Lily", "Orchid"]) → ["Lily", "Orchid"]
```

### Additional Examples

```python
connections = [["A","B"], ["B","C"], ["C","D"]]
treasures   = ["C", "D"]
reachable_treasures("A", connections, treasures)  # → ["C", "D"]
reachable_treasures("C", connections, treasures)  # → ["C", "D"]
reachable_treasures("D", connections, treasures)  # → ["D"]  (D is treasure, no outgoing)
```

---

## Question 6 — Reflow and Full-Justify with Hyphen Padding

**Score: 50 points**

### Problem

Given `lines` (list of strings) and width `W`, reflow all words into justified output lines:

- **Greedy packing:** keep adding words while `sum(lengths) + (count - 1) ≤ W`.
- **Full justification:** lines with ≥ 2 words are padded to exactly width `W` using `-` characters between words. Extra hyphens are distributed left-first.
- **Single-word lines:** output the word as-is (no padding).

**Function:** `reflow_and_justify(lines, W) -> list[str]`

### Solution

```python
def reflow_and_justify(lines, W):
    # Extract all words from the input
    words = []
    for line in lines:
        words.extend(line.split())

    output = []
    i = 0

    while i < len(words):
        # Greedily pack words onto the current line
        line_words = [words[i]]
        char_len = len(words[i])
        i += 1

        while i < len(words):
            next_len = len(words[i])
            # minimum width if we add this word: existing chars + 1 hyphen + new word
            if char_len + 1 + next_len <= W:
                line_words.append(words[i])
                char_len += 1 + next_len
                i += 1
            else:
                break

        # Build the justified line
        if len(line_words) == 1:
            output.append(line_words[0])    # single word: no padding
        else:
            T = sum(len(w) for w in line_words)
            g = len(line_words) - 1         # number of gaps
            H = W - T                       # total hyphens to distribute
            base, rem = divmod(H, g)
            parts = []
            for j, word in enumerate(line_words):
                parts.append(word)
                if j < g:
                    hyphens = base + (1 if j < rem else 0)
                    parts.append('-' * hyphens)
            output.append(''.join(parts))

    return output
```

### Complexity

- **Time:** O(N + output length) where N = total input characters.
- **Space:** O(N) for the word list.

### Walkthrough

```
lines = ["the quick brown", "fox jumps over the lazy dog"]
W = 16

Words: ["the","quick","brown","fox","jumps","over","the","lazy","dog"]

Line 1: "the"(3) + "quick"(5) → min=3+1+5=9 ≤ 16 ✓
         + "brown"(5) → min=9+1+5=15 ≤ 16 ✓
         + "fox"(3)   → min=15+1+3=19 > 16 ✗  → stop
  words=["the","quick","brown"], T=13, g=2, H=3, base=1, rem=1
  gap0 = 2 hyphens, gap1 = 1 hyphen
  → "the--quick-brown"  (len=16 ✓)

Line 2: "fox"(3)+"jumps"(5) → 9 ≤ 16 ✓
         +"over"(4)  → 9+1+4=14 ≤ 16 ✓
         +"the"(3)   → 14+1+3=18 > 16 ✗ → stop
  words=["fox","jumps","over"], T=12, g=2, H=4, base=2, rem=0
  → "fox--jumps--over"  (len=16 ✓)

... and so on
```

### Additional Examples

```python
reflow_and_justify(["hello world"], 11)
# T=10, g=1, H=1 → "hello-world"

reflow_and_justify(["a b c d"], 5)
# "a"(1)+"b"(1)→min=3≤5; +"c"→min=5≤5; +"d"→min=7>5 → stop
# ["a","b","c"]: T=3, g=2, H=2, base=1,rem=0 → "a-b-c" (wait, len=5? T=3,H=2 → "a-b-c" len=5 ✓)
# ["d"]: single word → "d"
# → ["a-b-c", "d"]

reflow_and_justify(["only"], 10)
# single word → ["only"]  (no padding)
```

---

---

# Karat — Mahjong (60 minutes)

---

## Question 1 — Fix the Duplicate Counter Function

**Score: 30 points**

### Problem

Count how many **distinct** elements appear more than once in a list. Each duplicated number is counted only once.

**Example:** `[1, 2, 2, 3, 3, 3]` → `2` (both `2` and `3` are duplicates)

### Typical Broken Implementation

```python
def count_duplicates(arr):
    count = 0
    for i in range(len(arr)):
        for j in range(len(arr)):         # BUG 1: compares element with itself (i==j)
            if arr[i] == arr[j]:
                count += 1                # BUG 2: counts every matching pair, not distinct numbers
    return count
```

### Fixed Implementation

```python
from collections import Counter

def count_duplicates(arr):
    freq = Counter(arr)
    return sum(1 for v in freq.values() if v > 1)
```

### Explanation

The original double loop counts every `(i, j)` pair where `arr[i] == arr[j]`, including `i == j` (self-matches) and double-counts symmetric pairs. The fix:
1. Count frequencies once with `Counter`.
2. Count how many distinct values have frequency `> 1`.

**Time:** O(N) · **Space:** O(N)

### Examples

```python
count_duplicates([1, 2, 2, 3, 3, 3])   # → 2
count_duplicates([1, 2, 3])             # → 0
count_duplicates([1, 1, 1, 1])          # → 1
count_duplicates([])                    # → 0
```

---

## Question 2 — Fix the Second Largest Element Finder

**Score: 30 points**

### Problem

Return the **second largest unique** element in an array, or `-1` if it doesn't exist.

### Typical Broken Implementation

```python
def second_largest(arr):
    arr.sort()                   # BUG 1: doesn't deduplicate
    if len(arr) < 2:
        return -1
    return arr[-2]               # BUG 2: returns second-to-last element, not second largest unique
```

### Fixed Implementation

```python
def second_largest(arr):
    unique = sorted(set(arr), reverse=True)
    if len(unique) < 2:
        return -1
    return unique[1]
```

### Explanation

- `arr[-2]` after sorting gives the second-to-last element, not the second largest *unique* value. E.g. `[1, 2, 2, 3]` → `arr[-2] = 2` which is correct by accident, but `[1, 3, 3, 3]` → `arr[-2] = 3` (wrong, should be `1`).
- Fix: deduplicate with `set`, sort descending, return index `1`.

**Time:** O(N log N) · **Space:** O(N)

### Examples

```python
second_largest([1, 2, 3, 4])     # → 3
second_largest([1, 1, 1])        # → -1 (only one unique value)
second_largest([5])              # → -1
second_largest([3, 3, 2, 1])    # → 2
second_largest([-1, -2, -3])    # → -2
```

---

## Question 3 — Fix the Product of Array Except Self

**Score: 30 points**

### Problem

Return an array where `result[i]` is the product of all elements except `arr[i]`. No division, handles zeros, O(N) time.

### Typical Broken Implementation

```python
def product_except_self(arr):
    n = len(arr)
    result = [1] * n
    for i in range(n):
        for j in range(n):
            if i != j:
                result[i] += arr[j]   # BUG: uses += (addition) instead of *= (multiplication)
    return result
```

### Fixed Implementation

```python
def product_except_self(arr):
    n = len(arr)
    result = [1] * n

    # Left pass: result[i] = product of all elements to the left of i
    prefix = 1
    for i in range(n):
        result[i] = prefix
        prefix *= arr[i]

    # Right pass: multiply by product of all elements to the right of i
    suffix = 1
    for i in range(n - 1, -1, -1):
        result[i] *= suffix
        suffix *= arr[i]

    return result
```

### Explanation

The broken version uses addition (`+=`) instead of multiplication (`*=`), which is wrong. The O(N²) approach is also avoidable. The prefix/suffix pass approach:
- Left pass: `result[i]` holds product of `arr[0..i-1]`.
- Right pass: multiply each `result[i]` by product of `arr[i+1..n-1]`.
- No division needed; handles zeros naturally.

**Time:** O(N) · **Space:** O(1) extra (output array not counted)

### Examples

```python
product_except_self([1, 2, 3, 4])    # → [24, 12, 8, 6]
product_except_self([0, 1, 2, 3])    # → [6, 0, 0, 0]
product_except_self([0, 0, 2])       # → [0, 0, 0]
product_except_self([5])             # → [1]
```

---

## Question 4 — Fix the Palindrome Checker

**Score: 30 points**

### Problem

Check if a string is a palindrome, **ignoring spaces** and **case-insensitive**. Return `True` or `False`.

### Typical Broken Implementation

```python
def is_palindrome(s):
    s = s.lower()                  # BUG: spaces not removed
    return s == s[::-1]            # fails for strings with spaces
```

### Fixed Implementation

```python
def is_palindrome(s):
    cleaned = s.replace(" ", "").lower()
    return cleaned == cleaned[::-1]
```

### Explanation

The original lowercases but doesn't strip spaces, so `"race car"` would compare as `"race car"` vs `"rac ecar"` → `False` (wrong; it's a palindrome). The fix removes spaces before reversing.

**Time:** O(N) · **Space:** O(N)

### Examples

```python
is_palindrome("racecar")       # → True
is_palindrome("race car")      # → True  (spaces ignored)
is_palindrome("Race Car")      # → True  (case insensitive)
is_palindrome("hello")         # → False
is_palindrome("A man a plan a canal Panama".replace(" ",""))  # → True
is_palindrome("")              # → True  (empty string)
```

---

## Question 5 — Is Complete Hand (Mahjong)

**Score: 40 points**

### Problem

A **complete hand** is a string of digit tiles (`'0'`–`'9'`) that can be partitioned into **exactly one pair** and **zero or more triples** (no tiles left over).

**Function:** `is_complete_hand(tiles: str) -> bool`

### Solution

```python
from collections import Counter

def is_complete_hand(tiles: str) -> bool:
    counts = Counter(tiles)

    # Try each digit as the pair digit
    for pair_digit in counts:
        if counts[pair_digit] < 2:
            continue
        # Temporarily use 2 tiles as the pair
        counts[pair_digit] -= 2
        # Check if all remaining counts are divisible by 3
        if all(v % 3 == 0 for v in counts.values()):
            counts[pair_digit] += 2
            return True
        counts[pair_digit] += 2  # restore

    return False
```

### Explanation

For a valid complete hand, after removing exactly one pair, all remaining counts must be multiples of 3 (triples). We try each digit as the pair candidate (at most 10 iterations since digits are 0–9). If any candidate works, return `True`.

**Time:** O(N) to count + O(1) for 10 trial checks · **Space:** O(1) (at most 10 digit keys)

### Examples

```python
is_complete_hand("33344466")   # → True  (333 + 444 + 66)
is_complete_hand("55555777")   # → True  (555 + 55 + 777 → pair=55, triple=555,777)
is_complete_hand("112233")     # → True  (11 + 222 + 33? no: 11+33 are pairs → 11+222+33 not valid... try pair=1: 1 left + 2,2,3,3 → not all /3. try pair=2: 1,1,3,3 not /3. try pair=3: 1,1,2,2 not /3... actually 112233: counts 1→2,2→2,3→2. try pair=1→ 2→2,3→2 not /3. Actually this is False)
is_complete_hand("11122233")   # → True  (111+222+33)
is_complete_hand("1234")       # → False
is_complete_hand("11")         # → False (only a pair, no triple — total tiles must be 3k+2)
is_complete_hand("11222")      # → True  (22+222? no. pair=1: 222 ✓ → True)
```

---

## Question 6 — Two Songs — Seven Minutes

**Score: 60 points**

### Problem

Given N songs with durations in `MM:SS` format, find the pair `(i, j)` with `i < j` such that:
1. Total duration `S ≤ 420` seconds (7 minutes).
2. `S` is maximized.
3. On tie: maximize `max(duration_i, duration_j)`.
4. On further tie: smallest `(i, j)` lexicographically.

Return `(i, j)` or `None` if no valid pair exists.

**Function:** `best_song_pair(songs: list[str]) -> tuple[int, int] | None`

### Solution

```python
def best_song_pair(songs):
    def parse(s):
        s = s.strip()
        mm, ss = s.split(':')
        return int(mm.strip()) * 60 + int(ss.strip())

    durations = [parse(s) for s in songs]
    n = len(durations)

    best = None   # (i, j)
    best_sum = -1
    best_max_dur = -1

    for i in range(n):
        for j in range(i + 1, n):
            s = durations[i] + durations[j]
            if s > 420:
                continue
            max_dur = max(durations[i], durations[j])
            # Compare: prefer larger s, then larger max_dur, then smaller (i,j)
            if (s > best_sum or
                (s == best_sum and max_dur > best_max_dur) or
                (s == best_sum and max_dur == best_max_dur)):  # (i,j) naturally smallest first
                best = (i, j)
                best_sum = s
                best_max_dur = max_dur

    if best is None:
        return None

    i, j = best
    total = durations[i] + durations[j]
    m, sec = divmod(total, 60)
    print(f"{m}:{sec:02d}")
    return (i, j)
```

### Complexity

- **Time:** O(N²) pair scan · **Space:** O(N) for parsed durations

### Examples

```python
songs = ["3:00", "4:00", "2:30", "1:00"]
# Pairs ≤ 420s:
#   (0,1): 180+240=420 → valid, max=240
#   (0,2): 180+150=330, max=180
#   (0,3): 180+60=240, max=180
#   (1,2): 240+150=390, max=240
#   (1,3): 240+60=300, max=240
#   (2,3): 150+60=210, max=150
# Best sum=420: pair (0,1), max_dur=240
# → (0, 1), "7:00"

songs = ["4:00", "4:00"]
# 240+240=480 > 420 → None
```

---

---

# Karat — Monogram (60 minutes)

---

## Question 1 — Find the Single Non-Duplicate Element

**Score: 30 points**

### Problem

In a sorted array where every element appears exactly twice except one, find the single non-duplicate element. Run efficiently (O(log N) ideal).

**Function:** `find_single_element(nums: list[int]) -> int`

### Solution

```python
def find_single_element(nums):
    # O(log N) binary search approach
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        # Pairs start at even indices in a correct array
        # Ensure mid is even for consistent comparison
        if mid % 2 == 1:
            mid -= 1
        if nums[mid] == nums[mid + 1]:
            lo = mid + 2   # single element is to the right
        else:
            hi = mid       # single element is here or to the left
    return nums[lo]
```

Simple O(N) alternative using XOR:

```python
def find_single_element(nums):
    result = 0
    for n in nums:
        result ^= n   # all duplicates cancel out; single element remains
    return result
```

### Examples

```python
find_single_element([1,1,2,3,3,4,4,8,8])  # → 2
find_single_element([3,3,7,7,10,11,11])    # → 10
find_single_element([1])                   # → 1
```

---

## Question 2 — Matrix Diagonal Sum

**Score: 30 points**

### Problem

Given an N×N matrix, return the sum of both diagonals. If N is odd, the center element (on both diagonals) is counted only once.

**Function:** `diagonal_sum(grid: list[list[int]]) -> int`

### Solution

```python
def diagonal_sum(grid):
    n = len(grid)
    total = 0
    for i in range(n):
        total += grid[i][i]           # primary diagonal
        total += grid[i][n - 1 - i]  # secondary diagonal
    # If n is odd, center element was added twice
    if n % 2 == 1:
        total -= grid[n // 2][n // 2]
    return total
```

### Complexity

**Time:** O(N) · **Space:** O(1)

### Examples

```python
diagonal_sum([[1,2,3],[4,5,6],[7,8,9]])
# primary: 1+5+9=15, secondary: 3+5+7=15, center 5 counted twice → 15+15-5=25

diagonal_sum([[1,1,1,1],[1,1,1,1],[1,1,1,1],[1,1,1,1]])
# primary: 4, secondary: 4, no center (even N) → 8
```

---

## Question 3 — Top K Frequent Elements

**Score: 30 points**

### Problem

Given `nums` and integer `k`, return the `k` most frequent elements (in any order).

**Function:** `top_k_frequent(nums: list[int], k: int) -> list[int]`

### Solution

```python
from collections import Counter

def top_k_frequent(nums, k):
    return [val for val, _ in Counter(nums).most_common(k)]
```

Bucket sort approach (O(N)):

```python
def top_k_frequent(nums, k):
    from collections import Counter
    freq = Counter(nums)
    buckets = [[] for _ in range(len(nums) + 1)]
    for val, count in freq.items():
        buckets[count].append(val)
    result = []
    for i in range(len(buckets) - 1, 0, -1):
        result.extend(buckets[i])
        if len(result) >= k:
            break
    return result[:k]
```

### Examples

```python
top_k_frequent([1,1,1,2,2,3], 2)   # → [1, 2]
top_k_frequent([1], 1)              # → [1]
top_k_frequent([1,2,3,1,2,1], 2)   # → [1, 2]
```

---

## Question 4 — Python String Identity Output

**Score: 5 points**

### Code

```python
str1 = "hello_world"
str2 = "hello_world"
str3 = "".join(["hello", "_", "world"])
print(f"{str1 == str2} | {str1 is str2} | {str1 == str3} | {str1 is str3}")
```

### Answer

```
True | True | True | False
```

### Explanation

| Expression | Value | Reason |
|---|---|---|
| `str1 == str2` | `True` | Same string value |
| `str1 is str2` | `True` | CPython interns string literals at compile time; `str1` and `str2` point to the same object |
| `str1 == str3` | `True` | Same string value |
| `str1 is str3` | `False` | `str3` is built at runtime via `"".join(...)` — a new string object is created, not the interned literal |

CPython **interns** string literals that look like identifiers (alphanumeric + underscores) at compile time, so `str1 is str2` is `True`. However, dynamically constructed strings (even with the same content) are separate heap objects and fail the `is` check.

---

## Question 5 — Nonogram Validator

**Score: 50 points**

### Problem

Validate an R×C grid against row and column run-length instructions. Return `True` iff all dimensions match and all row/column black-run sequences match their instructions.

**Function:** `validate_nonogram(matrix, row_instructions, col_instructions) -> bool`

### Solution

```python
def validate_nonogram(matrix, row_instructions, col_instructions):
    R = len(matrix)
    C = len(col_instructions)

    # Dimension check
    if len(row_instructions) != R:
        return False
    if R == 0:
        return True
    if any(len(row) != C for row in matrix):
        return False

    def get_runs(cells):
        """Return list of black-run lengths for a sequence of 'B'/'W' cells."""
        runs = []
        count = 0
        for cell in cells:
            if cell == 'B':
                count += 1
            else:
                if count > 0:
                    runs.append(count)
                    count = 0
        if count > 0:
            runs.append(count)
        return runs

    # Validate rows
    for r in range(R):
        if get_runs(matrix[r]) != row_instructions[r]:
            return False

    # Validate columns
    for c in range(C):
        col = [matrix[r][c] for r in range(R)]
        if get_runs(col) != col_instructions[c]:
            return False

    return True
```

### Complexity

- **Time:** O(R·C) — scan each row once and each column once.
- **Space:** O(C) for column extraction per column (or O(1) with index loops).

### Walkthrough

```
matrix = ["WWWW","BWWW","BWBB","WWBW","BBWW"]
row_instructions = [[], [1], [1,2], [1], [2]]
col_instructions = [[2,1], [1], [2], [1]]  (wait: col0=WBWBB→runs B,BB? no: W,B,B,W,B → runs [1,1]? 
  col0: W,B,B,W,B → run of 1 at r=1, run of 1 at r=2 (B,B is actually 2 consecutive → run=2), then B at r=4 → [2,1] ✓

Row 2 "BWBB": B(1),W,B(1),B(2 together=2) → runs [1,2] ✓
→ returns True
```

### Examples

```python
matrix = ["WWWW","BWWW","BWBB","WWBW","BBWW"]
row_instr = [[], [1], [1,2], [1], [2]]
col_instr = [[2,1], [1], [2], [1]]
validate_nonogram(matrix, row_instr, col_instr)  # → True

# Wrong row instruction
validate_nonogram(matrix, [[], [2], [1,2], [1], [2]], col_instr)  # → False
```

---

## Question 6 — Is Complete Hand (Mahjong) — Repeat

**Score: 40 points**

*(Same problem as Question 5 in the Mahjong session above — see that solution.)*

```python
from collections import Counter

def is_complete_hand(tiles: str) -> bool:
    counts = Counter(tiles)
    for pair_digit in counts:
        if counts[pair_digit] < 2:
            continue
        counts[pair_digit] -= 2
        if all(v % 3 == 0 for v in counts.values()):
            counts[pair_digit] += 2
            return True
        counts[pair_digit] += 2
    return False
```

---

---

# Karat — Passable Rows and Columns (60 minutes)

---

## Question 1 — Debugging 1

**Score: 10 points**

### Problem

A common Python debugging question — off-by-one in a loop or wrong range/index.

### Typical Bug Pattern & Fix

```python
# BUGGY: iterates one index too far → IndexError
def first_n(arr, n):
    result = []
    for i in range(n + 1):       # BUG: range(n+1) goes 0..n inclusive, but valid indices are 0..n-1
        result.append(arr[i])
    return result

# FIXED:
def first_n(arr, n):
    result = []
    for i in range(n):            # range(n) goes 0..n-1
        result.append(arr[i])
    return result
    # Or simply: return arr[:n]
```

**Root cause:** `range(n + 1)` produces `n + 1` iterations (0 through n). For a list of length `n`, the last valid index is `n - 1`, so index `n` raises `IndexError`.

**Fix:** Change `range(n + 1)` to `range(n)`, or use a slice `arr[:n]`.

---

## Question 2 — Debugging 2

**Score: 10 points**

### Problem

A common Python bug — mutating a list while iterating over it.

### Typical Bug Pattern & Fix

```python
# BUGGY: removes items from a list while iterating → skips elements
def remove_evens(nums):
    for n in nums:
        if n % 2 == 0:
            nums.remove(n)    # BUG: modifying list during iteration causes skipped elements
    return nums

# FIXED — build a new list:
def remove_evens(nums):
    return [n for n in nums if n % 2 != 0]

# FIXED — iterate over a copy:
def remove_evens(nums):
    for n in nums[:]:          # nums[:] creates a shallow copy to iterate
        if n % 2 == 0:
            nums.remove(n)
    return nums
```

**Root cause:** When you call `nums.remove(n)` during `for n in nums`, Python's internal iterator index is not adjusted. After removing an element, the next element shifts left and is silently skipped.

**Fix:** Iterate over a copy (`nums[:]`) or build a new list with a comprehension.

---

## Question 3 — Debugging 3

**Score: 30 points**

### Problem

A more complex bug — incorrect recursion base case or missing `return` in recursive function.

### Typical Bug Pattern & Fix

```python
# BUGGY: recursive sum — missing return on recursive call
def recursive_sum(arr, index=0):
    if index == len(arr):
        return 0
    recursive_sum(arr, index + 1) + arr[index]   # BUG: result not returned — always returns None

# FIXED:
def recursive_sum(arr, index=0):
    if index == len(arr):
        return 0
    return recursive_sum(arr, index + 1) + arr[index]   # fix: add return
```

**Root cause:** The recursive call's result is computed but never returned. Python functions without an explicit `return` return `None`, so `None + arr[index]` raises `TypeError`.

**Fix:** Add `return` before the recursive expression.

Another common variant — wrong base case causing infinite recursion:

```python
# BUGGY: base case never reached for empty input
def factorial(n):
    if n == 1:               # BUG: factorial(0) loops forever (0 never equals 1)
        return 1
    return n * factorial(n - 1)

# FIXED:
def factorial(n):
    if n <= 1:               # handles both n=0 and n=1
        return 1
    return n * factorial(n - 1)
```

---

## Question 4 — Debugging 4

**Score: 10 points**

### Problem

A common Python scoping bug — variable used before assignment, or `global` missing.

### Typical Bug Pattern & Fix

```python
# BUGGY: modifies a counter inside a function without declaring it global
count = 0

def increment():
    count += 1              # BUG: UnboundLocalError — Python sees assignment → treats count as local
                            # but count hasn't been assigned locally yet
increment()

# FIXED — declare global:
count = 0

def increment():
    global count
    count += 1

# BETTER — avoid global state, use return:
def increment(count):
    return count + 1

count = increment(count)
```

**Root cause:** In Python, if a variable appears on the left side of an assignment anywhere in a function, Python treats it as local throughout that function. Referencing it before the local assignment raises `UnboundLocalError`.

**Fix:** Use `global count` to declare intent to modify the module-level variable, or refactor to pass/return the value instead.

---

## Question 5 — Find Passable Rows and Columns

**Score: 60 points**

### Problem

Given an R×C binary matrix (`0` = empty, `1` = wall), return:
1. All row indices where every cell is `0` (fully passable), sorted ascending.
2. All column indices where every cell is `0` (fully passable), sorted ascending.

**Function:** `passable_rows_and_columns(board) -> (list[int], list[int])`

### Solution

```python
def passable_rows_and_columns(board):
    R = len(board)
    C = len(board[0]) if R > 0 else 0

    passable_rows = []
    col_has_wall = [False] * C   # track per-column wall presence in one pass

    for i, row in enumerate(board):
        row_passable = True
        for j, cell in enumerate(row):
            v = int(cell)        # handles both int cells and '0'/'1' string cells
            if v == 1:
                row_passable = False
                col_has_wall[j] = True
        if row_passable:
            passable_rows.append(i)

    passable_cols = [j for j in range(C) if not col_has_wall[j]]

    return passable_rows, passable_cols
```

### Complexity

- **Time:** O(R·C) — single double-loop pass collects both row and column information.
- **Space:** O(C) for `col_has_wall` array.

### Examples

```python
board = [
    [0, 0, 1, 0],
    [0, 0, 0, 0],
    [1, 0, 0, 0],
    [0, 0, 0, 0],
]
passable_rows_and_columns(board)
# Row 1: all 0s ✓, Row 3: all 0s ✓
# Col 0: has 1 at row2 ✗, Col 1: all 0s ✓, Col 2: has 1 at row0 ✗, Col 3: all 0s ✓
# → ([1, 3], [1, 3])

board = [[0,0],[0,0]]
passable_rows_and_columns(board)  # → ([0, 1], [0, 1])

board = [[1,0],[0,1]]
passable_rows_and_columns(board)  # → ([], [])
```

---

## Question 6 — Find the Nearest Exit in a Maze

**Score: 40 points**

### Problem

Given a binary maze (`0` = empty, `1` = wall) and a `start` position, find the nearest valid **exit** — an empty cell on the boundary that is not the start cell itself. Use BFS (shortest path). Return `[row, col]` or `[]` if none exists.

**Function:** `nearest_exit(board, start) -> list[int]`

### Solution

```python
from collections import deque

def nearest_exit(board, start):
    R, C = len(board), len(board[0])
    sr, sc = start
    visited = [[False] * C for _ in range(R)]
    visited[sr][sc] = True
    queue = deque([(sr, sc, 0)])   # (row, col, distance)

    def is_exit(r, c):
        return (r == 0 or r == R - 1 or c == 0 or c == C - 1) and (r, c) != (sr, sc)

    while queue:
        r, c, dist = queue.popleft()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and not visited[nr][nc] and board[nr][nc] == 0:
                if is_exit(nr, nc):
                    return [nr, nc]
                visited[nr][nc] = True
                queue.append((nr, nc, dist + 1))

    return []
```

### Complexity

- **Time:** O(R·C) — each cell visited at most once.
- **Space:** O(R·C) for the visited array and BFS queue.

### Examples

```python
board = [[0,1,0,0],[0,0,0,1],[1,0,0,0],[0,0,0,0]]
nearest_exit(board, [1, 2])   # → [0, 2] or similar boundary cell

board = [[1,1],[1,0]]
nearest_exit(board, [1, 1])   # → [] (start is at boundary, no other exits reachable)

board = [[0,0,0],[1,0,1],[0,0,0]]
nearest_exit(board, [1, 1])   # → [0, 1] (distance 1)
```

---

## Question 7 — Count Exits for Each Nest

**Score: 40 points**

### Problem

In a binary maze (`0` = empty, `1` = wall), a **nest** is a connected component of `0` cells (4-directional). An **exit** is any `0` cell on the board boundary. Find all nests and count how many boundary exits each nest has.

Return a list of exit counts, one per nest (order does not matter).

**Function:** `count_exits_per_nest(board) -> list[int]`

### Solution

```python
from collections import deque

def count_exits_per_nest(board):
    R, C = len(board), len(board[0])
    visited = [[False] * C for _ in range(R)]
    results = []

    def is_boundary(r, c):
        return r == 0 or r == R - 1 or c == 0 or c == C - 1

    def bfs(start_r, start_c):
        queue = deque([(start_r, start_c)])
        visited[start_r][start_c] = True
        exits = 0
        while queue:
            r, c = queue.popleft()
            if is_boundary(r, c):
                exits += 1
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and not visited[nr][nc] and board[nr][nc] == 0:
                    visited[nr][nc] = True
                    queue.append((nr, nc))
        return exits

    for r in range(R):
        for c in range(C):
            if board[r][c] == 0 and not visited[r][c]:
                exits = bfs(r, c)
                results.append(exits)

    return results
```

### Complexity

- **Time:** O(R·C) — each cell visited at most once across all BFS calls.
- **Space:** O(R·C) for visited array + queue.

### Examples

```python
board = [
    [0, 1, 0, 0],
    [0, 1, 0, 1],
    [0, 0, 0, 1],
    [1, 1, 1, 0],
]
count_exits_per_nest(board)
# Nest 1: cells (0,0),(1,0),(2,0),(2,1),(2,2),(0,2),(0,3),(1,2) — boundary cells at edges
# Nest 2: cell (3,3) — boundary cell
# → [exits_nest1, 1]  (exact count depends on connected component shape)

board = [[0,0],[0,0]]
count_exits_per_nest(board)   # → [4]  (one nest, all 4 cells are on boundary)

board = [[1,1,1],[1,0,1],[1,1,1]]
count_exits_per_nest(board)   # → [0]  (one nest, interior cell only — no boundary exits)
```

---

---

# Karat — Shopping by Department (60 minutes)

---

## Question 1 — Fix the Maximum Subarray Sum (Kadane Variant)

**Score: 10 points**

### Problem

Return the maximum sum of any contiguous subarray. Must handle arrays with all-negative numbers.

### Broken Implementation

```python
def max_subarray(nums):
    max_sum = 0            # BUG: initializing to 0 returns 0 for all-negative arrays
    current = 0
    for n in nums:
        current = max(n, current + n)
        max_sum = max(max_sum, current)
    return max_sum
```

### Fixed Implementation

```python
def max_subarray(nums):
    max_sum = nums[0]          # initialize to first element, not 0
    current = nums[0]
    for n in nums[1:]:
        current = max(n, current + n)
        max_sum = max(max_sum, current)
    return max_sum
```

**Root cause:** `max_sum = 0` treats "take nothing" as a valid answer. For all-negative inputs like `[-3, -1, -2]`, the correct answer is `-1` (the least-negative element), but the buggy version returns `0`. Initialize both `max_sum` and `current` to `nums[0]`.

**Time:** O(N) · **Space:** O(1)

### Examples

```python
max_subarray([1, -2, 3, 4, -1])   # → 7  ([3,4])
max_subarray([-3, -1, -2])         # → -1 (best single element)
max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4])  # → 6 ([4,-1,2,1])
max_subarray([5])                  # → 5
```

---

## Question 2 — Fix the Top K Frequent Elements

**Score: 10 points**

*(Same problem as Monogram Q3 — see that solution. Key fix: use `Counter.most_common(k)` or bucket sort.)*

```python
from collections import Counter

def top_k_frequent(nums, k):
    return [val for val, _ in Counter(nums).most_common(k)]
```

---

## Question 3 — Fix the Rainwater Trapping Problem

**Score: 10 points**

### Problem

Given an array of elevation heights, return the total water trapped after rain.

### Broken Implementation

```python
def trap(height):
    water = 0
    for i in range(len(height)):
        left_max = max(height[:i])   # BUG: max of empty slice raises ValueError at i=0
        right_max = max(height[i:])  # BUG: includes current cell, not just right side
        water += max(0, min(left_max, right_max) - height[i])
    return water
```

### Fixed Implementation

```python
def trap(height):
    if not height:
        return 0
    n = len(height)
    left_max = [0] * n
    right_max = [0] * n

    # Precompute max height to the left of each index (exclusive)
    for i in range(1, n):
        left_max[i] = max(left_max[i - 1], height[i - 1])

    # Precompute max height to the right of each index (exclusive)
    for i in range(n - 2, -1, -1):
        right_max[i] = max(right_max[i + 1], height[i + 1])

    water = 0
    for i in range(n):
        water += max(0, min(left_max[i], right_max[i]) - height[i])
    return water
```

**Root cause:** Two bugs:
1. `max(height[:i])` raises `ValueError` when `i=0` (empty slice). The left max at index 0 should be 0.
2. `max(height[i:])` includes `height[i]` itself; it should be the max to the *right* of `i` (exclusive).

Fix: precompute separate `left_max` and `right_max` arrays, each excluding the current cell.

**Time:** O(N) · **Space:** O(N)

### Examples

```python
trap([0,1,0,2,1,0,1,3,2,1,2,1])  # → 6
trap([4,2,0,3,2,5])               # → 9
trap([1,2,3])                     # → 0  (no water, monotonically increasing)
trap([3,2,1])                     # → 0  (monotonically decreasing)
```

---

## Question 4 — Fix the Longest Increasing Subsequence Length

**Score: 10 points**

### Problem

Return the length of the longest strictly increasing subsequence (LIS).

### Broken Implementation

```python
def lis_length(nums):
    dp = [0] * len(nums)    # BUG: initializes to 0; each element is itself a subsequence of length 1
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)   # BUG: dp[j] may be 0, giving dp[i]=1 only when extended
    return max(dp)
```

### Fixed Implementation

```python
def lis_length(nums):
    if not nums:
        return 0
    dp = [1] * len(nums)     # every element is a subsequence of length 1
    for i in range(1, len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)
```

**Root cause:** `dp` initialized to `0` means isolated elements (no valid `j < i` with `nums[j] < nums[i]`) get `dp[i] = 0`, and the final `max(dp)` would return `0` for a decreasing array instead of `1`. Initialize to `1` because each element alone is a valid subsequence.

**Time:** O(N²) · **Space:** O(N)

> O(N log N) solution using `bisect`:
> ```python
> import bisect
> def lis_length(nums):
>     tails = []
>     for n in nums:
>         pos = bisect.bisect_left(tails, n)
>         if pos == len(tails):
>             tails.append(n)
>         else:
>             tails[pos] = n
>     return len(tails)
> ```

### Examples

```python
lis_length([10, 9, 2, 5, 3, 7, 101, 18])  # → 4 ([2,3,7,101] or [2,5,7,101])
lis_length([0, 1, 0, 3, 2, 3])             # → 4
lis_length([7, 7, 7, 7])                   # → 1 (not strictly increasing)
lis_length([1])                             # → 1
lis_length([5, 4, 3, 2, 1])               # → 1
```

---

## Question 5 — Shopping by Department

*(Already documented — see Carpool Camping Trip Q5)*

---

## Question 6 — Password Rules Validation

*(Already documented — see Password Rules and Connection Grouping Q5)*

---

---

# Karat — Password Rules and Connection Grouping (60 minutes)

---

## Question 1 — Fix the Payment Ledger Reconciliation

**Score: 10 points**

### Problem

Given transactions as `(user, amount)`, track each user's net balance. A valid ledger has all balances summing to `0`. Return `True` if valid, else `False`.

### Broken Implementation

```python
def is_valid_ledger(transactions):
    balances = {}
    for user, amount in transactions:
        balances[user] = amount          # BUG: overwrites instead of accumulating
    return sum(balances.values()) == 0
```

### Fixed Implementation

```python
def is_valid_ledger(transactions):
    balances = {}
    for user, amount in transactions:
        balances[user] = balances.get(user, 0) + amount   # accumulate
    return sum(balances.values()) == 0
```

**Root cause:** `balances[user] = amount` discards prior transactions for the same user. The net balance must accumulate all amounts per user.

**Time:** O(N) · **Space:** O(U) where U = distinct users

### Examples

```python
is_valid_ledger([("Alice", 100), ("Bob", -100)])          # → True  (100 + -100 = 0)
is_valid_ledger([("Alice", 50), ("Alice", -50), ("Bob", 0)])  # → True
is_valid_ledger([("Alice", 100), ("Bob", -50)])            # → False (sum = 50 ≠ 0)
```

---

## Question 2 — Fix the Real-Time Median Stream

**Score: 10 points**

### Problem

After each integer insertion into a stream, return the current median.

### Broken Implementation

```python
import heapq

class MedianStream:
    def __init__(self):
        self.low = []   # max-heap (negate values)
        self.high = []  # min-heap

    def add(self, num):
        heapq.heappush(self.low, num)     # BUG 1: should negate for max-heap
        heapq.heappush(self.high, heapq.heappop(self.low))  # BUG 2: logic inverted
        if len(self.low) < len(self.high):
            heapq.heappush(self.low, heapq.heappop(self.high))

    def median(self):
        if len(self.low) == len(self.high):
            return (self.low[0] + self.high[0]) / 2   # BUG 3: low[0] is wrong sign
        return self.low[0]                              # BUG 4: same sign issue
```

### Fixed Implementation

```python
import heapq

class MedianStream:
    def __init__(self):
        self.low = []    # max-heap: stores negated values (left half)
        self.high = []   # min-heap: stores actual values (right half)

    def add(self, num):
        heapq.heappush(self.low, -num)                        # push to max-heap (negate)
        heapq.heappush(self.high, -heapq.heappop(self.low))   # balance: move max of low to high
        if len(self.low) < len(self.high):                    # keep low >= high in size
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def median(self):
        if len(self.low) == len(self.high):
            return (-self.low[0] + self.high[0]) / 2   # average of two middle values
        return -self.low[0]                             # odd total: low has one extra
```

**Root cause:** Max-heap simulation requires negating values on push/pop. The original pushed raw values to `low`, breaking the heap invariant and median calculation.

**Time:** O(log N) per insertion · **Space:** O(N)

### Examples

```python
ms = MedianStream()
ms.add(1);  ms.median()   # → 1.0
ms.add(3);  ms.median()   # → 2.0
ms.add(2);  ms.median()   # → 2.0
ms.add(5);  ms.median()   # → 2.5
```

---

## Question 3 — Fix the Consistent Hashing Ring

**Score: 10 points**

### Problem

Servers sit on a hash ring. `addServer(id)` adds a server; `getServer(key)` maps a key to the next server clockwise on the ring.

### Broken Implementation

```python
import bisect

class ConsistentHashRing:
    def __init__(self):
        self.ring = {}
        self.sorted_keys = []

    def addServer(self, server_id):
        key = hash(server_id)
        self.ring[key] = server_id
        self.sorted_keys.append(key)     # BUG: list not kept sorted after append

    def getServer(self, key):
        if not self.ring:
            return None
        h = hash(key)
        idx = bisect.bisect_left(self.sorted_keys, h)
        if idx == len(self.sorted_keys):
            idx = 0                      # wrap around
        return self.ring[self.sorted_keys[idx]]
```

### Fixed Implementation

```python
import bisect

class ConsistentHashRing:
    def __init__(self):
        self.ring = {}
        self.sorted_keys = []

    def addServer(self, server_id):
        key = hash(server_id)
        self.ring[key] = server_id
        bisect.insort(self.sorted_keys, key)   # fix: insert in sorted position

    def getServer(self, key):
        if not self.ring:
            return None
        h = hash(key)
        idx = bisect.bisect_left(self.sorted_keys, h)
        if idx == len(self.sorted_keys):
            idx = 0
        return self.ring[self.sorted_keys[idx]]
```

**Root cause:** `list.append()` adds to the end without maintaining sort order. `bisect.bisect_left` requires a sorted list to work correctly. Fix: use `bisect.insort()` which inserts in the correct sorted position in O(N) time.

---

## Question 4 — Fix the Message Queue Processor

**Score: 10 points**

*(Same problem as Carpool Camping Trip Q4 — see that solution. Key fixes: negate priority for max-heap, add insertion index for FIFO tie-breaking.)*

```python
import heapq

def process_messages(messages):
    heap = []
    for i, (msg_id, priority) in enumerate(messages):
        heapq.heappush(heap, (-priority, i, msg_id))   # negate + index for stable order
    result = []
    while heap:
        _, _, msg_id = heapq.heappop(heap)
        result.append(msg_id)
    return result
```

---

## Question 5 — Password Rules Validation

**Score: 50 points**

### Problem

Return a sorted list of rule IDs (1–5) that a password **fails**:

| Rule | Requirement |
|------|-------------|
| 1 | Length ≥ 16 |
| 2 | Does not contain `"password"` (case-insensitive) |
| 3 | No character appears more than 4 times (case-sensitive) |
| 4 | Contains at least one uppercase AND one lowercase ASCII letter |
| 5 | Contains at least one of `*`, `#`, `@` |

**Function:** `validate(password: str) -> list[int]`

### Solution

```python
from collections import Counter

def validate(password):
    failed = []

    # Rule 1: length >= 16
    if len(password) < 16:
        failed.append(1)

    # Rule 2: does not contain "password" (case-insensitive)
    if "password" in password.lower():
        failed.append(2)

    # Rule 3: no character appears more than 4 times (case-sensitive)
    freq = Counter(password)
    if any(v > 4 for v in freq.values()):
        failed.append(3)

    # Rule 4: at least one uppercase AND one lowercase ASCII letter
    has_upper = any(c.isupper() and c.isascii() for c in password)
    has_lower = any(c.islower() and c.isascii() for c in password)
    if not has_upper or not has_lower:
        failed.append(4)

    # Rule 5: at least one of *, #, @
    if not any(c in ('*', '#', '@') for c in password):
        failed.append(5)

    return failed   # already in ascending order since we check 1→5 in order
```

### Complexity

- **Time:** O(N) — each rule is a single pass or O(1) lookup.
- **Space:** O(min(N, |Σ|)) for `Counter`.

### Examples

```python
validate("Aess10#")
# length=7 → fail 1; no "password" ✓; no char >4 ✓; has upper+lower ✓; has # ✓
# → [1]

validate("Password@")
# length=9 → fail 1; contains "password" → fail 2
# → [1, 2]

validate("aZ*")
# length=3 → fail 1; others pass
# → [1]

validate("Abcdefghijklmnop@1")
# length=18 ✓; no "password" ✓; no char >4 ✓; upper+lower ✓; has @ ✓
# → []

validate("aaaaaAbcdefghij@1")
# 'a' appears 5 times → fail 3
# → [3]
```

---

## Question 6 — Connection Grouping

**Score: 40 points**

### Problem

Process a chronological event log of `CONNECT`/`DISCONNECT` events for user pairs. After all events, partition all users (even those with degree 0) into two groups based on a threshold `target`:

- Group 0: users with final connection count (degree) **strictly less than** `target`.
- Group 1: users with final connection count **≥ target**.

Each group sorted lexicographically.

**Function:** `grouping(events, target) -> list[list[str]]`

### Solution

```python
from collections import defaultdict

def grouping(events, target):
    pair_status = {}    # canonical pair (min,max) → bool connected
    all_users = set()

    for event in events:
        cmd, u1, u2 = event[0], event[1], event[2]
        all_users.add(u1)
        all_users.add(u2)
        pair = (min(u1, u2), max(u1, u2))
        pair_status[pair] = (cmd == "CONNECT")

    # Count degree for each user from active edges
    degree = defaultdict(int)
    for (u1, u2), connected in pair_status.items():
        if connected:
            degree[u1] += 1
            degree[u2] += 1

    low = sorted(u for u in all_users if degree[u] < target)
    high = sorted(u for u in all_users if degree[u] >= target)

    return [low, high]
```

### Complexity

- **Time:** O(E + U log U) — one pass over events, then sort U users.
- **Space:** O(U + P) where P = distinct pairs, U = distinct users.

### Examples

```python
events = [
    ["CONNECT", "Alice", "Bob"],
    ["CONNECT", "Alice", "Carol"],
    ["CONNECT", "Bob", "Carol"],
    ["DISCONNECT", "Alice", "Bob"],
]
grouping(events, 2)
# Final edges: Alice-Carol, Bob-Carol
# Degrees: Alice=1, Bob=1, Carol=2
# target=2: low=[Alice, Bob] (degree<2), high=[Carol] (degree>=2)
# → [["Alice", "Bob"], ["Carol"]]

events = [
    ["CONNECT", "X", "Y"],
    ["CONNECT", "X", "Y"],   # duplicate → last wins = CONNECT (still connected)
]
grouping(events, 1)
# X degree=1, Y degree=1 → both >= 1
# → [[], ["X", "Y"]]

events = [
    ["CONNECT", "A", "B"],
    ["DISCONNECT", "A", "B"],
]
grouping(events, 1)
# Final: no active edges → A=0, B=0, both < 1
# → [["A", "B"], []]
```

---

---

# Karat — Singable Song (60 minutes)

---

## Question 1 — Python Multithreading vs Multiprocessing

**Score: 10 points**

### Question

Which statement correctly describes the difference between multithreading and multiprocessing in Python?

- A. Multithreading uses multiple CPU cores automatically, while multiprocessing runs on a single thread only.
- **B. Multithreading creates multiple threads within the same process and shares memory, while multiprocessing creates separate processes with separate memory spaces. ✓**
- C. Multithreading is always faster than multiprocessing for CPU-intensive tasks because threads are lightweight.
- D. Multiprocessing cannot run tasks in parallel, but multithreading can always achieve true parallelism in Python.

### Answer: B

### Explanation

| | Multithreading | Multiprocessing |
|---|---|---|
| Unit | Threads within one process | Separate OS processes |
| Memory | Shared (same heap) | Separate memory spaces |
| GIL impact | Blocked for CPU-bound Python code | Bypasses GIL — true CPU parallelism |
| Best for | I/O-bound tasks (network, disk) | CPU-bound tasks (computation) |
| Overhead | Low (shared address space) | Higher (process creation, IPC) |

- **A is wrong:** Multithreading does *not* automatically use multiple cores for Python code due to the GIL. Multiprocessing does run on multiple cores.
- **C is wrong:** Threads are *lighter weight*, but for CPU-intensive Python, multiprocessing is faster because it sidesteps the GIL.
- **D is wrong:** Multiprocessing *can* run tasks in true parallel. Multithreading cannot achieve true parallelism for CPU-bound Python work.

---

## Question 2 — Python Global Interpreter Lock (GIL)

**Score: 10 points**

### Question

What is the purpose of the Global Interpreter Lock (GIL) in CPython?

- A. It allows multiple Python threads to execute Python bytecode simultaneously.
- **B. It prevents multiple native threads from executing Python bytecode at the same time. ✓**
- C. It improves multiprocessing performance.
- D. It is used only in Python 2.

### Answer: B

### Explanation

The **GIL** is a mutex in CPython that ensures only **one thread executes Python bytecode at any given moment**, even on multi-core hardware.

**Why it exists:** CPython's memory management (reference counting for garbage collection) is not thread-safe. The GIL is a simple way to protect internal interpreter state without fine-grained locking.

**Practical consequences:**

| Scenario | Effect of GIL |
|---|---|
| CPU-bound threads | No speedup — threads take turns holding the GIL |
| I/O-bound threads | Minimal impact — GIL released during I/O waits |
| `multiprocessing` | Not affected — each process has its own GIL |
| C extensions | Can release the GIL manually (e.g. NumPy, pandas) |

- **A is wrong:** The GIL *prevents* simultaneous bytecode execution, not allows it.
- **C is wrong:** The GIL has no direct effect on multiprocessing.
- **D is wrong:** The GIL exists in CPython 2 *and* CPython 3 (efforts to remove it are ongoing in Python 3.13+).

---

## Question 3 — Singable Song (Vocal Range)

*(Already documented — see Thrilling Teleporters Q6)*

---

## Question 4 — Supermarket Shopping — Multi-Department & Closures

**Score: 50 points**

### Problem

Each product can belong to **multiple departments** (in preference order). Some departments are **closed**. For each product on the shopping list:

- If all its departments are closed → `unavailable_items`.
- Otherwise → use the **first open department** for the original plan.

Return:
- `original_visits` — visits following the list order (using first-open dept per product).
- `optimized_visits` — minimum distinct departments needed to cover all purchasable items.
- `visits_saved = original_visits - optimized_visits`.
- `departments_used` — sorted list of departments in the lexicographically smallest optimal assignment.
- `unavailable_items` — sorted list of unpurchasable product names.

**Function:** `shopping(products, shopping_list, closed_departments) -> tuple`

### Solution

```python
from itertools import product as iterproduct

def shopping(products, shopping_list, closed_departments):
    closed = set(closed_departments)

    # Build product → list of open departments (in preference order)
    prod_map = {}
    for name, depts in products:
        open_depts = [d for d in depts if d not in closed]
        prod_map[name] = open_depts

    unavailable_items = []
    purchasable = []   # list of open-dept lists for each purchasable item in list order

    for item in shopping_list:
        open_depts = prod_map.get(item, [])
        if not open_depts:
            unavailable_items.append(item)
        else:
            purchasable.append((item, open_depts))

    unavailable_items.sort()

    if not purchasable:
        return (0, 0, 0, [], unavailable_items)

    # Original visits: use first open dept per item, count dept transitions
    original_visits = 1
    prev_dept = purchasable[0][1][0]
    for _, open_depts in purchasable[1:]:
        dept = open_depts[0]
        if dept != prev_dept:
            original_visits += 1
        prev_dept = dept

    # Optimized visits: find assignment of one open dept per item that
    # minimizes distinct departments used. Brute-force over all combinations.
    # (Feasible for small P, M per constraints)
    best_count = float('inf')
    best_set = None

    dept_options = [open_depts for _, open_depts in purchasable]

    def backtrack(idx, current_set):
        nonlocal best_count, best_set
        # Prune: even if all remaining items reuse existing depts, can't beat best
        if len(current_set) >= best_count:
            return
        if idx == len(dept_options):
            n = len(current_set)
            s = tuple(sorted(current_set))
            if n < best_count or (n == best_count and s < best_set):
                best_count = n
                best_set = s
            return
        # Try adding a dept already in current_set first (no increase in count)
        tried = set()
        for dept in dept_options[idx]:
            if dept in current_set:
                if dept not in tried:
                    tried.add(dept)
                    backtrack(idx + 1, current_set)
        # Then try new depts
        for dept in dept_options[idx]:
            if dept not in current_set and dept not in tried:
                tried.add(dept)
                current_set.add(dept)
                backtrack(idx + 1, current_set)
                current_set.remove(dept)

    backtrack(0, set())

    optimized_visits = best_count
    visits_saved = original_visits - optimized_visits
    departments_used = sorted(best_set)

    return (original_visits, optimized_visits, visits_saved,
            departments_used, unavailable_items)
```

### Complexity

- **Building maps:** O(P + M)
- **Original visits:** O(M)
- **Optimized (backtracking):** O(Π|O_i|) worst case — feasible for small M and dept counts per constraints (M, P ≤ 15, distinct depts ≤ 30).

### Example Walkthrough

```
products = [["Apples","Produce"],["Milk","Dairy"],["Rice","Pantry"],
            ["Cheese","Dairy"],["Carrots","Produce"]]
            (each as [name, [dept1, ...]] — single-dept here)
shopping_list = ["Apples","Milk","Rice","Cheese","Carrots"]
closed_departments = {"Frozen"}

Original plan (first-open dept):
  Apples→Produce, Milk→Dairy, Rice→Pantry, Cheese→Dairy, Carrots→Produce
  Transitions: Produce→Dairy(+1), Dairy→Pantry(+1), Pantry→Dairy(+1), Dairy→Produce(+1)
  original_visits = 5

Optimized: all items covered by {Produce, Dairy, Pantry} → 3 distinct depts
  optimized_visits = 3, visits_saved = 2
  departments_used = ["Dairy", "Pantry", "Produce"]
  unavailable_items = []

→ (5, 3, 2, ["Dairy", "Pantry", "Produce"], [])
```

```python
# All unpurchasable
shopping(
    [["Ice Cream", ["Frozen"]], ["Milk", ["Dairy"]]],
    ["Ice Cream", "Milk"],
    {"Frozen", "Dairy"}
)
# → (0, 0, 0, [], ["Ice Cream", "Milk"])
```

---

---

# Karat — Snake Path (60 minutes)

---

## Question 1 — Advanced Python Gotchas: Late Binding in Lambdas

**Score: 50 points**

### Problem

Build `n` functions where `f_k(x) = k * x`. The starter appends lambdas in a loop, but all lambdas capture the variable `i` by reference (late binding), so every function uses the same final value of `i` at call time.

**Input:** integer `n`. **Output:** `f_0(1) f_1(1) … f_{n-1}(1)` (should be `0 1 2 … n-1`).

### Buggy Starter

```python
n = int(input())
funcs = []
for i in range(n):
    funcs.append(lambda x: i * x)   # BUG: i is looked up at call time, not captured at definition
print(*[f(1) for f in funcs])
# For n=4, prints: 3 3 3 3  (final i=3 for all)
```

### Fixed Implementation

```python
n = int(input())
funcs = []
for i in range(n):
    funcs.append(lambda x, k=i: k * x)   # fix: default argument captures i's current value
print(*[f(1) for f in funcs])
# For n=4, prints: 0 1 2 3
```

### Explanation: Late Binding vs Default-Argument Binding

**Late binding** — Python closures capture *variables* (names), not *values*. When `lambda x: i * x` is called later, it looks up `i` in the enclosing scope at that moment. After the loop ends, `i` holds the final value `n - 1`, so every lambda returns `(n-1) * x`.

**Default-argument binding** — Default parameter values are evaluated *once at definition time*. `lambda x, k=i: k * x` creates a new local `k` bound to the current value of `i` when that line executes. Each lambda gets its own `k`.

```python
# Alternative fixes:
# 1. functools.partial
from functools import partial
funcs = [partial(lambda k, x: k * x, i) for i in range(n)]

# 2. factory function
def make_f(k):
    return lambda x: k * x
funcs = [make_f(i) for i in range(n)]
```

### Examples

```
n=1  → 0
n=4  → 0 1 2 3
n=5  → 0 1 2 3 4
```

---

## Question 2 — Mutable Default Argument

**Score: 50 points**

### Problem

`record_batch(values)` should record only the integers in `values` for that call and return how many were recorded in *that call only*. The starter uses a mutable default list that persists across calls.

**Input:** `b` batches, each with `k` integers. **Output:** `b` lines, each printing `k` (the count for that batch only).

### Buggy Starter

```python
def record_batch(values, recorded=[]):   # BUG: [] created once, shared across all calls
    for v in values:
        recorded.append(v)
    return len(recorded)                  # BUG: returns total ever recorded, not this batch's count
```

### Fixed Implementation

```python
def record_batch(values, recorded=None):
    if recorded is None:
        recorded = []          # fresh list for each call
    for v in values:
        recorded.append(v)
    return len(recorded)       # equals len(values) since recorded starts empty each call
```

Or more directly:

```python
def record_batch(values):
    return len(values)         # no state needed at all
```

### Explanation

Python evaluates default argument expressions **once** at function definition time. `recorded=[]` creates a single list object that is reused on every call where `recorded` is not explicitly passed. Each `append` mutates that shared list, so `len(recorded)` grows across calls (1, 2, 3, …) instead of returning the per-call count.

**Fix:** Use `None` as the sentinel and create `recorded = []` inside the function body, which runs fresh on every call.

### Examples

```
b=3, batches: [5,3,1], [2,4], [7]
Buggy:  1, 3, 4   (cumulative lengths)
Fixed:  1, 2, 1   (per-batch counts = k values each)
```

---

## Question 3 — Shallow Row Replication

**Score: 50 points**

### Problem

Build an N×M matrix of zeros, set cell `(r, c)` to `v`, print space-separated row sums. The starter uses `[[0]*m]*n`, which repeats the **same inner list** `n` times — mutating one row affects all rows.

**Input:** `n m r c v`. **Output:** `n` row sums after the update.

### Buggy Starter

```python
n, m, r, c, v = map(int, input().split())
matrix = [[0] * m] * n       # BUG: all n rows are the same list object
matrix[r][c] = v              # sets column c to v in ALL rows, not just row r
print(*[sum(row) for row in matrix])
# For n=3, m=3, r=1, c=1, v=5: prints "5 5 5" instead of "0 5 0"
```

### Fixed Implementation

```python
n, m, r, c, v = map(int, input().split())
matrix = [[0] * m for _ in range(n)]   # fix: new list object per row
matrix[r][c] = v
print(*[sum(row) for row in matrix])
```

### Explanation: Reference Sharing vs Independent Rows

`[[0]*m]*n` multiplies a list — it creates `n` references to the **same** inner list object. All `matrix[0]`, `matrix[1]`, …, `matrix[n-1]` point to the identical object in memory.

`[[0]*m for _ in range(n)]` runs the expression `[0]*m` `n` times, creating `n` **distinct** list objects.

```python
# Verify:
a = [[0]*3]*3
a[0] is a[1]   # True  — same object

b = [[0]*3 for _ in range(3)]
b[0] is b[1]   # False — different objects
```

### Examples

```
Input: 3 3 1 1 5
matrix after fix:
  [0,0,0]  → sum=0
  [0,5,0]  → sum=5
  [0,0,0]  → sum=0
Output: 0 5 0

Input: 2 4 0 2 7
Output: 7 0
```

---

## Question 4 — Iterator / Map Consumed Once

**Score: 50 points**

### Problem

Read integers and print twice their sum. The starter maps integers via a `map` iterator and calls `sum` on it twice — but iterators are single-pass; the second `sum` sees an exhausted stream and returns 0.

**Input:** space-separated integers. **Output:** `2 * sum(integers)`.

### Buggy Starter

```python
parts = map(int, input().split())   # BUG: map returns a lazy iterator
total = sum(parts) + sum(parts)     # first sum exhausts the iterator; second sum → 0
print(total)
# Always prints sum once (not twice) for any non-empty input
```

### Fixed Implementation

```python
# Option 1: convert to list (reusable)
parts = list(map(int, input().split()))
print(sum(parts) + sum(parts))

# Option 2: compute once and double
parts = map(int, input().split())
s = sum(parts)
print(s * 2)

# Option 3: one-liner
print(sum(map(int, input().split())) * 2)
```

### Explanation: Iterator Consumption vs Reusable Containers

A `map` object is a **lazy iterator** — it yields values one at a time and remembers its position. Once `sum(parts)` pulls all values, the iterator is exhausted (`StopIteration`). The second `sum(parts)` starts iterating from the empty "done" state and immediately returns `0`.

`list(map(...))` materializes all values into a **list** (a reusable sequence). A list can be iterated any number of times without exhaustion.

**General rule:** If you need to traverse a stream more than once, either convert to `list`/`tuple` or compute the final answer in a single pass.

### Examples

```
Input: 1 2 3 4 5   → Output: 30   (sum=15, 15*2=30)
Input: -5 5        → Output: 0    (sum=0, 0*2=0)
Input: 7           → Output: 14
```

---

## Question 5 — Snake Path on a Grid

**Score: 50 points**

### Problem

Given a binary N×M board (`0`=open, `1`=blocked), a snake starts on any **edge cell** containing `0` and moves in a straight line (up/down/left/right) through `0` cells until it would leave the grid or hit a `1`. Return all **unique** paths (as `{"rows": [...], "columns": [...]}` dicts), deduplicated and sorted lexicographically by `(rows, columns)`.

**Function:** `snake_paths(board) -> list[dict]`

### Solution

```python
def snake_paths(board):
    N = len(board)
    M = len(board[0]) if N > 0 else 0

    def cell(r, c):
        return int(board[r][c])

    # All edge cells that are open
    edge_cells = set()
    for r in range(N):
        for c in range(M):
            if (r == 0 or r == N-1 or c == 0 or c == M-1) and cell(r, c) == 0:
                edge_cells.add((r, c))

    directions = [(-1,0),(1,0),(0,-1),(0,1)]  # up, down, left, right
    seen = set()
    paths = []

    for (sr, sc) in edge_cells:
        for dr, dc in directions:
            rows, cols = [sr], [sc]
            r, c = sr + dr, sc + dc
            while 0 <= r < N and 0 <= c < M and cell(r, c) == 0:
                rows.append(r)
                cols.append(c)
                r += dr
                c += dc
            key = (tuple(rows), tuple(cols))
            if key not in seen:
                seen.add(key)
                paths.append({"rows": rows[:], "columns": cols[:]})

    # Sort by (rows tuple, columns tuple)
    paths.sort(key=lambda p: (tuple(p["rows"]), tuple(p["columns"])))
    return paths
```

### Complexity

- **Time:** O(E · max(N,M)) where E = number of edge `0` cells.
- **Space:** O(K·L) for output paths + O(E) for deduplication keys.

### Examples

```python
board = [[0,1,0],
         [0,0,0],
         [0,1,0]]
# Edge 0-cells: (0,0),(0,2),(1,0),(1,2),(2,0),(2,2)
# Snake from (0,0) going right: hits (0,1)=1 immediately → path [(0,0)]
# Snake from (1,0) going right: (1,0)→(1,1)→(1,2)=0, then (1,3) OOB → rows=[1,1,1], cols=[0,1,2]
# etc.
paths = snake_paths(board)

board = [[0,0],[0,0]]
# Every edge cell, every direction → several paths, all deduplicated
```

---

## Question 6 — Game Map Traversal

*(Already documented — see Game Map Traversal Q5)*

---

---

# Karat — Social Grouping (60 minutes)

---

## Question 1 — Fix the File Log Reordering

**Score: 10 points**

### Problem

Reorder log entries (each a string starting with an identifier):
- Letter-logs (content is all letters) come before digit-logs.
- Letter-logs sorted lexicographically by content, then by identifier on tie.
- Digit-logs retain their original relative order.

### Broken Implementation

```python
def reorder_log_files(logs):
    letters, digits = [], []
    for log in logs:
        parts = log.split()
        if parts[1].isdigit():
            digits.append(log)
        else:
            letters.append(log)
    letters.sort()                      # BUG: sorts by full string (includes identifier first)
    return letters + digits
```

### Fixed Implementation

```python
def reorder_log_files(logs):
    letters, digits = [], []
    for log in logs:
        parts = log.split(maxsplit=1)   # split into [identifier, content]
        if parts[1][0].isdigit():
            digits.append(log)
        else:
            letters.append(log)
    # Sort by (content, identifier)
    letters.sort(key=lambda log: (log.split(maxsplit=1)[1], log.split(maxsplit=1)[0]))
    return letters + digits
```

**Root cause:** `letters.sort()` sorts lexicographically by the full string, meaning the identifier sorts first. The spec requires sorting by *content* first, then *identifier* as tiebreaker.

**Time:** O(N log N · L) where L = average log length · **Space:** O(N)

### Examples

```python
logs = ["dig1 8 1 5 1","let1 art can","dig2 3 6","let2 own kit dig","let3 art zero"]
reorder_log_files(logs)
# → ["let1 art can","let3 art zero","let2 own kit dig","dig1 8 1 5 1","dig2 3 6"]
# letter-logs sorted by content ("art can" < "art zero" < "own kit dig"), digits in original order
```

---

## Question 2 — Fix the Task Scheduler (Least Interval)

**Score: 10 points**

### Problem

Given tasks (list of chars) and cooldown `n`, same tasks must be at least `n` intervals apart. Return the minimum number of intervals to finish all tasks.

### Broken Implementation

```python
from collections import Counter

def least_interval(tasks, n):
    freq = Counter(tasks)
    max_freq = max(freq.values())
    # BUG: counts only tasks with max_freq, misses the +1 formula
    max_count = sum(1 for v in freq.values() if v == max_freq)
    return max_freq * (n + 1)    # BUG: missing max_count and len(tasks) comparison
```

### Fixed Implementation

```python
from collections import Counter

def least_interval(tasks, n):
    freq = Counter(tasks)
    max_freq = max(freq.values())
    max_count = sum(1 for v in freq.values() if v == max_freq)
    # Formula: slots needed = (max_freq - 1) * (n + 1) + max_count
    # But if tasks fill all slots, answer is just len(tasks)
    return max(len(tasks), (max_freq - 1) * (n + 1) + max_count)
```

### Explanation

The key formula: imagine arranging the most-frequent task in frames of size `(n+1)`. There are `(max_freq - 1)` full frames plus a final partial frame of size `max_count`. If enough distinct tasks exist to fill every idle slot, the answer is simply `len(tasks)`.

**Time:** O(N) · **Space:** O(1) (at most 26 distinct tasks)

### Examples

```python
least_interval(["A","A","A","B","B","B"], 2)
# max_freq=3, max_count=2 (A and B both appear 3 times)
# (3-1)*(2+1)+2 = 8, len=6 → max(6,8)=8
# → 8  (sequence: A B _ A B _ A B)

least_interval(["A","A","A","B","B","B"], 0)
# n=0: no cooldown → max(6, 2*1+2)=max(6,4)=6
# → 6

least_interval(["A","A","A","A","B","C","D"], 3)
# max_freq=4(A), max_count=1
# (4-1)*4+1=13, len=7 → 13
# → 13
```

---

## Question 3 — Fix the Course Schedule (Cycle Detection)

**Score: 10 points**

### Problem

Given `numCourses` and a list of prerequisite pairs `[a, b]` (must take `b` before `a`), return `True` if you can finish all courses (no cycle in the directed graph).

### Broken Implementation

```python
from collections import defaultdict, deque

def can_finish(numCourses, prerequisites):
    graph = defaultdict(list)
    in_degree = [0] * numCourses
    for a, b in prerequisites:
        graph[b].append(a)
        in_degree[a] += 1

    queue = deque([i for i in range(numCourses) if in_degree[i] == 0])
    count = 0
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
        # BUG: count never incremented — always returns False (0 != numCourses)

    return count == numCourses
```

### Fixed Implementation

```python
from collections import defaultdict, deque

def can_finish(numCourses, prerequisites):
    graph = defaultdict(list)
    in_degree = [0] * numCourses
    for a, b in prerequisites:
        graph[b].append(a)
        in_degree[a] += 1

    queue = deque([i for i in range(numCourses) if in_degree[i] == 0])
    count = 0
    while queue:
        node = queue.popleft()
        count += 1                      # fix: count each processed node
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return count == numCourses          # True if all nodes processed (no cycle)
```

**Root cause:** `count` was never incremented, so `count == numCourses` was always `False` (except for `numCourses == 0`). Kahn's topological sort counts processed nodes; if the count equals the total number of nodes, the graph is a DAG (no cycle).

**Time:** O(V + E) · **Space:** O(V + E)

### Examples

```python
can_finish(2, [[1,0]])          # → True  (0→1, no cycle)
can_finish(2, [[1,0],[0,1]])    # → False (cycle: 0↔1)
can_finish(4, [[1,0],[2,1],[3,2]])  # → True (linear chain)
```

---

## Question 4 — Fix the Text Justification

**Score: 10 points**

### Problem

Format words into lines of exactly `maxWidth` characters: spaces distributed evenly between words (left-heavy on unequal distribution). Last line is left-justified (single spaces, left-padded).

### Broken Implementation

```python
def full_justify(words, maxWidth):
    lines = []
    current, cur_len = [], 0
    for word in words:
        if cur_len + len(word) + len(current) > maxWidth:
            lines.append(current)
            current, cur_len = [], 0
        current.append(word)
        cur_len += len(word)

    lines.append(current)  # last line

    result = []
    for i, line in enumerate(lines):
        if i == len(lines) - 1 or len(line) == 1:
            result.append(' '.join(line).ljust(maxWidth))
        else:
            gaps = len(line) - 1
            total_spaces = maxWidth - sum(len(w) for w in line)
            space, extra = divmod(total_spaces, gaps)
            # BUG: builds string incorrectly — joins with wrong spacing
            result.append(' '.join(line))   # BUG: ignores calculated space distribution
    return result
```

### Fixed Implementation

```python
def full_justify(words, maxWidth):
    lines = []
    current, cur_len = [], 0
    for word in words:
        if cur_len + len(word) + len(current) > maxWidth:
            lines.append(current)
            current, cur_len = [], 0
        current.append(word)
        cur_len += len(word)
    lines.append(current)

    result = []
    for i, line in enumerate(lines):
        if i == len(lines) - 1 or len(line) == 1:
            # Last line or single word: left-justify with single spaces
            result.append(' '.join(line).ljust(maxWidth))
        else:
            gaps = len(line) - 1
            total_spaces = maxWidth - sum(len(w) for w in line)
            base, extra = divmod(total_spaces, gaps)
            row = ''
            for j, word in enumerate(line[:-1]):
                row += word + ' ' * (base + (1 if j < extra else 0))
            row += line[-1]                 # no trailing space after last word
            result.append(row)
    return result
```

**Root cause:** The fixed spacing was calculated correctly but then discarded — `' '.join(line)` ignores `base`/`extra` and puts exactly one space everywhere. The fix builds the row character-by-character using the computed distribution.

**Time:** O(N · W) where N = words, W = maxWidth · **Space:** O(N)

### Examples

```python
full_justify(["This","is","an","example","of","text","justification"], 16)
# → ["This    is    an", "example  of text", "justification   "]

full_justify(["What","must","be","acknowledgment","shall","be"], 16)
# → ["What   must  be", "acknowledgment  ", "shall be        "]
```

---

## Question 5 — Connection Grouping

*(Already documented — see Password Rules and Connection Grouping Q6)*

---

## Question 6 — Shopping by Department

*(Already documented — see Carpool Camping Trip Q5)*

---

---

# Karat — Sudoku Extended (60 minutes)

---

## Question 1 — Fix the Minimum Size Subarray Sum

**Score: 10 points**

### Problem

Given an array of positive integers and a target, return the minimum length of a contiguous subarray with sum ≥ target. Return `0` if none exists.

### Broken Implementation

```python
def min_subarray_len(target, nums):
    min_len = float('inf')
    total = 0
    left = 0
    for right in range(len(nums)):
        total += nums[right]
        while total >= target:
            min_len = min(min_len, right - left)   # BUG: off-by-one, should be right - left + 1
            total -= nums[left]
            left += 1
    return min_len if min_len != float('inf') else 0
```

### Fixed Implementation

```python
def min_subarray_len(target, nums):
    min_len = float('inf')
    total = 0
    left = 0
    for right in range(len(nums)):
        total += nums[right]
        while total >= target:
            min_len = min(min_len, right - left + 1)   # fix: inclusive window length
            total -= nums[left]
            left += 1
    return min_len if min_len != float('inf') else 0
```

**Root cause:** `right - left` gives window size minus 1 (e.g. a single-element window at `left==right` gives `0`). The correct inclusive length is `right - left + 1`.

**Time:** O(N) · **Space:** O(1)

### Examples

```python
min_subarray_len(7, [2,3,1,2,4,3])   # → 2  ([4,3])
min_subarray_len(4, [1,4,4])          # → 1  ([4])
min_subarray_len(11, [1,1,1,1,1,1])  # → 0  (sum never reaches 11)
min_subarray_len(7, [7])              # → 1
```

---

## Question 2 — Fix the Group Anagrams

**Score: 10 points**

*(Already documented — see Thrilling Teleporters Q3. Key fix: use `tuple(sorted(word))` as the grouping key in a `defaultdict`.)*

```python
from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)
    for word in words:
        key = tuple(sorted(word))
        groups[key].append(word)
    return list(groups.values())
```

---

## Question 3 — Fix the Find All Duplicates in Array

**Score: 10 points**

### Problem

Given an integer array where `1 ≤ arr[i] ≤ n`, some elements appear twice and others once. Return all elements that appear twice. Must run in O(N) time and O(1) extra space.

### Broken Implementation

```python
def find_duplicates(nums):
    result = []
    seen = set()
    for n in nums:
        if n in seen:
            result.append(seen)   # BUG: appends the set object, not the number n
        seen.add(n)
    return result
```

### Fixed Implementation

```python
def find_duplicates(nums):
    result = []
    for num in nums:
        idx = abs(num) - 1
        if nums[idx] < 0:
            result.append(abs(num))   # already negated → seen before
        else:
            nums[idx] = -nums[idx]    # mark as seen by negating
    return result
```

**Root cause (two bugs):**
1. `result.append(seen)` appends the entire `set` object instead of `n`.
2. The `set`-based approach uses O(N) extra space. The in-place sign-flip technique achieves O(1) extra space: use `arr[abs(num)-1]`'s sign as a visited flag.

**Time:** O(N) · **Space:** O(1) extra (output not counted)

### Examples

```python
find_duplicates([4,3,2,7,8,2,3,1])   # → [2, 3]
find_duplicates([1,1,2])              # → [1]
find_duplicates([1])                  # → []
```

---

## Question 4 — Fix the Decode String (Nested Encoding)

**Score: 10 points**

### Problem

Decode a string where `k[encoded_string]` means repeat `encoded_string` k times. Encoding may be nested (e.g. `2[a3[b]]` → `abbbabbb`).

### Broken Implementation

```python
def decode_string(s):
    stack = []
    current = ''
    k = 0
    for ch in s:
        if ch.isdigit():
            k = k * 10 + int(ch)
        elif ch == '[':
            stack.append((current, k))
            current = ''
            # BUG: k not reset to 0 after push
        elif ch == ']':
            prev, num = stack.pop()
            current = prev + current * num
        else:
            current += ch
    return current
```

### Fixed Implementation

```python
def decode_string(s):
    stack = []
    current = ''
    k = 0
    for ch in s:
        if ch.isdigit():
            k = k * 10 + int(ch)
        elif ch == '[':
            stack.append((current, k))
            current = ''
            k = 0              # fix: reset k for the next number inside brackets
        elif ch == ']':
            prev, num = stack.pop()
            current = prev + current * num
        else:
            current += ch
    return current
```

**Root cause:** After pushing onto the stack on `[`, `k` is never reset to `0`. If the outer bracket's `k` was `3`, the inner bracket's number would accumulate on top of `3` (e.g. inner `2` becomes `k = 3*10+2 = 32`), producing completely wrong repeat counts.

**Time:** O(N · max_k) · **Space:** O(N) for the stack

### Examples

```python
decode_string("3[a]2[bc]")         # → "aaabcbc"
decode_string("3[a2[c]]")          # → "accaccacc"
decode_string("2[abc]3[cd]ef")     # → "abcabccdcdcdef"
decode_string("2[a3[b]]")          # → "abbbabbb"
decode_string("abc")               # → "abc"
```

---

## Question 5 — Generalized Sudoku Validator

*(Already documented — see Monogram Q6)*

---

## Question 6 — Supermarket Shopping — Multi-Department & Closures

*(Already documented — see Singable Song Q4)*

---

---

# Karat — Supermarket (60 minutes)

---

## Question 1 — Fix the Event Ordering with Clock Skew

**Score: 10 points**

### Problem

Given distributed system logs as `(service_id, timestamp, message)`, sort globally by timestamp. For equal timestamps, preserve original input order (stable sort).

### Broken Implementation

```python
def reorder_logs(logs):
    logs.sort(key=lambda x: x[1])   # BUG: sort() is stable in Python, but this is correct...
    # Actually the real bug in typical starters is using sorted() with wrong key
    # or reversing the order, e.g.:
    return sorted(logs, key=lambda x: x[1], reverse=True)  # BUG: reverse=True sorts descending
```

### Fixed Implementation

```python
def reorder_logs(logs):
    # Python's sort is stable: equal timestamps preserve original (input) order
    return sorted(logs, key=lambda x: x[1])   # ascending timestamp, stable tie-breaking
```

For explicit stable tie-breaking with insertion index:

```python
def reorder_logs(logs):
    indexed = [(ts, i, log) for i, log in enumerate(logs) for ts in [log[1]]]
    indexed.sort(key=lambda x: (x[0], x[1]))   # sort by (timestamp, original_index)
    return [log for _, _, log in indexed]
```

**Root cause:** Common bugs include `reverse=True` (descending sort), sorting by full tuple (service_id sorts first), or using an unstable comparison. Python's `sort`/`sorted` is **stable** by default, so `key=lambda x: x[1]` is sufficient.

**Time:** O(N log N) · **Space:** O(N)

### Examples

```python
logs = [("svc1", 3, "msg_a"), ("svc2", 1, "msg_b"), ("svc3", 3, "msg_c"), ("svc4", 2, "msg_d")]
reorder_logs(logs)
# → [("svc2",1,"msg_b"), ("svc4",2,"msg_d"), ("svc1",3,"msg_a"), ("svc3",3,"msg_c")]
# Note: svc1 before svc3 — both ts=3, original order preserved (stable)
```

---

## Question 2 — Fix the Running Balance with Reversals

**Score: 10 points**

### Problem

Given financial transactions `(id, amount)` where negative amounts are reversals, return the running balance after each transaction.

### Broken Implementation

```python
def running_balance(transactions):
    balance = 0
    balances = []
    for tid, amount in transactions:
        if amount < 0:
            balance -= amount   # BUG: double-negates — subtracts a negative = adds the value
        else:
            balance += amount
        balances.append(balance)
    return balances
```

### Fixed Implementation

```python
def running_balance(transactions):
    balance = 0
    balances = []
    for tid, amount in transactions:
        balance += amount      # simply add the signed amount — negatives reduce balance correctly
        balances.append(balance)
    return balances
```

**Root cause:** `balance -= amount` when `amount < 0` computes `balance - (-x) = balance + x`, which adds the absolute value instead of subtracting. A reversal of `-50` should reduce the balance by 50, but the buggy code increases it by 50. Signed addition `balance += amount` handles all cases uniformly.

**Time:** O(N) · **Space:** O(N)

### Examples

```python
running_balance([("t1", 100), ("t2", -30), ("t3", 50), ("t4", -20)])
# → [100, 70, 120, 100]

running_balance([("t1", -10), ("t2", -20)])
# → [-10, -30]  (all reversals/withdrawals)
```

---

## Question 3 — Fix the Build System Dependency Resolver

**Score: 10 points**

### Problem

Given modules and their dependencies, return a valid build order (topological sort). A module can only be built after all its dependencies.

### Broken Implementation

```python
from collections import defaultdict, deque

def build_order(modules, dependencies):
    graph = defaultdict(list)
    in_degree = {m: 0 for m in modules}
    for a, b in dependencies:
        graph[b].append(a)    # b must be built before a
        in_degree[a] += 1

    queue = deque([m for m in modules if in_degree[m] == 0])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(modules):
        return []              # cycle detected — BUG in starters: often missing this check
    return order
```

*(The above is actually correct — typical bugs in starters:)*

### Typical Broken Variants and Fixes

```python
# BUG 1: edge direction reversed
for a, b in dependencies:
    graph[a].append(b)    # WRONG: builds a before b, but b is a's dependency
    in_degree[b] += 1

# FIXED:
for a, b in dependencies:
    graph[b].append(a)    # b → a means "b must come before a"
    in_degree[a] += 1

# BUG 2: modules not initialized in in_degree → KeyError for modules with no deps
in_degree = {}            # WRONG: only populated when seen in dependencies
# FIXED:
in_degree = {m: 0 for m in modules}

# BUG 3: no cycle detection → returns partial order silently
# FIXED: check len(order) == len(modules)
```

**Time:** O(V + E) · **Space:** O(V + E)

### Examples

```python
modules = ["A","B","C","D"]
deps    = [("B","A"), ("C","A"), ("D","B"), ("D","C")]
# A has no deps → first; B,C after A; D after B and C
build_order(modules, deps)  # → ["A","B","C","D"] or ["A","C","B","D"]

build_order(["X","Y"], [("X","Y"),("Y","X")])  # → [] (cycle)
```

---

## Question 4 — Fix the Expiring Key-Value Store

**Score: 10 points**

### Problem

Implement a key-value store with TTL. `SET key value time ttl` stores the value; it expires at `time + ttl`. `GET key time` returns the value if not expired, else `None`.

### Broken Implementation

```python
class TTLStore:
    def __init__(self):
        self.store = {}

    def set(self, key, value, time, ttl):
        self.store[key] = (value, ttl)    # BUG: stores ttl, not expiry time

    def get(self, key, time):
        if key not in self.store:
            return None
        value, ttl = self.store[key]
        if time > ttl:                    # BUG: compares current time to raw ttl, not expiry
            del self.store[key]
            return None
        return value
```

### Fixed Implementation

```python
class TTLStore:
    def __init__(self):
        self.store = {}   # key → (value, expiry_time)

    def set(self, key, value, time, ttl):
        self.store[key] = (value, time + ttl)   # fix: store absolute expiry time

    def get(self, key, time):
        if key not in self.store:
            return None
        value, expiry = self.store[key]
        if time >= expiry:                      # fix: expired at or after expiry time
            del self.store[key]
            return None
        return value
```

**Root cause:** The store saved the raw `ttl` duration instead of the absolute expiry timestamp `time + ttl`. The comparison `time > ttl` compared e.g. current_time=`105` against `ttl=10`, always expiring immediately. The fix computes `expiry = set_time + ttl` and checks `current_time >= expiry`.

**Time:** O(1) per operation · **Space:** O(K) where K = number of active keys

### Examples

```python
store = TTLStore()
store.set("a", "hello", 100, 10)   # expires at t=110
store.get("a", 105)                 # → "hello"   (105 < 110)
store.get("a", 110)                 # → None      (110 >= 110, expired)

store.set("b", "world", 50, 100)   # expires at t=150
store.set("b", "new",   80, 30)    # overwrites: expires at t=110
store.get("b", 100)                 # → "new"     (100 < 110)
store.get("b", 115)                 # → None      (115 >= 110)
```

---

## Question 5 — Supermarket Shopping — Multi-Department & Closures

*(Already documented — see Singable Song Q4)*

---

## Question 6 — Build Your Own Story

*(Already documented — see Build Your Own Story Q5)*

---

---

# Karat — Thrilling Teleporters Extended (60 minutes)

---

## Question 1 — Fix the Sliding Window Maximum

**Score: 10 points**

### Problem

Given an array and window size `k`, return the maximum value in each sliding window.

### Broken Implementation

```python
def max_sliding_window(nums, k):
    result = []
    for i in range(len(nums) - k + 1):
        result.append(max(nums[i:i+k]))   # correct logic but O(N·k) — not the typical bug
    return result

# More typical broken starter:
def max_sliding_window(nums, k):
    from collections import deque
    dq = deque()
    result = []
    for i, n in enumerate(nums):
        dq.append(n)                      # BUG 1: appends value, not index — can't evict old elements
        if len(dq) > k:
            dq.popleft()
        result.append(max(dq))            # BUG 2: O(k) max on every step instead of O(1)
    return result
```

### Fixed Implementation (O(N) monotonic deque)

```python
from collections import deque

def max_sliding_window(nums, k):
    dq = deque()   # stores indices; front always holds index of current window's max
    result = []

    for i, n in enumerate(nums):
        # Remove indices outside the current window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        # Maintain decreasing order: remove indices whose values are < current
        while dq and nums[dq[-1]] < n:
            dq.pop()
        dq.append(i)
        # Window is full — record the maximum (front of deque)
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
```

**Root cause:** Storing values instead of indices prevents eviction of out-of-window elements. The correct approach stores **indices** so stale elements can be removed when `dq[0] < i - k + 1`. The deque is kept in **decreasing value order** so the front always holds the window maximum in O(1).

**Time:** O(N) · **Space:** O(k)

### Examples

```python
max_sliding_window([1,3,-1,-3,5,3,6,7], 3)  # → [3,3,5,5,6,7]
max_sliding_window([1], 1)                    # → [1]
max_sliding_window([1,2,3,4,5], 2)           # → [2,3,4,5]
```

---

## Question 2 — Fix the Word Break Problem

**Score: 10 points**

### Problem

Given a string `s` and a dictionary of words, return `True` if `s` can be segmented into dictionary words.

### Broken Implementation

```python
def word_break(s, word_dict):
    word_set = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                # BUG: missing break — continues checking after finding a valid split
                # (not a correctness bug per se, just inefficiency — real bugs below)
    return dp[n]

# More typical broken starter:
def word_break(s, word_dict):
    word_set = set(word_dict)
    dp = [False] * len(s)    # BUG: array is len(s), not len(s)+1 — missing the base case index
    dp[0] = True
    for i in range(1, len(s)):          # BUG: should be range(1, len(s)+1)
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
    return dp[len(s) - 1]              # BUG: should check dp[len(s)], not dp[len(s)-1]
```

### Fixed Implementation

```python
def word_break(s, word_dict):
    word_set = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)   # dp[i] = True if s[:i] can be segmented
    dp[0] = True              # empty prefix is always valid

    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break         # optimization: stop once True found
    return dp[n]
```

**Root cause:** `dp` size is `len(s)` instead of `len(s)+1`, so `dp[0]` is the first character, not the empty prefix. The empty-string base case `dp[0] = True` sets the wrong index. The loop range and final return index are both off by one.

**Time:** O(N² · L) where L = average word length · **Space:** O(N)

### Examples

```python
word_break("leetcode", ["leet","code"])           # → True
word_break("applepenapple", ["apple","pen"])      # → True
word_break("catsandog", ["cats","dog","sand","and","cat"])  # → False
```

---

## Question 3 — Fix the Binary Search in Rotated Sorted Array

**Score: 10 points**

### Problem

Search for a target in a rotated sorted array (e.g. `[4,5,6,7,0,1,2]`). Return its index or `-1`.

### Broken Implementation

```python
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        # BUG: conditions check wrong half — doesn't account for rotation correctly
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

### Fixed Implementation

```python
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        # Determine which half is sorted
        if nums[lo] <= nums[mid]:           # left half is sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1               # target in sorted left half
            else:
                lo = mid + 1               # target in right half
        else:                              # right half is sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1              # target in sorted right half
            else:
                hi = mid - 1             # target in left half
    return -1
```

**Root cause:** The broken version does a plain binary search ignoring rotation — it moves purely based on `nums[mid] < target`, which fails when the pivot is between `mid` and the target. The fix first identifies which half is sorted, then checks if the target falls in that sorted range.

**Time:** O(log N) · **Space:** O(1)

### Examples

```python
search_rotated([4,5,6,7,0,1,2], 0)   # → 4
search_rotated([4,5,6,7,0,1,2], 3)   # → -1
search_rotated([1], 0)               # → -1
search_rotated([1,3], 3)             # → 1
```

---

## Question 4 — Fix the Minimum Window Substring

**Score: 10 points**

### Problem

Given strings `s` and `t`, return the smallest window in `s` containing all characters of `t`. Return `""` if none exists.

### Broken Implementation

```python
from collections import Counter

def min_window(s, t):
    need = Counter(t)
    have = {}
    formed = 0
    required = len(need)
    left = 0
    min_len = float('inf')
    result = ""

    for right, ch in enumerate(s):
        have[ch] = have.get(ch, 0) + 1
        if ch in need and have[ch] == need[ch]:
            formed += 1
        while formed == required:
            window_len = right - left    # BUG: off-by-one, should be right - left + 1
            if window_len < min_len:
                min_len = window_len
                result = s[left:right]   # BUG: excludes right character, should be s[left:right+1]
            # shrink window
            left_ch = s[left]
            have[left_ch] -= 1
            if left_ch in need and have[left_ch] < need[left_ch]:
                formed -= 1
            left += 1
    return result
```

### Fixed Implementation

```python
from collections import Counter

def min_window(s, t):
    if not t or not s:
        return ""
    need = Counter(t)
    have = {}
    formed = 0
    required = len(need)
    left = 0
    min_len = float('inf')
    result = ""

    for right, ch in enumerate(s):
        have[ch] = have.get(ch, 0) + 1
        if ch in need and have[ch] == need[ch]:
            formed += 1
        while formed == required:
            window_len = right - left + 1       # fix: inclusive length
            if window_len < min_len:
                min_len = window_len
                result = s[left:right + 1]      # fix: include right character
            left_ch = s[left]
            have[left_ch] -= 1
            if left_ch in need and have[left_ch] < need[left_ch]:
                formed -= 1
            left += 1
    return result
```

**Root cause:** Two off-by-one errors:
1. `right - left` gives window length minus 1 (a single-char window at `left==right` gives 0).
2. `s[left:right]` excludes `s[right]` — the Python slice end is exclusive, so `s[left:right+1]` is needed.

**Time:** O(|s| + |t|) · **Space:** O(|t|)

### Examples

```python
min_window("ADOBECODEBANC", "ABC")   # → "BANC"
min_window("a", "a")                 # → "a"
min_window("a", "aa")                # → ""
min_window("aa", "aa")               # → "aa"
```

---

## Question 5 — Quantum Chain Teleporters

**Score: 50 points**

### Problem

Extended Thrilling Teleporters with **chaining** and **quantum branching**:

- Effects are strings: `"from,to"` (standard), `"from,to1|to2"` (quantum — produces multiple destinations), `"from,+N"` or `"from,-N"` (relative boost).
- After landing on a square, keep applying effects until none applies.
- Quantum effects branch independently — track each branch separately.
- **Overshoot:** if `start + roll > last_square`, the player stays on `start` for that roll.
- **Loop guard:** if chaining on one die outcome revisits a square already in the current recursion stack, discard that branch.
- **Validity:** any index outside `[0, last_square]` invalidates that branch.

**Function:** `destinations(effects, die_sides, start, last_square) -> list[int]`

### Solution

```python
def destinations(effects, die_sides, start, last_square):
    # Parse effects into a map: from_square → list of destination lists (quantum branches)
    effect_map = {}
    for e in effects:
        parts = e.split(',', 1)
        src = int(parts[0])
        dest_str = parts[1]
        branches = []
        for branch in dest_str.split('|'):
            branch = branch.strip()
            if branch.startswith('+'):
                branches.append(('relative', int(branch)))
            elif branch.startswith('-'):
                branches.append(('relative', int(branch)))
            else:
                branches.append(('absolute', int(branch)))
        effect_map[src] = branches

    def chase(square, stack):
        """Return set of final squares reachable from `square` via chaining.
        `stack` is the set of squares on the current recursion path (loop detection)."""
        if square < 0 or square > last_square:
            return set()
        if square not in effect_map:
            return {square}   # no effect — terminal
        if square in stack:
            return set()      # loop detected — discard branch

        results = set()
        stack.add(square)
        for kind, val in effect_map[square]:
            if kind == 'relative':
                next_sq = square + val
            else:
                next_sq = val
            results |= chase(next_sq, set(stack))  # new stack copy per branch
        stack.discard(square)
        return results

    finals = set()
    for roll in range(1, die_sides + 1):
        raw = start + roll
        if raw > last_square:
            finals.add(start)   # overshoot: stay on start
            continue
        finals |= chase(raw, set())

    return sorted(finals)
```

### Walkthrough

```
effects1 = ["3,10", "10,14|15", "14,+3", "18,-5", "20,25", "25,18"]
die_sides=6, start=0, last_square=30

Roll 3: land 3 → effect: go 10 → quantum: go 14 or 15
  Branch 14: effect +3 → land 17 (no effect) → terminal 17
  Branch 15: no effect → terminal 15
  Finals from roll 3: {15, 17}

Rolls 1,2,4,5,6: no special squares → finals {1,2,4,5,6}

Sorted distinct: [1, 2, 4, 5, 6, 15, 17]
```

### Complexity

- **Parsing:** O(E)
- **Per roll:** DFS with loop detection; worst case exponential in chain depth, but loop guard ensures termination.

---

## Question 6 — Snake Nest Entrances

*(Already documented — see Passable Rows and Columns Q7)*

---

## Question 7 — Nearest Maze Exit

*(Already documented — see Passable Rows and Columns Q6)*

---

---

# Karat — Word Wrap with Hyphenation (45 minutes)

---

## Question 1 — Text Reflow — Fixed Width + Balanced Hyphen Distribution

**Score: 50 points**

### Problem

Given a maximum line width `W` and a text string of space-separated words:

1. **Short words** (`len(word) ≤ W`): emit as a single token.
2. **Long words** (`len(word) > W`): split into `k` fragments where:
   - Fragments `p1…p_{k-1}` are emitted as `pi + '-'`, each of length ≤ `W` (so `len(pi) ≤ W-1`).
   - Last fragment `pk` has no trailing hyphen, `len(pk) ≤ W`.
   - Choose **minimum** `k` first.
   - Given minimum `k`, distribute letters as **balanced** as possible (round-robin extra letters from `p1`).
3. **Pack tokens greedily** into lines: join tokens with single spaces; start a new line when the next token doesn't fit.

**Function:** `reflow_text(text: str, W: int) -> list[str]`

### Solution

```python
import math

def reflow_text(text: str, W: int) -> list[str]:
    if not text.strip():
        return []

    def split_long_word(word, W):
        """Split word into balanced fragments. Returns list of tokens (last has no hyphen)."""
        L = len(word)
        if L <= W:
            return [word]
        # Find minimum k: each of first k-1 fragments uses at most W-1 letters,
        # last fragment uses at most W letters.
        # Need: (k-1)*(W-1) + W >= L  →  k >= ceil((L - W) / (W - 1)) + 1
        k = math.ceil((L - W) / (W - 1)) + 1

        # Distribute L letters across k fragments as evenly as possible.
        # Caps: W-1 for first k-1, W for last.
        # Baseline: 1 letter each. Extras = L - k distributed round-robin from p1.
        base = L // k
        extra = L % k
        # But we must respect caps: base+1 <= W-1 for i<k, base+1 <= W for i=k
        # With minimum k this is guaranteed.
        lengths = []
        for i in range(k):
            cap = W - 1 if i < k - 1 else W
            length = min(base + (1 if i < extra else 0), cap)
            lengths.append(length)

        tokens = []
        pos = 0
        for i, ln in enumerate(lengths):
            fragment = word[pos:pos + ln]
            pos += ln
            if i < k - 1:
                tokens.append(fragment + '-')
            else:
                tokens.append(fragment)
        return tokens

    # Expand all words into tokens
    tokens = []
    for word in text.split():
        tokens.extend(split_long_word(word, W))

    # Greedily pack tokens into lines
    lines = []
    current_line = []
    current_len = 0

    for token in tokens:
        if not current_line:
            current_line = [token]
            current_len = len(token)
        else:
            needed = current_len + 1 + len(token)  # +1 for space
            if needed <= W:
                current_line.append(token)
                current_len = needed
            else:
                lines.append(' '.join(current_line))
                current_line = [token]
                current_len = len(token)

    if current_line:
        lines.append(' '.join(current_line))

    return lines
```

### Complexity

- **Per word:** O(L) to split + O(L) to emit tokens.
- **Overall:** O(L_txt) for tokenization and packing.

### Examples

```python
reflow_text("hello world", 5)
# tokens: ["hello", "world"]  (both ≤ 5)
# line1: "hello" (5), "world" doesn't fit → line2
# → ["hello", "world"]

reflow_text("abcdefgh", 3)
# L=8, W=3: k = ceil((8-3)/(3-1))+1 = ceil(2.5)+1 = 4
# base=2, extra=0 → lengths [2,2,2,2]
# caps: [2,2,2,3] — all fit
# tokens: ["ab-","cd-","ef-","gh"]
# each token length 3,3,3,2 — all ≤ W=3, each on its own line
# → ["ab-", "cd-", "ef-", "gh"]

reflow_text("hi abcdefgh", 4)
# "hi" → ["hi"]
# "abcdefgh" L=8, W=4: k=ceil((8-4)/3)+1=ceil(4/3)+1=2+1=3? 
#   k=ceil((8-4)/(4-1))+1=ceil(4/3)+1=2+1=3
#   base=2,extra=2 → lengths [3,3,2], caps [3,3,4]
#   tokens: ["abc-","def-","gh"]
# pack: "hi" (2); "abc-" → "hi abc-" (7>4) → new line
# → ["hi", "abc-", "def-", "gh"]
```

---

## Question 2 — Word Wrap With Hyphenation

**Score: 70 points**

### Problem

Same line-packing rules, but with a **simpler greedy hyphenation** (no balancing):

- If `len(word) > W`: while remaining suffix `> W`, emit `suffix[:W-1] + '-'` as a token, continue with `suffix[W-1:]`.
- Final suffix (length ≤ W): emit as-is (no trailing hyphen).
- Then pack all tokens greedily into lines with single spaces.

**Function:** `wrap_text(text: str, W: int) -> list[str]`

### Solution

```python
def wrap_text(text: str, W: int) -> list[str]:
    if not text:
        return []

    def tokenize(word, W):
        """Split a single word into hyphenated tokens using greedy W-1 rule."""
        if len(word) <= W:
            return [word]
        tokens = []
        while len(word) > W:
            tokens.append(word[:W - 1] + '-')
            word = word[W - 1:]
        tokens.append(word)
        return tokens

    # Tokenize all words
    all_tokens = []
    for word in text.split():
        all_tokens.extend(tokenize(word, W))

    # Greedy line packing
    lines = []
    current = []
    current_len = 0

    for token in all_tokens:
        if not current:
            current = [token]
            current_len = len(token)
        else:
            if current_len + 1 + len(token) <= W:
                current.append(token)
                current_len += 1 + len(token)
            else:
                lines.append(' '.join(current))
                current = [token]
                current_len = len(token)

    if current:
        lines.append(' '.join(current))

    return lines
```

### Complexity

- **Time:** O(L) — each character visited at most once during tokenization and packing.
- **Space:** O(L) for output.

### Difference from Q1

| | Q1 (Balanced) | Q2 (Greedy) |
|---|---|---|
| Fragment sizes | Balanced (round-robin extra letters) | All `W-1` except last |
| Min fragments | Computed via `ceil` | Naturally minimal (greedy fills maximally) |
| Complexity | O(log L + L) per word | O(L) per word |

### Examples

```python
wrap_text("hello world", 5)
# → ["hello", "world"]

wrap_text("abcdefgh", 3)
# W=3: "abcdefgh"[:2]+"-"="ab-", "cdefgh"[:2]+"-"="cd-", "efgh"[:2]+"-"="ef-", "gh"
# tokens: ["ab-","cd-","ef-","gh"]
# each fits on its own line (len=3,3,3,2)
# → ["ab-", "cd-", "ef-", "gh"]

wrap_text("the quick brown fox", 9)
# tokens: ["the","quick","brown","fox"] all ≤ 9
# "the quick" = 9 ✓; "brown" doesn't fit → new line
# "brown fox" = 9 ✓
# → ["the quick", "brown fox"]

wrap_text("", 5)
# → []

wrap_text("superlongword", 4)
# W=4: "sup-","erl-","ong-","wor-","d"  (each W-1=3 chars + hyphen)
# each token ≤ 4, each on own line
# → ["sup-", "erl-", "ong-", "wor-", "d"]
```
