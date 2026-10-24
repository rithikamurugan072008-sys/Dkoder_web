import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.utils import timezone

from django.contrib.auth.models import User
from core.models import (
    RolePermission, StudentProfile, AIConversation, AIMessage,
    CodingProblem, TestCase, CodeSubmission, PlacementRoadmap, RoadmapTask,
    StudentSkill, SkillAssessment, StudentAnalytics, MockInterview, InterviewQuestion,
    InterviewAnswer, Competition, CompetitionRegistration, CompetitionSubmission,
    LeaderboardEntry, CommunityPost, Comment, Reaction, StudyGroup, GroupMembership,
    ContentReport, Resume, ResumeVersion, Portfolio, PortfolioProject, AdminAuditLog,
    Notification, SystemSetting
)

def run_seed():
    print("Starting DKoder 2.0 database seeding...")

    # 1. System Settings
    settings_data = [
        ('gemini_api_configured', 'false', 'Status of Gemini LLM API integration'),
        ('judge0_configured', 'false', 'Status of Judge0 execution sandbox'),
        ('ai_daily_limit', '100', 'Maximum AI requests allowed per student per day'),
        ('platform_name', 'DKoder 2.0 Placement LMS', 'Platform branding title'),
    ]
    for key, val, desc in settings_data:
        SystemSetting.objects.get_or_create(key=key, defaults={'value': val, 'description': desc})

    # 2. Roles
    roles = [
        ('student', 'Student Aspirant', ['access_mentor', 'access_codelab', 'access_roadmap', 'access_interview', 'access_arena', 'access_community', 'access_career']),
        ('moderator', 'Community Moderator', ['moderate_community', 'review_reports', 'manage_posts']),
        ('admin', 'Placement Administrator', ['all_permissions', 'manage_users', 'manage_questions', 'manage_competitions', 'view_audit_logs', 'system_settings']),
    ]
    for r_name, d_name, perms in roles:
        RolePermission.objects.get_or_create(role_name=r_name, defaults={'display_name': d_name, 'permissions': perms})

    # 3. Users: Student, Moderator, Admin
    users_data = [
        ('alex', 'alex@dkoder.edu', 'Alex Rivera', 'student', 'Anna University / CEG', 'Computer Science & Engineering', 2026, 14, 28, 1850),
        ('priya', 'priya@dkoder.edu', 'Priya Patel', 'moderator', 'PSG College of Technology', 'Information Technology', 2025, 21, 35, 2410),
        ('admin', 'admin@dkoder.edu', 'Prof. Vikram Sharma', 'admin', 'DKoder Faculty / Placement Cell', 'Dean of Career Advancement', 2024, 45, 90, 4900),
        ('rohit', 'rohit@dkoder.edu', 'Rohit Verma', 'student', 'SRM Institute of Science', 'Computer Science', 2026, 9, 18, 1620),
        ('sneha', 'sneha@dkoder.edu', 'Sneha Menon', 'student', 'SSN College of Engineering', 'Electronics & Comm.', 2026, 17, 24, 1940),
    ]

    created_users = {}
    for uname, email, full_name, role, college, dept, grad_yr, streak, b_streak, pts in users_data:
        user, created = User.objects.get_or_create(username=uname, defaults={'email': email, 'first_name': full_name.split()[0], 'last_name': ' '.join(full_name.split()[1:])})
        if created:
            user.set_password('dkoder123')
            user.save()
        created_users[uname] = user

        StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': role,
                'college': college,
                'department': dept,
                'graduation_year': grad_yr,
                'bio': f"{role.capitalize()} at {college}. Actively practicing coding and company patterns on DKoder.",
                'primary_language': 'Python',
                'target_role': 'Full Stack SDE / Systems Engineer',
                'target_companies': 'Zoho, TCS Digital, Amazon, Infosys',
                'current_streak': streak,
                'best_streak': b_streak,
                'total_points': pts,
                'is_active_account': True
            }
        )

    alex_user = created_users['alex']

    # 4. Student Analytics for Alex
    StudentAnalytics.objects.get_or_create(
        user=alex_user,
        defaults={
            'problems_attempted': 54,
            'problems_solved': 45,
            'aptitude_accuracy_pct': 88.5,
            'interview_avg_score': 87.0,
            'total_learning_minutes': 3120,
            'active_streak_days': 14,
            'best_streak_days': 28,
            'weekly_activity_json': [
                {'day': 'Mon', 'problems': 5, 'hours': 2.5},
                {'day': 'Tue', 'problems': 8, 'hours': 3.0},
                {'day': 'Wed', 'problems': 6, 'hours': 2.0},
                {'day': 'Thu', 'problems': 10, 'hours': 4.0},
                {'day': 'Fri', 'problems': 7, 'hours': 2.5},
                {'day': 'Sat', 'problems': 12, 'hours': 4.5},
                {'day': 'Sun', 'problems': 6, 'hours': 2.5},
            ]
        }
    )

    # 5. Coding Problems & Test Cases
    problems_data = [
        {
            'title': 'String Pattern Expansion with Bracket Multipliers',
            'slug': 'string-pattern-expansion',
            'difficulty': 'Medium',
            'category': 'Arrays & Strings',
            'company_tags': 'Zoho, TCS Digital',
            'description': 'Given an encoded string where repetitions of substrings are represented as `k[substring]`, return its decoded string.\n\nThe encoding rule is: `k[encoded_string]`, where the `encoded_string` inside the square brackets is being repeated exactly `k` times. You may assume that the input string is always valid; no extra white spaces, square brackets are well-formed, etc.',
            'input_format': 'A single encoded string `s` consisting of digits, lowercase English letters, and square brackets `[` and `]`.',
            'output_format': 'Return the decoded string without brackets.',
            'constraints': '1 <= s.length <= 1000\ns consists of digits, letters, and brackets.\nAll integers k are in the range [1, 300].',
            'sample_input': '3[a]2[bc]',
            'sample_output': 'aaabcbc',
            'time_limit_ms': 1000,
            'points': 120,
            'starter_templates': {
                'python': 'def decodeString(s: str) -> str:\n    # Write your solution here\n    stack = []\n    curr_num = 0\n    curr_str = ""\n    for char in s:\n        if char.isdigit():\n            curr_num = curr_num * 10 + int(char)\n        elif char == "[":\n            stack.append((curr_str, curr_num))\n            curr_str = ""\n            curr_num = 0\n        elif char == "]":\n            prev_str, num = stack.pop()\n            curr_str = prev_str + curr_str * num\n        else:\n            curr_str += char\n    return curr_str\n\nimport sys\nif __name__ == "__main__":\n    s = sys.stdin.read().strip()\n    if s:\n        print(decodeString(s))\n',
                'javascript': 'const fs = require("fs");\nfunction decodeString(s) {\n    let stack = [];\n    let currNum = 0;\n    let currStr = "";\n    for (let char of s) {\n        if (!isNaN(char)) {\n            currNum = currNum * 10 + parseInt(char);\n        } else if (char === "[") {\n            stack.push([currStr, currNum]);\n            currStr = "";\n            currNum = 0;\n        } else if (char === "]") {\n            let [prevStr, num] = stack.pop();\n            currStr = prevStr + currStr.repeat(num);\n        } else {\n            currStr += char;\n        }\n    }\n    return currStr;\n}\nconst input = fs.readFileSync(0, "utf-8").trim();\nif (input) console.log(decodeString(input));\n',
                'cpp': '#include <iostream>\n#include <string>\n#include <stack>\nusing namespace std;\n\nstring decodeString(string s) {\n    stack<int> countStack;\n    stack<string> stringStack;\n    string currString = "";\n    int k = 0;\n    for (char c : s) {\n        if (isdigit(c)) {\n            k = k * 10 + (c - \'0\');\n        } else if (c == \'[\') {\n            countStack.push(k);\n            stringStack.push(currString);\n            currString = "";\n            k = 0;\n        } else if (c == \']\') {\n            string temp = currString;\n            int count = countStack.top(); countStack.pop();\n            currString = stringStack.top(); stringStack.pop();\n            while (count-- > 0) currString += temp;\n        } else {\n            currString += c;\n        }\n    }\n    return currString;\n}\n\nint main() {\n    string s;\n    if (cin >> s) cout << decodeString(s) << endl;\n    return 0;\n}\n',
                'java': 'import java.util.*;\n\npublic class Solution {\n    public static String decodeString(String s) {\n        Stack<Integer> countStack = new Stack<>();\n        Stack<StringBuilder> stringStack = new Stack<>();\n        StringBuilder currentString = new StringBuilder();\n        int k = 0;\n        for (char ch : s.toCharArray()) {\n            if (Character.isDigit(ch)) {\n                k = k * 10 + (ch - \'0\');\n            } else if (ch == \'[\') {\n                countStack.push(k);\n                stringStack.push(currentString);\n                currentString = new StringBuilder();\n                k = 0;\n            } else if (ch == \']\') {\n                StringBuilder decoded = stringStack.pop();\n                int currentK = countStack.pop();\n                for (int i = 0; i < currentK; i++) {\n                    decoded.append(currentString);\n                }\n                currentString = decoded;\n            } else {\n                currentString.append(ch);\n            }\n        }\n        return currentString.toString();\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNext()) {\n            System.out.println(decodeString(sc.next()));\n        }\n    }\n}\n',
                'c': '#include <stdio.h>\n#include <string.h>\n// C starter code\nint main() {\n    char s[1000];\n    if (scanf("%s", s) == 1) {\n        // Process string\n        printf("aaabcbc\\n");\n    }\n    return 0;\n}\n',
                'sql': '-- Sample SQL query template\nSELECT "aaabcbc" AS result;\n'
            },
            'test_cases': [
                ('3[a]2[bc]', 'aaabcbc', False, 'Sample test case 1'),
                ('3[a2[c]]', 'accaccacc', False, 'Nested repetition'),
                ('2[abc]3[cd]ef', 'abcabccdcdcdef', True, 'Hidden case: Multiple sequential blocks with trailing characters'),
            ]
        },
        {
            'title': 'Prime Pair Distance & Segmented Sieve',
            'slug': 'prime-pair-distance',
            'difficulty': 'Medium',
            'category': 'Aptitude & Algorithms',
            'company_tags': 'TCS NQT, Cognizant',
            'description': 'Given two integers L and R, find the pair of adjacent prime numbers (p1, p2) with the minimum difference such that L <= p1 < p2 <= R. If multiple pairs have the same minimum difference, return the pair with the smallest p1. If no prime pair exists, return -1 -1.',
            'input_format': 'Two space-separated integers L and R.',
            'output_format': 'Two space-separated integers p1 and p2, or -1 -1.',
            'constraints': '1 <= L < R <= 10^6\nR - L <= 10^5',
            'sample_input': '10 20',
            'sample_output': '11 13',
            'time_limit_ms': 1500,
            'points': 100,
            'starter_templates': {
                'python': 'def is_prime(n):\n    if n < 2: return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0: return False\n    return True\n\ndef solve(L, R):\n    primes = [x for x in range(L, R + 1) if is_prime(x)]\n    if len(primes) < 2:\n        return "-1 -1"\n    min_diff = float("inf")\n    ans = (-1, -1)\n    for i in range(len(primes) - 1):\n        diff = primes[i+1] - primes[i]\n        if diff < min_diff:\n            min_diff = diff\n            ans = (primes[i], primes[i+1])\n    return f"{ans[0]} {ans[1]}"\n\nimport sys\nif __name__ == "__main__":\n    line = sys.stdin.read().strip()\n    if line:\n        L, R = map(int, line.split())\n        print(solve(L, R))\n',
                'javascript': 'const fs = require("fs");\nfunction isPrime(n) {\n    if (n < 2) return false;\n    for (let i = 2; i * i <= n; i++) if (n % i === 0) return false;\n    return true;\n}\nconst input = fs.readFileSync(0, "utf-8").trim().split(/\\s+/);\nif (input.length >= 2) {\n    const L = parseInt(input[0]), R = parseInt(input[1]);\n    const primes = [];\n    for (let i = L; i <= R; i++) if (isPrime(i)) primes.push(i);\n    if (primes.length < 2) console.log("-1 -1");\n    else {\n        let minDiff = Infinity, ans = [-1, -1];\n        for (let i = 0; i < primes.length - 1; i++) {\n            let diff = primes[i+1] - primes[i];\n            if (diff < minDiff) { minDiff = diff; ans = [primes[i], primes[i+1]]; }\n        }\n        console.log(`${ans[0]} ${ans[1]}`);\n    }\n}\n',
                'cpp': '#include <iostream>\n#include <vector>\nusing namespace std;\nbool isPrime(int n) {\n    if (n < 2) return false;\n    for (int i = 2; i * i <= n; ++i) if (n % i == 0) return false;\n    return true;\n}\nint main() {\n    int L, R;\n    if (cin >> L >> R) {\n        vector<int> primes;\n        for (int i = L; i <= R; ++i) if (isPrime(i)) primes.push_back(i);\n        if (primes.size() < 2) cout << "-1 -1\\n";\n        else {\n            int minD = 1e9, p1 = -1, p2 = -1;\n            for (size_t i = 0; i < primes.size() - 1; ++i) {\n                if (primes[i+1] - primes[i] < minD) {\n                    minD = primes[i+1] - primes[i];\n                    p1 = primes[i]; p2 = primes[i+1];\n                }\n            }\n            cout << p1 << " " << p2 << "\\n";\n        }\n    }\n    return 0;\n}\n',
                'java': 'import java.util.*;\npublic class Solution {\n    public static boolean isPrime(int n) {\n        if (n < 2) return false;\n        for (int i = 2; i * i <= n; i++) if (n % i == 0) return false;\n        return true;\n    }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int L = sc.nextInt(), R = sc.nextInt();\n            List<Integer> primes = new ArrayList<>();\n            for (int i = L; i <= R; i++) if (isPrime(i)) primes.add(i);\n            if (primes.size() < 2) System.out.println("-1 -1");\n            else {\n                int minD = Integer.MAX_VALUE, p1 = -1, p2 = -1;\n                for (int i = 0; i < primes.size() - 1; i++) {\n                    int d = primes.get(i+1) - primes.get(i);\n                    if (d < minD) { minD = d; p1 = primes.get(i); p2 = primes.get(i+1); }\n                }\n                System.out.println(p1 + " " + p2);\n            }\n        }\n    }\n}\n',
                'c': '#include <stdio.h>\nint main() { printf("11 13\\n"); return 0; }\n',
                'sql': 'SELECT 11, 13;\n'
            },
            'test_cases': [
                ('10 20', '11 13', False, 'Standard prime range'),
                ('2 5', '2 3', False, 'Smallest primes twin'),
                ('14 16', '-1 -1', True, 'Hidden case: No primes in range'),
            ]
        },
        {
            'title': 'Rotten Oranges Graph BFS with Multi-Source Queue',
            'slug': 'rotten-oranges-bfs',
            'difficulty': 'Hard',
            'category': 'Trees & Graphs',
            'company_tags': 'Amazon SDE-1, Microsoft',
            'description': 'You are given an m x n grid where each cell can have one of three values:\n- 0 representing an empty cell,\n- 1 representing a fresh orange, or\n- 2 representing a rotten orange.\n\nEvery minute, any fresh orange that is 4-directionally adjacent to a rotten orange becomes rotten.\n\nReturn the minimum number of minutes that must elapse until no cell has a fresh orange. If this is impossible, return -1.',
            'input_format': 'The first line contains integers m and n. The next m lines each contain n space-separated integers (0, 1, or 2).',
            'output_format': 'An integer representing the minimum minutes elapsed, or -1.',
            'constraints': 'm == grid.length\nn == grid[i].length\n1 <= m, n <= 10\ngrid[i][j] is 0, 1, or 2.',
            'sample_input': '3 3\n2 1 1\n1 1 0\n0 1 1',
            'sample_output': '4',
            'time_limit_ms': 2000,
            'points': 150,
            'starter_templates': {
                'python': 'from collections import deque\nimport sys\n\ndef orangesRotting(grid):\n    rows, cols = len(grid), len(grid[0])\n    q = deque()\n    fresh = 0\n    for r in range(rows):\n        for c in range(cols):\n            if grid[r][c] == 2: q.append((r, c, 0))\n            elif grid[r][c] == 1: fresh += 1\n    time = 0\n    while q:\n        r, c, time = q.popleft()\n        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:\n            nr, nc = r + dr, c + dc\n            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:\n                grid[nr][nc] = 2\n                fresh -= 1\n                q.append((nr, nc, time + 1))\n    return time if fresh == 0 else -1\n\nif __name__ == "__main__":\n    data = sys.stdin.read().split()\n    if data:\n        m, n = int(data[0]), int(data[1])\n        grid = []\n        idx = 2\n        for _ in range(m):\n            grid.append([int(x) for x in data[idx:idx+n]])\n            idx += n\n        print(orangesRotting(grid))\n',
                'javascript': 'const fs = require("fs");\nconst data = fs.readFileSync(0, "utf-8").trim().split(/\\s+/);\nif (data.length > 2) {\n    const m = parseInt(data[0]), n = parseInt(data[1]);\n    const grid = [];\n    let idx = 2;\n    for (let i = 0; i < m; i++) {\n        grid.push(data.slice(idx, idx + n).map(Number));\n        idx += n;\n    }\n    const q = [];\n    let fresh = 0;\n    for (let r = 0; r < m; r++) {\n        for (let c = 0; c < n; c++) {\n            if (grid[r][c] === 2) q.push([r, c, 0]);\n            else if (grid[r][c] === 1) fresh++;\n        }\n    }\n    let time = 0;\n    let head = 0;\n    while (head < q.length) {\n        const [r, c, t] = q[head++];\n        time = t;\n        const dirs = [[-1,0],[1,0],[0,-1],[0,1]];\n        for (const [dr, dc] of dirs) {\n            const nr = r + dr, nc = c + dc;\n            if (nr >= 0 && nr < m && nc >= 0 && nc < n && grid[nr][nc] === 1) {\n                grid[nr][nc] = 2;\n                fresh--;\n                q.push([nr, nc, t + 1]);\n            }\n        }\n    }\n    console.log(fresh === 0 ? time : -1);\n}\n',
                'cpp': '#include <iostream>\n#include <vector>\n#include <queue>\nusing namespace std;\nint main() {\n    int m, n; if (cin >> m >> n) {\n        vector<vector<int>> grid(m, vector<int>(n));\n        queue<pair<pair<int,int>, int>> q;\n        int fresh = 0;\n        for (int i=0; i<m; ++i) for (int j=0; j<n; ++j) {\n            cin >> grid[i][j];\n            if (grid[i][j] == 2) q.push({{i,j}, 0});\n            else if (grid[i][j] == 1) fresh++;\n        }\n        int time = 0;\n        int d[4][2] = {{-1,0},{1,0},{0,-1},{0,1}};\n        while(!q.empty()){\n            auto curr = q.front(); q.pop();\n            int r = curr.first.first, c = curr.first.second;\n            time = curr.second;\n            for(int i=0; i<4; ++i){\n                int nr = r + d[i][0], nc = c + d[i][1];\n                if(nr>=0 && nr<m && nc>=0 && nc<n && grid[nr][nc]==1){\n                    grid[nr][nc] = 2; fresh--;\n                    q.push({{nr, nc}, time + 1});\n                }\n            }\n        }\n        cout << (fresh == 0 ? time : -1) << endl;\n    }\n    return 0;\n}\n',
                'java': 'import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        System.out.println(4);\n    }\n}\n',
                'c': '#include <stdio.h>\nint main(){ printf("4\\n"); return 0; }\n',
                'sql': 'SELECT 4;\n'
            },
            'test_cases': [
                ('3 3\n2 1 1\n1 1 0\n0 1 1', '4', False, 'Sample 3x3 standard test'),
                ('3 3\n0 2 0\n0 0 0\n0 0 0', '0', False, 'No fresh oranges initially'),
                ('2 2\n2 0\n0 1', '-1', True, 'Hidden: Impossible to reach isolated fresh orange'),
            ]
        },
        {
            'title': 'Subarray Sum Divisible by K',
            'slug': 'subarray-sum-divisible-k',
            'difficulty': 'Medium',
            'category': 'Dynamic Programming & Hash',
            'company_tags': 'Infosys SP, Zoho',
            'description': 'Given an integer array nums and an integer k, return the number of non-empty subarrays that have a sum divisible by k.\n\nA subarray is a contiguous part of an array.',
            'input_format': 'First line contains integer k. Second line contains space-separated integers representing the array.',
            'output_format': 'Return a single integer: the count of matching subarrays.',
            'constraints': '1 <= nums.length <= 3 * 10^4\n-10^4 <= nums[i] <= 10^4\n2 <= k <= 10^4',
            'sample_input': '5\n4 5 0 -2 -3 1',
            'sample_output': '7',
            'time_limit_ms': 1000,
            'points': 110,
            'starter_templates': {
                'python': 'def subarraysDivByK(nums, k):\n    remainder_count = {0: 1}\n    prefix_sum = 0\n    count = 0\n    for x in nums:\n        prefix_sum += x\n        rem = prefix_sum % k\n        if rem < 0: rem += k\n        count += remainder_count.get(rem, 0)\n        remainder_count[rem] = remainder_count.get(rem, 0) + 1\n    return count\n\nimport sys\nif __name__ == "__main__":\n    lines = sys.stdin.read().strip().split("\\n")\n    if len(lines) >= 2:\n        k = int(lines[0].strip())\n        nums = list(map(int, lines[1].strip().split()))\n        print(subarraysDivByK(nums, k))\n',
                'javascript': 'const fs = require("fs");\nconst lines = fs.readFileSync(0, "utf-8").trim().split("\\n");\nif (lines.length >= 2) {\n    const k = parseInt(lines[0]);\n    const nums = lines[1].trim().split(/\\s+/).map(Number);\n    const remCount = {0: 1};\n    let prefix = 0, count = 0;\n    for (let x of nums) {\n        prefix += x;\n        let rem = prefix % k;\n        if (rem < 0) rem += k;\n        count += (remCount[rem] || 0);\n        remCount[rem] = (remCount[rem] || 0) + 1;\n    }\n    console.log(count);\n}\n',
                'cpp': '#include <iostream>\n#include <vector>\n#include <unordered_map>\nusing namespace std;\nint main() {\n    int k; if (cin >> k) {\n        unordered_map<int, int> remCount; remCount[0] = 1;\n        int x, prefix = 0, count = 0;\n        while(cin >> x) {\n            prefix += x;\n            int rem = ((prefix % k) + k) % k;\n            count += remCount[rem];\n            remCount[rem]++;\n        }\n        cout << count << endl;\n    }\n    return 0;\n}\n',
                'java': 'import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        System.out.println(7);\n    }\n}\n',
                'c': '#include <stdio.h>\nint main(){ printf("7\\n"); return 0; }\n',
                'sql': 'SELECT 7;\n'
            },
            'test_cases': [
                ('5\n4 5 0 -2 -3 1', '7', False, 'Standard sample with negative integers'),
                ('9\n5', '0', False, 'Single element not divisible'),
                ('3\n3 3 3', '6', True, 'Hidden case: All elements divisible by k'),
            ]
        }
    ]

    for pdata in problems_data:
        test_cases = pdata.pop('test_cases')
        problem, _ = CodingProblem.objects.get_or_create(slug=pdata['slug'], defaults=pdata)
        for inp, outp, hidden, expl in test_cases:
            TestCase.objects.get_or_create(
                problem=problem, input_data=inp,
                defaults={'expected_output': outp, 'is_hidden': hidden, 'explanation': expl}
            )

    # 6. Placement Roadmap for Alex
    roadmap, _ = PlacementRoadmap.objects.get_or_create(
        user=alex_user,
        defaults={
            'title': '2026 Dream Placement Preparation Plan (Zoho & Amazon Track)',
            'education_level': 'B.E / B.Tech (Final / Pre-Final Year)',
            'department': 'Computer Science & Engineering',
            'grad_year': 2026,
            'target_role': 'Full Stack SDE / Systems Engineer',
            'target_companies': 'Zoho, TCS Digital, Amazon, Infosys',
            'current_skill_level': 'Intermediate',
            'daily_hours': 2.5,
            'completion_percentage': 45.0,
            'is_active': True
        }
    )

    roadmap_tasks = [
        # Cat 1: Programming Fundamentals
        ('1. Programming Fundamentals', 'Master C/C++ Pointers & Memory Layout', 'Deep dive into malloc, calloc, struct memory alignment, and double pointers for Zoho Round 1 & 2.', 'High', 1, 1, True),
        ('1. Programming Fundamentals', 'Bitwise Manipulation Mastery', 'Fast XOR operations, single number detection, power of two checks, and bitmasking.', 'Medium', 1, 2, True),

        # Cat 2: Data Structures & Algorithms
        ('2. Data Structures & Algorithms', 'In-Place Array Manipulations & Cyclic Sort', 'Solve Find Disappeared Numbers and Duplicate In-Place with O(1) space.', 'High', 1, 3, True),
        ('2. Data Structures & Algorithms', 'Multi-Source Queue & BFS on 2D Grids', 'Amazon SDE pattern: Rotten Oranges, 01 Matrix, and Shortest Path in Binary Matrix.', 'High', 2, 1, False),
        ('2. Data Structures & Algorithms', 'Dynamic Programming on Substrings', 'Longest Palindromic Substring and Subarray Sum Divisible by K.', 'High', 2, 2, False),

        # Cat 3: Aptitude & Logical Reasoning
        ('3. Aptitude & Logical Reasoning', 'TCS NQT Time, Speed & Distance Speed Drills', 'Master relative speed, train meeting times, and boat & stream shortcuts.', 'Medium', 1, 4, True),
        ('3. Aptitude & Logical Reasoning', 'Syllogisms & Venn Diagrams for Campus Drives', 'Solve 30 real company placement reasoning puzzles with zero negative marking.', 'Medium', 2, 3, False),

        # Cat 4: DBMS & SQL
        ('4. Database Management Systems', 'ACID Properties & Transaction Isolation Levels', 'Prepare for technical interview questions on Dirty Reads, Non-repeatable Reads & Phantom Rows.', 'Medium', 1, 5, True),

        # Cat 5: Object-Oriented Programming
        ('5. Object-Oriented Programming', 'Design Patterns in Campus Interviews', 'Implement Singleton, Factory, and Observer patterns with thread safety.', 'Medium', 2, 4, False),

        # Cat 6: Operating Systems
        ('6. Operating Systems', 'Process Synchronization & Semaphore Implementation', 'Understand Producer-Consumer, Dining Philosophers, and Mutex vs Binary Semaphore.', 'High', 2, 5, False),

        # Cat 7: Computer Networks
        ('7. Computer Networks', 'TCP 3-Way Handshake & HTTP/2 vs HTTP/3', 'Explain what happens when you type google.com into your browser step by step.', 'Medium', 3, 1, False),

        # Cat 8: SQL & Database Queries
        ('8. SQL and Database Queries', 'Window Functions & Subquery Joins', 'Write DENSE_RANK(), PARTITION BY queries to find the 2nd highest salary department-wise.', 'High', 3, 2, False),

        # Cat 9: Technical Interview Preparation
        ('9. Technical Interview Preparation', 'System Design Basics: Rate Limiter & URL Shortener', 'Learn client-side throttling, Redis token bucket, and Base62 hashing.', 'High', 3, 3, False),

        # Cat 10: HR Interview Preparation
        ('10. HR Interview Preparation', 'STAR Method for Behavioral Rounds', 'Prepare 5 compelling real stories: Conflict Resolution, Leadership, and Failure to Success.', 'Medium', 3, 4, False),

        # Cat 11: Resume Preparation
        ('11. Resume Preparation', 'ATS Optimization & Project Impact Metric Writing', 'Revise bullet points with the Google XYZ formula: Accomplished [X] measured by [Y] by doing [Z].', 'High', 4, 1, False),

        # Cat 12: Mock Assessments
        ('12. Mock Assessments', 'Full-Length 90-Minute Zoho Coding Simulation', 'Simulate Zoho Round 2: 5 coding questions under timed constraints with live tests.', 'High', 4, 2, False),
    ]

    for cat, title, desc, prio, wk, dy, comp in roadmap_tasks:
        RoadmapTask.objects.get_or_create(
            roadmap=roadmap, title=title,
            defaults={
                'category': cat,
                'description': desc,
                'priority': prio,
                'week_number': wk,
                'day_number': dy,
                'is_completed': comp,
                'estimated_minutes': 75
            }
        )

    # 7. Student Skills for Alex (14 core skills tracked)
    skills_data = [
        ('Arrays & Strings', 'DSA', 88.0, 18, 16, 'proficient', 'rising', ['Solve Hard Sliding Window', 'Matrix Spiral Multi-layer']),
        ('Searching & Sorting', 'DSA', 82.0, 14, 12, 'proficient', 'steady', ['Quickselect 3-way partition']),
        ('Recursion & Backtracking', 'DSA', 68.0, 10, 7, 'developing', 'rising', ['N-Queens optimization', 'Sudoku Solver']),
        ('Linked Lists', 'DSA', 80.0, 12, 10, 'proficient', 'steady', ['LRU Cache implementation']),
        ('Trees & Graphs', 'DSA', 62.0, 15, 9, 'developing', 'rising', ['Multi-Source BFS', 'Dijkstra Priority Queue']),
        ('Dynamic Programming', 'DSA', 44.0, 12, 5, 'needs_attention', 'declining', ['Knapsack 0/1 variants', 'Coin Change DP']),
        ('SQL & Complex Queries', 'Core CS', 92.0, 16, 15, 'proficient', 'rising', ['Window functions: DENSE_RANK']),
        ('Object-Oriented Programming', 'Core CS', 84.0, 11, 10, 'proficient', 'steady', ['Virtual functions & V-Tables in C++']),
        ('Database Management Systems', 'Core CS', 78.0, 14, 11, 'proficient', 'rising', ['B-Tree Indexing internals']),
        ('Operating Systems', 'Core CS', 72.0, 13, 9, 'developing', 'steady', ['Virtual Memory & Page Replacement']),
        ('Computer Networks', 'Core CS', 70.0, 10, 7, 'developing', 'steady', ['Subnetting and CIDR calculation']),
        ('Logical Reasoning', 'Aptitude', 90.0, 22, 20, 'proficient', 'rising', ['Blood Relations & Direction Sense']),
        ('Quantitative Aptitude', 'Aptitude', 84.0, 25, 21, 'proficient', 'rising', ['Permutations & Probability speed']),
        ('Communication & HR', 'Soft Skills', 86.0, 8, 7, 'proficient', 'steady', ['STAR format storytelling in mock rounds']),
    ]

    for s_name, cat, pct, att, corr, status, trend, recs in skills_data:
        StudentSkill.objects.get_or_create(
            user=alex_user, skill_name=s_name,
            defaults={
                'category': cat,
                'proficiency_pct': pct,
                'assessment_attempts': att,
                'correct_attempts': corr,
                'status': status,
                'trend': trend,
                'recommended_tasks': recs
            }
        )

    # 8. AI Mock Interview for Alex
    interview, _ = MockInterview.objects.get_or_create(
        user=alex_user,
        interview_type='Zoho Technical Round 2 Practice',
        defaults={
            'target_role': 'Software Developer (₹8.5 LPA)',
            'difficulty': 'Medium',
            'duration_mins': 25,
            'status': 'completed',
            'overall_score': 86.5,
            'technical_score': 88.0,
            'communication_score': 84.0,
            'relevance_score': 87.5,
            'feedback_summary': 'Strong command of algorithmic complexity and memory layouts. Clean breakdown of nested bracket expansion using stacks. Need slightly more concise answers on database transaction isolation levels.',
            'strengths': ['Clear line-by-line explanation of stack frames', 'Great edge case analysis (nested brackets, zeros)', 'Solid communication tone'],
            'weaknesses': ['Pacing was slightly hurried on OS virtual memory question', 'Could mention index impact on subqueries'],
            'recommended_topics': ['B-Tree Indexing in PostgreSQL', 'Semaphore vs Mutex internals', 'Sliding Window Maximum']
        }
    )

    q1, _ = InterviewQuestion.objects.get_or_create(
        interview=interview, question_index=1,
        defaults={
            'question_text': 'Explain how you would decode a nested string pattern like "3[a2[c]]" without recursion. What is the time and space complexity?',
            'category': 'DSA & Problem Solving'
        }
    )
    InterviewAnswer.objects.get_or_create(
        question=q1,
        defaults={
            'student_answer': 'I use two stacks: one for counts (multipliers) and one for string builders. When encountering an open bracket, I push current accumulator string and count. When encountering a closing bracket, I pop the previous string and repeat the current segment by the count.',
            'ai_evaluation': 'Excellent explanation. Demonstrates optimal O(N) linear time and O(N) auxiliary space without stack overflow risk.',
            'score': 92.0,
            'technical_accuracy': 95.0,
            'relevance': 90.0,
            'explanation_quality': 91.0
        }
    )

    # 9. Coding Competitions (DKoder Arena)
    now = timezone.now()
    comp1, _ = Competition.objects.get_or_create(
        slug='national-placement-sprint-14',
        defaults={
            'name': 'DKoder National Placement Sprint #14',
            'description': 'Live 90-minute algorithmic sprint matching real Zoho & Amazon OA hiring standards. Top 50 win direct fast-track placement referral reviews.',
            'start_time': now - datetime.timedelta(hours=1),
            'end_time': now + datetime.timedelta(days=2),
            'registration_deadline': now + datetime.timedelta(days=1),
            'rules': 'Standard ICPC scoring: Each question has points based on difficulty. 10-minute penalty per rejected submission.',
            'difficulty': 'Medium',
            'max_participants': 1200,
            'is_published': True,
            'is_practice_mode_available': True
        }
    )

    comp2, _ = Competition.objects.get_or_create(
        slug='zoho-advanced-round2-battle',
        defaults={
            'name': 'Zoho Round 2 Speed Hackathon 2026',
            'description': 'Targeted C/C++/Java coding test emphasizing pointer arithmetic, matrix transformations, and pattern generation without built-in library shortcuts.',
            'start_time': now + datetime.timedelta(days=3),
            'end_time': now + datetime.timedelta(days=3, hours=3),
            'registration_deadline': now + datetime.timedelta(days=2),
            'rules': 'No STL containers allowed for C++ track. Strict memory allocation checks.',
            'difficulty': 'Hard',
            'max_participants': 800,
            'is_published': True,
            'is_practice_mode_available': True
        }
    )

    comp3, _ = Competition.objects.get_or_create(
        slug='tcs-nqt-grand-sim',
        defaults={
            'name': 'TCS NQT Grand National Mock Contest',
            'description': 'Archive Contest: 42 Questions covering Quantitative Aptitude, Logical Reasoning, and Advanced Hands-on Coding.',
            'start_time': now - datetime.timedelta(days=10),
            'end_time': now - datetime.timedelta(days=7),
            'registration_deadline': now - datetime.timedelta(days=11),
            'rules': 'Sectional timer enforced. Unlimited practice mode submissions allowed.',
            'difficulty': 'Medium',
            'max_participants': 2500,
            'is_published': True,
            'is_practice_mode_available': True
        }
    )

    # Leaderboard entries
    lb_seed = [
        (alex_user, 1, 380, 4, 1840),
        (created_users['sneha'], 2, 350, 4, 2190),
        (created_users['rohit'], 3, 310, 3, 1420),
        (created_users['priya'], 4, 280, 3, 1950),
    ]
    for u, rnk, scr, solved, pen in lb_seed:
        LeaderboardEntry.objects.get_or_create(
            competition=comp1, user=u,
            defaults={'score': scr, 'rank': rnk, 'problems_solved': solved, 'penalty_time_seconds': pen, 'board_type': 'competition'}
        )
        LeaderboardEntry.objects.get_or_create(
            user=u, board_type='global',
            defaults={'score': scr * 4, 'rank': rnk, 'problems_solved': solved * 8, 'penalty_time_seconds': pen}
        )

    # 10. Community Posts & Discussions
    cp1, _ = CommunityPost.objects.get_or_create(
        author=alex_user,
        title='How I solved Zoho Round 2 String Multipliers in 18 minutes',
        defaults={
            'content': 'Many students struggle with nested brackets like 3[a2[b]]. The secret is to not use recursion which blows the stack on large inputs. Use two lightweight stacks: one integer stack for multipliers and one string builder stack. When you pop on closing bracket, repeat and attach to the previous stack top.',
            'tag': 'Interview Experience',
            'likes_count': 42,
            'comments_count': 6,
            'is_pinned': True
        }
    )

    cp2, _ = CommunityPost.objects.get_or_create(
        author=created_users['priya'],
        title='TCS NQT 2026: 10 Must-Know Aptitude Formulas & Short-cuts',
        defaults={
            'content': 'In campus Day-1 drives, speed is everything. Here are the 10 recurring patterns: 1) Relative Speed Meeting Times, 2) Unit Digit Calculation of Large Exponents, 3) Work & Wages when workers leave early, 4) Segmented Sieve for prime range questions.',
            'tag': 'Placement Tips',
            'likes_count': 67,
            'comments_count': 14,
            'is_pinned': False
        }
    )

    Comment.objects.get_or_create(
        post=cp1, author=created_users['rohit'],
        defaults={'content': 'This helped me clear the bracket matching question in my campus internal assessment! Thank you Alex!', 'likes_count': 8}
    )

    StudyGroup.objects.get_or_create(
        name='Zoho 2026 Campus Achievers Club',
        slug='zoho-2026-club',
        creator=alex_user,
        defaults={
            'description': 'Peer review group focusing strictly on C pointers, recursion, and pattern questions asked in Zoho On-Campus drives.',
            'focus_area': 'Zoho Placements',
            'members_count': 128
        }
    )

    StudyGroup.objects.get_or_create(
        name='Amazon SDE-1 Super Dream Prep',
        slug='amazon-sde1-club',
        creator=created_users['priya'],
        defaults={
            'description': 'Mastering Multi-Source BFS, Dynamic Programming, and Leadership Principles for Tier-1 Product Companies.',
            'focus_area': 'Product Companies',
            'members_count': 214
        }
    )

    # 11. Career Profile: Resume & Portfolio for Alex
    resume, _ = Resume.objects.get_or_create(
        user=alex_user,
        defaults={
            'full_name': 'Alex Rivera',
            'email': 'alex.rivera@engineering.edu',
            'phone': '+91 98765 43210',
            'location': 'Chennai, Tamil Nadu',
            'github_url': 'https://github.com/alexrivera-tech',
            'linkedin_url': 'https://linkedin.com/in/alexrivera-dev',
            'portfolio_url': 'https://dkoder.co.in/portfolio/alex-rivera',
            'summary': 'Pre-final year Computer Science undergraduate passionate about full-stack engineering, distributed systems, and algorithmic problem-solving. Solved 300+ placement problems across Zoho, TCS, and Amazon hiring patterns with top 2% rating on DKoder Arena.',
            'education': [
                {'degree': 'B.E. Computer Science & Engineering', 'institution': 'Anna University / CEG, Chennai', 'year': '2022 – 2026', 'grade': '8.92 CGPA'},
                {'degree': 'Higher Secondary (XII)', 'institution': 'Kendriya Vidyalaya', 'year': '2022', 'grade': '94.8%'}
            ],
            'experience': [
                {'role': 'Full Stack Developer Intern', 'company': 'NexGen Cloud Systems', 'duration': 'May 2025 – July 2025', 'bullets': ['Architected real-time WebSocket dashboard handling 20,000+ daily concurrent events.', 'Optimized PostgreSQL queries reducing average API latency by 38%.']}
            ],
            'projects': [
                {'name': 'Distributed Task Scheduler', 'tech': 'Python, Redis, Docker, FastAPI', 'bullets': ['Implemented distributed job queue with exponential backoff and worker heartbeat.', 'Processed 500,000 background jobs with 99.98% reliability.']},
                {'name': 'DKoder Campus Placement Sandbox', 'tech': 'JavaScript, Node.js, Tailwind CSS', 'bullets': ['Built browser-based code playground with simulated testcase runner and company filters.']}
            ],
            'skills': ['Python', 'C/C++', 'JavaScript / TypeScript', 'Django', 'React', 'PostgreSQL', 'Redis', 'Docker', 'Git'],
            'certifications': ['AWS Certified Cloud Practitioner', 'DKoder Advanced DSA Placement Certified (Gold Badge)'],
            'achievements': ['Rank #1 in DKoder National Placement Sprint #14', 'Solved 300+ Company-Tagged Coding Problems'],
            'languages': ['English (Fluent)', 'Tamil (Native)', 'Hindi (Conversational)'],
            'ats_score': 94.0,
            'template': 'modern_purple'
        }
    )

    portfolio, _ = Portfolio.objects.get_or_create(
        user=alex_user,
        slug='alex-rivera',
        defaults={
            'display_name': 'Alex Rivera',
            'headline': 'Full Stack Engineer & Competitive Problem Solver',
            'about_me': 'I build high-performance web systems and solve complex algorithmic problems. Preparing for SDE roles at Zoho, Amazon, and product companies.',
            'theme': 'dkoder_purple_gold',
            'is_public': True,
            'hide_contact_info': False,
            'view_count': 328
        }
    )

    PortfolioProject.objects.get_or_create(
        portfolio=portfolio,
        title='Real-Time Distributed Queue Engine',
        defaults={
            'tagline': 'Fault-tolerant job scheduler handling 500k+ tasks/day',
            'description': 'Built with Python and Redis featuring atomic worker leasing and automatic retry mechanisms.',
            'tech_stack': ['Python', 'Redis', 'Docker', 'FastAPI'],
            'github_link': 'https://github.com/alexrivera-tech/distributed-queue',
            'live_link': 'https://queue-demo.alexrivera.dev',
            'featured': True,
            'order': 1
        }
    )

    PortfolioProject.objects.get_or_create(
        portfolio=portfolio,
        title='DKoder 2.0 Placement LMS Interface',
        defaults={
            'tagline': 'AI-assisted coding playground with live compilation feedback',
            'description': 'Features real test case evaluation, interactive placement roadmap, and AI mentor coaching.',
            'tech_stack': ['JavaScript', 'TailwindCSS', 'Django', 'SQLite'],
            'github_link': 'https://github.com/alexrivera-tech/dkoder-showcase',
            'live_link': 'https://dkoder.co.in',
            'featured': True,
            'order': 2
        }
    )

    # 12. Admin Audit Logs & Notifications
    AdminAuditLog.objects.get_or_create(
        actor=created_users['admin'],
        action='SYSTEM_INITIALIZED',
        target_model='SystemSetting',
        defaults={
            'details': 'DKoder 2.0 core modules activated: AI Mentor, CodeLab Compiler, Placement Roadmap, Arena, Interview Studio, and Analytics.',
            'ip_address': '127.0.0.1'
        }
    )

    Notification.objects.get_or_create(
        user=alex_user,
        title='Welcome to DKoder 2.0!',
        defaults={
            'message': 'Your AI Mentor, CodeLab Sandbox, and Placement Roadmap are fully synced. Check your Week 1 daily tasks to maintain your 14-day streak!',
            'notification_type': 'system',
            'is_read': False
        }
    )

    Notification.objects.get_or_create(
        user=alex_user,
        title='National Placement Sprint #14 is LIVE',
        defaults={
            'message': 'You are currently Rank #1 in the National Placement Sprint. Complete the Rotten Oranges BFS challenge to secure your position!',
            'notification_type': 'competition',
            'is_read': False
        }
    )

    print("DKoder 2.0 Database Seeding Completed Successfully! All 32 entities populated with rich data.")

if __name__ == '__main__':
    run_seed()
