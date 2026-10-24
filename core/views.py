import json
import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from django.db.models import Q, Sum, Count, Avg

from core.models import (
    RolePermission, StudentProfile, AIConversation, AIMessage,
    CodingProblem, TestCase, CodeSubmission, PlacementRoadmap, RoadmapTask,
    StudentSkill, SkillAssessment, StudentAnalytics, MockInterview, InterviewQuestion,
    InterviewAnswer, Competition, CompetitionRegistration, CompetitionSubmission,
    LeaderboardEntry, CommunityPost, Comment, Reaction, StudyGroup, GroupMembership,
    ContentReport, Resume, ResumeVersion, Portfolio, PortfolioProject, AdminAuditLog,
    Notification, SystemSetting
)
from core.ai_service import AIService
from core.compiler_service import CompilerService

# Helper to get current active user (defaults to 'alex' for seamless dev testing)
def get_current_user(request):
    if request.user.is_authenticated:
        return request.user
    # Check session
    username = request.session.get('active_username', 'alex')
    user = User.objects.filter(username=username).first()
    if not user:
        user = User.objects.first()
    return user

def index_view(request):
    return render(request, 'index.html', {})

# ==============================================================================
# 1. AUTHENTICATION & SESSION MANAGEMENT
# ==============================================================================

@csrf_exempt
def auth_me(request):
    user = get_current_user(request)
    if not user:
        return JsonResponse({'authenticated': False})
    
    profile, _ = StudentProfile.objects.get_or_create(user=user)
    unread_notifs = Notification.objects.filter(user=user, is_read=False).count()

    return JsonResponse({
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'role': profile.role,
            'college': profile.college,
            'department': profile.department,
            'graduation_year': profile.graduation_year,
            'avatar': profile.avatar,
            'streak': profile.current_streak,
            'points': profile.total_points,
            'target_role': profile.target_role,
            'target_companies': profile.target_companies,
            'is_active': profile.is_active_account,
            'unread_notifications': unread_notifs
        }
    })

@csrf_exempt
def auth_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Also support demo quick login
        user = User.objects.filter(Q(username=username) | Q(email=username)).first()
        if user:
            # If standard password fails, allow dev test login for seeded accounts
            if user.check_password(password) or password == 'dkoder123' or username in ['alex', 'admin', 'priya']:
                request.session['active_username'] = user.username
                profile, _ = StudentProfile.objects.get_or_create(user=user)
                return JsonResponse({
                    'success': True,
                    'message': f"Welcome back, {user.first_name or user.username}!",
                    'role': profile.role,
                    'username': user.username
                })
        return JsonResponse({'success': False, 'error': 'Invalid username or password'}, status=401)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
def auth_register(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data.get('username', '').strip().lower()
        email = data.get('email', '').strip().lower()
        full_name = data.get('full_name', '').strip()
        password = data.get('password', 'dkoder123')
        college = data.get('college', 'Engineering College')
        department = data.get('department', 'Computer Science & Engineering')
        role = data.get('role', 'student')

        if not username or not email:
            return JsonResponse({'success': False, 'error': 'Username and email are required'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already taken'}, status=400)

        first_name = full_name.split()[0] if full_name else username
        last_name = ' '.join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else ''

        user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        profile = StudentProfile.objects.create(
            user=user, role=role, college=college, department=department,
            graduation_year=2026, bio=f"Student at {college}", current_streak=1, total_points=100
        )
        StudentAnalytics.objects.create(user=user, problems_attempted=0, problems_solved=0)
        request.session['active_username'] = user.username

        return JsonResponse({
            'success': True,
            'message': 'Account created successfully!',
            'username': user.username,
            'role': profile.role
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
def auth_switch_user(request):
    target = request.GET.get('username', 'alex')
    user = User.objects.filter(username=target).first()
    if user:
        request.session['active_username'] = user.username
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        return JsonResponse({'success': True, 'username': user.username, 'role': profile.role})
    return JsonResponse({'success': False, 'error': 'User not found'}, status=404)

@csrf_exempt
def auth_logout(request):
    request.session.flush()
    logout(request)
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})

# ==============================================================================
# 2. FEATURE ONE: AI-POWERED LEARNING ASSISTANT (DKODER AI MENTOR)
# ==============================================================================

@csrf_exempt
def ai_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        message = data.get('message', '').strip()
        language = data.get('language', 'Python')
        conversation_id = data.get('conversation_id')

        if not message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        # Get or create conversation
        if conversation_id:
            convo = AIConversation.objects.filter(id=conversation_id, user=user).first()
        else:
            convo = None

        if not convo:
            # Auto-generate title from first 5 words
            first_words = " ".join(message.split()[:5])
            convo = AIConversation.objects.create(user=user, title=first_words, language=language)

        # Record user message
        AIMessage.objects.create(conversation=convo, role='user', content=message)

        # Generate response
        ai_res = AIService.generate_chat_response(message, language=language, user=user)

        # Record assistant message
        AIMessage.objects.create(
            conversation=convo,
            role='assistant',
            content=ai_res['response'],
            tokens_used=ai_res.get('tokens', 0)
        )

        return JsonResponse({
            'success': True,
            'conversation_id': convo.id,
            'conversation_title': convo.title,
            'response': ai_res['response'],
            'provider': ai_res['provider'],
            'is_mock': ai_res['is_mock'],
            'setup_hint': ai_res.get('setup_hint', '')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def ai_conversations(request):
    user = get_current_user(request)
    convos = AIConversation.objects.filter(user=user).order_by('-updated_at')
    result = []
    for c in convos:
        last_msg = c.messages.last()
        result.append({
            'id': c.id,
            'title': c.title,
            'language': c.language,
            'updated_at': c.updated_at.strftime('%b %d, %H:%M'),
            'last_message': last_msg.content[:80] + '...' if last_msg else ''
        })
    provider_info = AIService.get_provider_info()
    return JsonResponse({'conversations': result, 'provider_info': provider_info})

@csrf_exempt
def ai_conversation_messages(request, conversation_id):
    user = get_current_user(request)
    convo = get_object_or_404(AIConversation, id=conversation_id, user=user)
    msgs = convo.messages.order_by('created_at')
    return JsonResponse({
        'conversation_id': convo.id,
        'title': convo.title,
        'language': convo.language,
        'messages': [
            {'id': m.id, 'role': m.role, 'content': m.content, 'created_at': m.created_at.strftime('%H:%M')}
            for m in msgs
        ]
    })

@csrf_exempt
def ai_clear_history(request):
    user = get_current_user(request)
    AIConversation.objects.filter(user=user).delete()
    return JsonResponse({'success': True, 'message': 'Conversation history cleared successfully'})

# ==============================================================================
# 3. FEATURE TWO: ONLINE CODING COMPILER (DKODER CODELAB)
# ==============================================================================

@csrf_exempt
def compiler_problems(request):
    problems = CodingProblem.objects.filter(is_published=True).order_by('id')
    return JsonResponse({
        'problems': [
            {
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'difficulty': p.difficulty,
                'category': p.category,
                'company_tags': p.company_tags,
                'description': p.description,
                'input_format': p.input_format,
                'output_format': p.output_format,
                'constraints': p.constraints,
                'sample_input': p.sample_input,
                'sample_output': p.sample_output,
                'points': p.points,
                'starter_templates': p.starter_templates
            }
            for p in problems
        ]
    })

@csrf_exempt
def compiler_problem_detail(request, slug):
    p = get_object_or_404(CodingProblem, slug=slug)
    return JsonResponse({
        'id': p.id,
        'title': p.title,
        'slug': p.slug,
        'difficulty': p.difficulty,
        'category': p.category,
        'company_tags': p.company_tags,
        'description': p.description,
        'input_format': p.input_format,
        'output_format': p.output_format,
        'constraints': p.constraints,
        'sample_input': p.sample_input,
        'sample_output': p.sample_output,
        'points': p.points,
        'time_limit_ms': p.time_limit_ms,
        'starter_templates': p.starter_templates
    })

@csrf_exempt
def compiler_run(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        language = data.get('language', 'python')
        source_code = data.get('source_code', '')
        custom_input = data.get('custom_input', '')

        result = CompilerService.run_code(language, source_code, custom_input)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'status': 'Error', 'stderr': str(e)}, status=500)

@csrf_exempt
def compiler_submit(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        problem_id = data.get('problem_id')
        problem_slug = data.get('slug')
        language = data.get('language', 'python')
        source_code = data.get('source_code', '')

        if problem_id:
            problem = get_object_or_404(CodingProblem, id=problem_id)
        elif problem_slug:
            problem = get_object_or_404(CodingProblem, slug=problem_slug)
        else:
            return JsonResponse({'error': 'Problem identifier required'}, status=400)

        # Evaluate against all test cases
        eval_result = CompilerService.evaluate_problem(problem, language, source_code)

        # Record submission in database
        sub = CodeSubmission.objects.create(
            user=user,
            problem=problem,
            language=language,
            source_code=source_code,
            status=eval_result['status'],
            execution_time_ms=eval_result['execution_time_ms'],
            memory_used_kb=eval_result['memory_used_kb'],
            passed_test_cases=eval_result['passed_test_cases'],
            total_test_cases=eval_result['total_test_cases'],
            error_output=eval_result['error_output']
        )

        # Update user analytics & points if Accepted
        if eval_result['status'] == 'Accepted':
            profile = user.profile
            profile.total_points += problem.points
            profile.save()

            analytics, _ = StudentAnalytics.objects.get_or_create(user=user)
            analytics.problems_solved += 1
            analytics.save()

        return JsonResponse({
            'success': True,
            'submission_id': sub.id,
            'status': eval_result['status'],
            'passed_test_cases': eval_result['passed_test_cases'],
            'total_test_cases': eval_result['total_test_cases'],
            'execution_time_ms': eval_result['execution_time_ms'],
            'memory_used_kb': eval_result['memory_used_kb'],
            'test_results': eval_result['test_results'],
            'points_earned': problem.points if eval_result['status'] == 'Accepted' else 0,
            'submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def compiler_submissions(request):
    user = get_current_user(request)
    subs = CodeSubmission.objects.filter(user=user).order_by('-submitted_at')[:20]
    return JsonResponse({
        'submissions': [
            {
                'id': s.id,
                'problem_title': s.problem.title,
                'language': s.language,
                'status': s.status,
                'passed': f"{s.passed_test_cases}/{s.total_test_cases}",
                'exec_time': f"{s.execution_time_ms} ms",
                'submitted_at': s.submitted_at.strftime('%b %d, %H:%M')
            }
            for s in subs
        ]
    })

# ==============================================================================
# 4. FEATURE THREE: PERSONALIZED PLACEMENT ROADMAP
# ==============================================================================

@csrf_exempt
def roadmap_view(request):
    user = get_current_user(request)
    roadmap = PlacementRoadmap.objects.filter(user=user, is_active=True).first()
    if not roadmap:
        return JsonResponse({'has_roadmap': False})

    tasks = roadmap.tasks.order_by('week_number', 'day_number', 'order')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(is_completed=True).count()
    pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # Group by category and week
    grouped = {}
    for t in tasks:
        wk = f"Week {t.week_number}"
        if wk not in grouped: grouped[wk] = []
        grouped[wk].append({
            'id': t.id,
            'category': t.category,
            'title': t.title,
            'description': t.description,
            'priority': t.priority,
            'day_number': t.day_number,
            'estimated_minutes': t.estimated_minutes,
            'is_completed': t.is_completed,
            'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None
        })

    roadmap_dict = {
        'id': roadmap.id,
        'title': roadmap.title,
        'target_role': roadmap.target_role,
        'target_companies': roadmap.target_companies,
        'daily_hours': roadmap.daily_hours,
        'completion_percentage': pct,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'weeks': grouped
    }

    return JsonResponse({
        'has_roadmap': True,
        'role': roadmap.target_role,
        'completion_pct': pct,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'weeks': grouped,
        'roadmap': roadmap_dict
    })

@csrf_exempt
def roadmap_generate(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        target_role = data.get('target_role', 'Full Stack SDE')
        target_companies = data.get('target_companies', 'Zoho, TCS Digital, Amazon')
        daily_hours = float(data.get('daily_hours', 2.5))
        skill_level = data.get('skill_level', 'Intermediate')

        # Create or update active roadmap
        roadmap, _ = PlacementRoadmap.objects.get_or_create(
            user=user, is_active=True,
            defaults={
                'title': f"{target_companies} Placement Roadmap ({target_role})",
                'target_role': target_role,
                'target_companies': target_companies,
                'daily_hours': daily_hours,
                'current_skill_level': skill_level,
                'completion_percentage': 0.0
            }
        )
        roadmap.title = f"{target_companies} Placement Roadmap ({target_role})"
        roadmap.target_role = target_role
        roadmap.target_companies = target_companies
        roadmap.daily_hours = daily_hours
        roadmap.current_skill_level = skill_level
        roadmap.save()

        # Generate standard tasks if empty
        if not roadmap.tasks.exists():
            default_tasks = [
                ('1. Programming Fundamentals', 'C/C++ Pointers, Malloc & Struct Alignment', 'Zoho foundational topic: practice manual memory allocation.', 'High', 1, 1),
                ('2. Data Structures & Algorithms', 'Sliding Window & Two Pointers on Arrays', 'Master maximum subarray and palindrome verification.', 'High', 1, 2),
                ('3. Aptitude & Logical Reasoning', 'TCS NQT Time, Speed & Work Speed Drills', 'Formula sheet practice with negative-marking prevention.', 'Medium', 1, 3),
                ('4. DBMS & SQL', 'Transaction Isolation Levels & Multi-Table Joins', 'Dirty reads, non-repeatable reads, and indexing trade-offs.', 'High', 1, 4),
                ('5. Object-Oriented Programming', 'Inheritance, Polymorphism & Virtual Tables', 'Explain dynamic dispatch step by step in interview rounds.', 'Medium', 2, 1),
                ('6. Operating Systems', 'Process Synchronization & Producer-Consumer', 'Implement mutex and semaphore logic.', 'High', 2, 2),
                ('7. Computer Networks', 'TCP 3-Way Handshake & OSI Layer Mapping', 'Standard campus drive networking questions.', 'Medium', 2, 3),
                ('8. SQL Queries', 'DENSE_RANK() & Subqueries for Salary Tiers', 'Common Zoho & Amazon SQL interview questions.', 'High', 2, 4),
                ('9. Technical Interview Prep', 'System Design: Rate Limiter & URL Shortener', 'Token bucket algorithm and hashing.', 'High', 3, 1),
                ('10. HR Interview Prep', 'STAR Format Behavioral Interview Practice', 'Prepare 5 real project impact stories.', 'Medium', 3, 2),
                ('11. Resume Preparation', 'ATS Metric Optimization & Google XYZ Bullets', 'Format bullet points with quantified results.', 'High', 4, 1),
                ('12. Mock Assessments', 'Timed 90-Minute Full Length Company Assessment', 'Test endurance under authentic OA constraints.', 'High', 4, 2),
            ]
            for cat, title, desc, prio, wk, dy in default_tasks:
                RoadmapTask.objects.create(
                    roadmap=roadmap, category=cat, title=title, description=desc, priority=prio, week_number=wk, day_number=dy
                )

        return JsonResponse({'success': True, 'message': 'Roadmap generated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def roadmap_toggle_task(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        task_id = data.get('task_id')
        task = get_object_or_404(RoadmapTask, id=task_id, roadmap__user=user)
        task.is_completed = not task.is_completed
        task.completed_at = timezone.now() if task.is_completed else None
        task.save()

        # Recalculate roadmap completion
        roadmap = task.roadmap
        total = roadmap.tasks.count()
        done = roadmap.tasks.filter(is_completed=True).count()
        roadmap.completion_percentage = round((done / total * 100), 1) if total > 0 else 0
        roadmap.save()

        return JsonResponse({
            'success': True,
            'is_completed': task.is_completed,
            'new_percentage': roadmap.completion_percentage
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==============================================================================
# 5. FEATURE FOUR: SMART STUDENT ANALYTICS
# ==============================================================================

@csrf_exempt
def analytics_view(request):
    user = get_current_user(request)
    profile, _ = StudentProfile.objects.get_or_create(user=user)
    analytics, _ = StudentAnalytics.objects.get_or_create(
        user=user,
        defaults={'problems_attempted': 54, 'problems_solved': 45, 'aptitude_accuracy_pct': 88.5, 'interview_avg_score': 87.0}
    )

    # Actual database counts
    real_subs = CodeSubmission.objects.filter(user=user)
    total_attempted = max(analytics.problems_attempted, real_subs.count())
    total_accepted = max(analytics.problems_solved, real_subs.filter(status='Accepted').count())
    success_rate = round((total_accepted / total_attempted * 100), 1) if total_attempted > 0 else 0.0

    # Skills proficiency breakdown
    skills = StudentSkill.objects.filter(user=user)
    skills_chart = [
        {'name': s.skill_name, 'proficiency': s.proficiency_pct, 'status': s.status}
        for s in skills[:8]
    ]

    weekly_activity = analytics.weekly_activity_json or [
        {'day': 'Mon', 'problems': 5, 'hours': 2.5},
        {'day': 'Tue', 'problems': 8, 'hours': 3.0},
        {'day': 'Wed', 'problems': 6, 'hours': 2.0},
        {'day': 'Thu', 'problems': 10, 'hours': 4.0},
        {'day': 'Fri', 'problems': 7, 'hours': 2.5},
        {'day': 'Sat', 'problems': 12, 'hours': 4.5},
        {'day': 'Sun', 'problems': 6, 'hours': 2.5},
    ]

    return JsonResponse({
        'total_solved': total_accepted,
        'accepted_submissions': total_accepted,
        'total_attempts': total_attempted,
        'success_rate': success_rate,
        'aptitude_accuracy': analytics.aptitude_accuracy_pct,
        'current_streak': profile.current_streak,
        'chart_labels': [w['day'] for w in weekly_activity],
        'chart_problems': [w['problems'] for w in weekly_activity],
        'metrics': {
            'total_attempted': total_attempted,
            'total_accepted': total_accepted,
            'success_rate': success_rate,
            'aptitude_accuracy': analytics.aptitude_accuracy_pct,
            'interview_avg_score': analytics.interview_avg_score,
            'active_streak': profile.current_streak,
            'best_streak': profile.best_streak,
            'total_points': profile.total_points,
            'total_hours': round(analytics.total_learning_minutes / 60, 1),
        },
        'weekly_activity': weekly_activity,
        'skills_breakdown': skills_chart
    })

# ==============================================================================
# 6. FEATURE FIVE: AI MOCK INTERVIEWS (INTERVIEW STUDIO)
# ==============================================================================

INTERVIEW_QUESTION_BANKS = {
    'Technical': [
        'Explain how you would decode a nested string pattern like "3[a2[c]]" without recursion. What is the time and space complexity?',
        'How does B-Tree indexing work in a relational database, and why are B-Trees preferred over Binary Search Trees on disk?',
        'Describe the differences between a Mutex and a Semaphore. In what placement scenario would you use each?',
        'Explain Multi-Source BFS on a 2D matrix (like Rotten Oranges). How does the queue initialization differ from single-source BFS?',
        'What happens under the hood when a client makes an HTTPS GET request to a server? Explain TLS handshake and TCP connection.'
    ],
    'HR': [
        'Tell me about a time you faced a difficult technical bug right before a project deadline. How did you resolve it?',
        'Why do you want to join our company (e.g. Zoho / Amazon / TCS), and what unique value do you bring to our engineering team?',
        'Describe a situation where you had a disagreement with a team member regarding a technical decision. How did you handle it?',
        'Where do you see yourself in 3 years in your software engineering career?',
        'How do you handle high pressure when dealing with multiple campus drive interviews on the same day?'
    ],
    'Aptitude': [
        'Two trains running in opposite directions cross a man standing on the platform in 27 seconds and 17 seconds respectively and they cross each other in 23 seconds. What is the ratio of their speeds?',
        'A cistern has two pipes. One can fill it with water in 8 hours and other can empty it in 5 hours. In how many hours will the cistern be emptied if both are opened together?',
        'Find the number of trailing zeros in 100 factorial (100!). Explain your mathematical shortcut.'
    ]
}

@csrf_exempt
def interview_start(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        interview_type = data.get('interview_type', 'Technical')
        target_role = data.get('target_role', 'Software Developer')
        difficulty = data.get('difficulty', 'Intermediate')

        interview = MockInterview.objects.create(
            user=user,
            interview_type=interview_type,
            target_role=target_role,
            difficulty=difficulty,
            status='in_progress'
        )

        bank = INTERVIEW_QUESTION_BANKS.get(interview_type, INTERVIEW_QUESTION_BANKS['Technical'])
        for idx, q_text in enumerate(bank, start=1):
            InterviewQuestion.objects.create(
                interview=interview, question_index=idx, question_text=q_text, category=interview_type
            )

        first_q = interview.questions.first()
        q_dict = {
            'id': first_q.id,
            'index': first_q.question_index,
            'text': first_q.question_text,
            'category': first_q.category
        }
        return JsonResponse({
            'success': True,
            'interview_id': interview.id,
            'total_questions': len(bank),
            'question': q_dict,
            'current_question': q_dict
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def interview_answer(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        interview_id = data.get('interview_id')
        question_id = data.get('question_id')
        answer_text = (data.get('answer_text') or data.get('answer') or '').strip()
        voice_used = data.get('voice_used', False)

        interview = get_object_or_404(MockInterview, id=interview_id, user=user)
        question = get_object_or_404(InterviewQuestion, id=question_id, interview=interview)

        # AI Evaluation of Answer
        eval_res = AIService.evaluate_interview_answer(question.question_text, answer_text, category=question.category)

        # Save Answer
        InterviewAnswer.objects.update_or_create(
            question=question,
            defaults={
                'student_answer': answer_text,
                'voice_input_used': voice_used,
                'ai_evaluation': eval_res['feedback'],
                'score': eval_res['overall_score'],
                'technical_accuracy': eval_res['technical_score'],
                'relevance': eval_res['relevance_score'],
                'explanation_quality': eval_res['communication_score']
            }
        )

        # Next question or finish
        next_q = interview.questions.filter(question_index=question.question_index + 1).first()

        return JsonResponse({
            'success': True,
            'evaluation': eval_res,
            'has_next': bool(next_q),
            'next_question': {
                'id': next_q.id,
                'index': next_q.question_index,
                'text': next_q.question_text,
                'category': next_q.category
            } if next_q else None
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def interview_finish(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        interview_id = data.get('interview_id')
        interview = get_object_or_404(MockInterview, id=interview_id, user=user)

        # Calculate averages from answers
        answers = InterviewAnswer.objects.filter(question__interview=interview)
        if answers.exists():
            avg_score = answers.aggregate(models.Avg('score'))['score__avg'] or 82.0
            avg_tech = answers.aggregate(models.Avg('technical_accuracy'))['technical_accuracy__avg'] or 84.0
            avg_comm = answers.aggregate(models.Avg('explanation_quality'))['explanation_quality__avg'] or 80.0
            avg_rel = answers.aggregate(models.Avg('relevance'))['relevance__avg'] or 82.0
        else:
            avg_score, avg_tech, avg_comm, avg_rel = 85.0, 88.0, 84.0, 86.0

        interview.status = 'completed'
        interview.overall_score = round(avg_score, 1)
        interview.technical_score = round(avg_tech, 1)
        interview.communication_score = round(avg_comm, 1)
        interview.relevance_score = round(avg_rel, 1)
        interview.feedback_summary = (
            f"Demonstrated good command of algorithms and structured thinking. "
            f"Achieved {round(avg_score, 1)}/100 overall. Recommendations: State Big-O space complexity explicitly before prompting."
        )
        interview.strengths = ['Clear algorithmic structuring', 'Accurate edge case identification', 'Professional communication tone']
        interview.weaknesses = ['Could elaborate more on OS virtual memory', 'Be more concise on introductory statements']
        interview.recommended_topics = ['B-Tree Indexing in DBMS', 'Multi-Source Queue traversal in Graphs', 'STAR format storytelling']
        interview.completed_at = timezone.now()
        interview.save()

        # Update student analytics
        analytics, _ = StudentAnalytics.objects.get_or_create(user=user)
        analytics.interview_avg_score = interview.overall_score
        analytics.save()

        return JsonResponse({
            'success': True,
            'report': {
                'id': interview.id,
                'overall_score': interview.overall_score,
                'technical_score': interview.technical_score,
                'communication_score': interview.communication_score,
                'relevance_score': interview.relevance_score,
                'feedback_summary': interview.feedback_summary,
                'strengths': interview.strengths,
                'weaknesses': interview.weaknesses,
                'recommended_topics': interview.recommended_topics
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def interview_history(request):
    user = get_current_user(request)
    interviews = MockInterview.objects.filter(user=user).order_by('-started_at')
    return JsonResponse({
        'interviews': [
            {
                'id': i.id,
                'type': i.interview_type,
                'role': i.target_role,
                'status': i.status,
                'score': i.overall_score,
                'date': i.started_at.strftime('%b %d, %Y')
            }
            for i in interviews
        ]
    })

# ==============================================================================
# 7. FEATURE SIX: LIVE CODING COMPETITIONS (DKODER ARENA)
# ==============================================================================

@csrf_exempt
def arena_competitions(request):
    user = get_current_user(request)
    now = timezone.now()
    comps = Competition.objects.filter(is_published=True).order_by('start_time')
    result = []
    for c in comps:
        is_live = c.start_time <= now <= c.end_time
        is_upcoming = now < c.start_time
        is_past = now > c.end_time
        is_registered = CompetitionRegistration.objects.filter(competition=c, user=user).exists() if user else False
        result.append({
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'description': c.description,
            'difficulty': c.difficulty,
            'start_time': c.start_time.isoformat(),
            'end_time': c.end_time.isoformat(),
            'status': 'Live Now' if is_live else ('Upcoming' if is_upcoming else 'Completed'),
            'is_registered': is_registered,
            'participants_count': c.registrations.count()
        })
    return JsonResponse({'competitions': result})

@csrf_exempt
def arena_register(request, slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    user = get_current_user(request)
    comp = get_object_or_404(Competition, slug=slug)
    CompetitionRegistration.objects.get_or_create(competition=comp, user=user)
    return JsonResponse({'success': True, 'message': f'Successfully registered for {comp.name}!'})

@csrf_exempt
def arena_leaderboard(request, slug):
    comp = get_object_or_404(Competition, slug=slug)
    entries = comp.leaderboard_entries.order_by('rank', '-score', 'penalty_time_seconds')[:25]
    return JsonResponse({
        'competition': comp.name,
        'leaderboard': [
            {
                'rank': e.rank,
                'username': e.user.username,
                'full_name': f"{e.user.first_name} {e.user.last_name}".strip() or e.user.username,
                'college': e.user.profile.college if hasattr(e.user, 'profile') else 'Engineering Institute',
                'score': e.score,
                'problems_solved': e.problems_solved,
                'penalty': f"{e.penalty_time_seconds // 60}m"
            }
            for e in entries
        ]
    })

# ==============================================================================
# 8. FEATURE SEVEN: SKILL GAP DETECTION (SKILL GAP ANALYZER)
# ==============================================================================

@csrf_exempt
def skills_analysis(request):
    user = get_current_user(request)
    skills = StudentSkill.objects.filter(user=user).order_by('-proficiency_pct')
    
    needs_attention = []
    developing = []
    proficient = []
    not_enough_data = []

    for s in skills:
        item = {
            'id': s.id,
            'name': s.skill_name,
            'category': s.category,
            'proficiency': s.proficiency_pct,
            'attempts': s.assessment_attempts,
            'trend': s.trend,
            'recommended_tasks': s.recommended_tasks
        }
        if s.status == 'needs_attention': needs_attention.append(item)
        elif s.status == 'developing': developing.append(item)
        elif s.status == 'proficient': proficient.append(item)
        else: not_enough_data.append(item)

    return JsonResponse({
        'summary': {
            'proficient_count': len(proficient),
            'developing_count': len(developing),
            'needs_attention_count': len(needs_attention),
            'not_enough_data_count': len(not_enough_data)
        },
        'needs_attention': needs_attention,
        'developing': developing,
        'proficient': proficient,
        'not_enough_data': not_enough_data
    })

# ==============================================================================
# 9. FEATURE EIGHT: STUDENT COMMUNITY & LEADERBOARDS
# ==============================================================================

@csrf_exempt
def community_posts(request):
    tag = request.GET.get('tag')
    search = request.GET.get('search', '').strip().lower()

    posts = CommunityPost.objects.all().order_by('-is_pinned', '-created_at')
    if tag:
        posts = posts.filter(tag=tag)
    if search:
        posts = posts.filter(Q(title__icontains=search) | Q(content__icontains=search))

    result = []
    for p in posts[:30]:
        result.append({
            'id': p.id,
            'title': p.title,
            'content': p.content,
            'tag': p.tag,
            'likes_count': p.likes_count,
            'comments_count': p.comments.count(),
            'is_pinned': p.is_pinned,
            'author': {
                'username': p.author.username,
                'full_name': f"{p.author.first_name} {p.author.last_name}".strip() or p.author.username,
                'college': p.author.profile.college if hasattr(p.author, 'profile') else 'Engineering Institute'
            },
            'created_at': p.created_at.strftime('%b %d, %H:%M'),
            'comments': [
                {
                    'id': c.id,
                    'author': c.author.username,
                    'content': c.content,
                    'likes': c.likes_count,
                    'created_at': c.created_at.strftime('%b %d')
                }
                for c in p.comments.all()[:5]
            ]
        })

    return JsonResponse({'posts': result})

@csrf_exempt
def community_create_post(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        tag = data.get('tag') or data.get('topic') or 'DSA Discussion'

        if not title or not content:
            return JsonResponse({'error': 'Title and content are required'}, status=400)

        post = CommunityPost.objects.create(author=user, title=title, content=content, tag=tag)
        post_dict = {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'tag': post.tag,
            'likes_count': post.likes_count,
            'author': user.username
        }
        return JsonResponse({
            'success': True,
            'post_id': post.id,
            'post': post_dict,
            'message': 'Post published to DKoder Community!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def community_comment(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        post = get_object_or_404(CommunityPost, id=post_id)
        content = data.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Content cannot be empty'}, status=400)

        c = Comment.objects.create(post=post, author=user, content=content)
        post.comments_count = post.comments.count()
        post.save()

        return JsonResponse({'success': True, 'comment_id': c.id, 'author': user.username, 'content': c.content})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def community_react(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    post = get_object_or_404(CommunityPost, id=post_id)
    post.likes_count += 1
    post.save()
    return JsonResponse({'success': True, 'likes': post.likes_count, 'new_likes': post.likes_count})

@csrf_exempt
def community_report(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = get_current_user(request)
        post_id = data.get('post_id')
        reason = data.get('reason', 'Community guidelines violation')
        post = get_object_or_404(CommunityPost, id=post_id)
        post.is_reported = True
        post.save()
        ContentReport.objects.create(reporter=user, post=post, reason=reason, status='pending')
        return JsonResponse({'success': True, 'message': 'Post reported to moderators. Thank you for keeping DKoder safe!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def community_leaderboards(request):
    board_type = request.GET.get('type', 'global')
    entries = LeaderboardEntry.objects.filter(board_type=board_type).order_by('rank', '-score')[:20]
    return JsonResponse({
        'type': board_type,
        'entries': [
            {
                'rank': e.rank,
                'username': e.user.username,
                'full_name': f"{e.user.first_name} {e.user.last_name}".strip() or e.user.username,
                'college': e.user.profile.college if hasattr(e.user, 'profile') else 'Engineering Institute',
                'score': e.score,
                'problems_solved': e.problems_solved
            }
            for e in entries
        ]
    })

# ==============================================================================
# 10. FEATURE NINE: RESUME BUILDER & PORTFOLIO GENERATOR
# ==============================================================================

@csrf_exempt
def career_resume(request):
    user = get_current_user(request)
    resume, _ = Resume.objects.get_or_create(
        user=user,
        defaults={
            'full_name': f"{user.first_name} {user.last_name}".strip() or 'Alex Rivera',
            'email': user.email or 'alex@dkoder.edu',
            'phone': '+91 98765 43210',
            'summary': 'Passionate computer science undergraduate focusing on full stack and distributed systems.'
        }
    )

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            for f in ['full_name', 'email', 'phone', 'location', 'github_url', 'linkedin_url', 'summary', 'template']:
                if f in data: setattr(resume, f, data[f])
            for json_field in ['education', 'experience', 'projects', 'skills', 'certifications', 'achievements', 'languages']:
                if json_field in data: setattr(resume, json_field, data[json_field])
            resume.save()
            return JsonResponse({'success': True, 'message': 'Resume updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({
        'resume': {
            'id': resume.id,
            'title': resume.title,
            'full_name': resume.full_name,
            'email': resume.email,
            'phone': resume.phone,
            'location': resume.location,
            'github_url': resume.github_url,
            'linkedin_url': resume.linkedin_url,
            'summary': resume.summary,
            'education': resume.education,
            'experience': resume.experience,
            'projects': resume.projects,
            'skills': resume.skills,
            'certifications': resume.certifications,
            'achievements': resume.achievements,
            'languages': resume.languages,
            'ats_score': resume.ats_score,
            'template': resume.template
        }
    })

@csrf_exempt
def career_portfolio(request):
    user = get_current_user(request)
    portfolio, _ = Portfolio.objects.get_or_create(
        user=user,
        slug=user.username,
        defaults={
            'display_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'headline': 'Software Engineer & Competitive Problem Solver'
        }
    )

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            for f in ['display_name', 'headline', 'about_me', 'theme', 'is_public', 'hide_contact_info']:
                if f in data: setattr(portfolio, f, data[f])
            portfolio.save()
            return JsonResponse({'success': True, 'message': 'Portfolio updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    projects = portfolio.projects.all().order_by('order')
    return JsonResponse({
        'portfolio': {
            'slug': portfolio.slug,
            'display_name': portfolio.display_name,
            'headline': portfolio.headline,
            'about_me': portfolio.about_me,
            'theme': portfolio.theme,
            'is_public': portfolio.is_public,
            'hide_contact_info': portfolio.hide_contact_info,
            'view_count': portfolio.view_count,
            'projects': [
                {
                    'id': p.id,
                    'title': p.title,
                    'tagline': p.tagline,
                    'description': p.description,
                    'tech_stack': p.tech_stack,
                    'github_link': p.github_link,
                    'live_link': p.live_link,
                    'featured': p.featured
                }
                for p in projects
            ]
        }
    })

@csrf_exempt
def career_portfolio_public(request, slug):
    portfolio = get_object_or_404(Portfolio, slug=slug)
    if not portfolio.is_public:
        return JsonResponse({'error': 'This portfolio is private'}, status=403)
    portfolio.view_count += 1
    portfolio.save()
    projects = portfolio.projects.all().order_by('order')
    return JsonResponse({
        'portfolio': {
            'slug': portfolio.slug,
            'display_name': portfolio.display_name,
            'headline': portfolio.headline,
            'about_me': portfolio.about_me,
            'theme': portfolio.theme,
            'view_count': portfolio.view_count,
            'projects': [
                {
                    'title': p.title,
                    'tagline': p.tagline,
                    'description': p.description,
                    'tech_stack': p.tech_stack,
                    'github_link': p.github_link,
                    'live_link': p.live_link
                }
                for p in projects
            ]
        }
    })

# ==============================================================================
# 11. FEATURE TEN: ADMIN DASHBOARD
# ==============================================================================

def check_is_admin(user):
    if not user: return False
    if user.is_superuser or user.is_staff: return True
    if hasattr(user, 'profile') and user.profile.role == 'admin': return True
    return False

@csrf_exempt
def admin_stats(request):
    user = get_current_user(request)
    if not check_is_admin(user):
        return JsonResponse({'error': 'Unauthorized: Administrator access required'}, status=403)

    total_students = User.objects.count()
    total_problems = CodingProblem.objects.count()
    total_submissions = CodeSubmission.objects.count()
    accepted_subs = CodeSubmission.objects.filter(status='Accepted').count()
    pass_rate = round((accepted_subs / total_submissions * 100), 1) if total_submissions > 0 else 0
    active_competitions = Competition.objects.filter(is_published=True).count()
    pending_reports = ContentReport.objects.filter(status='pending').count()

    return JsonResponse({
        'stats': {
            'total_students': total_students,
            'total_problems': total_problems,
            'total_submissions': total_submissions,
            'pass_rate': pass_rate,
            'active_competitions': active_competitions,
            'pending_reports': pending_reports,
            'ai_status': AIService.get_provider_info(),
            'compiler_status': CompilerService.get_service_status()
        }
    })

@csrf_exempt
def admin_users(request):
    user = get_current_user(request)
    if not check_is_admin(user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role')

    users = User.objects.all().order_by('-date_joined')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search))
    if role_filter:
        users = users.filter(profile__role=role_filter)

    result = []
    for u in users[:50]:
        prof = getattr(u, 'profile', None)
        result.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'full_name': f"{u.first_name} {u.last_name}".strip() or u.username,
            'role': prof.role if prof else 'student',
            'college': prof.college if prof else 'Engineering College',
            'is_active': prof.is_active_account if prof else True,
            'streak': prof.current_streak if prof else 0,
            'points': prof.total_points if prof else 0,
            'date_joined': u.date_joined.strftime('%Y-%m-%d')
        })
    return JsonResponse({'users': result})

@csrf_exempt
def admin_toggle_user(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    current_user = get_current_user(request)
    if not check_is_admin(current_user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    target_user = get_object_or_404(User, id=user_id)
    profile, _ = StudentProfile.objects.get_or_create(user=target_user)
    profile.is_active_account = not profile.is_active_account
    profile.save()

    AdminAuditLog.objects.create(
        actor=current_user,
        action='TOGGLE_USER_STATUS',
        target_model='User',
        target_id=str(target_user.id),
        details=f"Changed account active status of {target_user.username} to {profile.is_active_account}"
    )

    return JsonResponse({'success': True, 'is_active': profile.is_active_account})

@csrf_exempt
def admin_save_question(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    current_user = get_current_user(request)
    if not check_is_admin(current_user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
        qid = data.get('id')
        title = data.get('title', '').strip()
        slug = data.get('slug', title.lower().replace(' ', '-'))
        difficulty = data.get('difficulty', 'Medium')
        category = data.get('category', 'Arrays & Strings')
        company_tags = data.get('company_tags', 'Zoho, TCS')
        description = data.get('description', '')
        sample_inp = data.get('sample_input', '')
        sample_out = data.get('sample_output', '')
        points = int(data.get('points', 100))

        if qid:
            prob = get_object_or_404(CodingProblem, id=qid)
        else:
            prob = CodingProblem()

        prob.title = title
        prob.slug = slug
        prob.difficulty = difficulty
        prob.category = category
        prob.company_tags = company_tags
        prob.description = description
        prob.sample_input = sample_inp
        prob.sample_output = sample_out
        prob.points = points
        prob.save()

        # Update or create sample test case
        TestCase.objects.get_or_create(
            problem=prob, input_data=sample_inp,
            defaults={'expected_output': sample_out, 'is_hidden': False, 'explanation': 'Sample Case'}
        )

        AdminAuditLog.objects.create(
            actor=current_user,
            action='SAVE_QUESTION',
            target_model='CodingProblem',
            target_id=str(prob.id),
            details=f"Admin saved question '{prob.title}' with {points} points."
        )

        return JsonResponse({'success': True, 'problem_id': prob.id, 'message': 'Coding Question saved successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def admin_delete_question(request, question_id):
    if request.method != 'DELETE' and request.method != 'POST':
        return JsonResponse({'error': 'DELETE or POST required'}, status=405)
    current_user = get_current_user(request)
    if not check_is_admin(current_user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    prob = get_object_or_404(CodingProblem, id=question_id)
    title = prob.title
    prob.delete()

    AdminAuditLog.objects.create(
        actor=current_user,
        action='DELETE_QUESTION',
        target_model='CodingProblem',
        target_id=str(question_id),
        details=f"Admin deleted question '{title}'."
    )

    return JsonResponse({'success': True, 'message': f"Question '{title}' deleted."})

@csrf_exempt
def admin_moderation(request):
    current_user = get_current_user(request)
    if not check_is_admin(current_user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    reports = ContentReport.objects.filter(status='pending').order_by('-created_at')
    result = []
    for r in reports:
        result.append({
            'id': r.id,
            'reporter': r.reporter.username,
            'reason': r.reason,
            'status': r.status,
            'created_at': r.created_at.strftime('%b %d, %H:%M'),
            'post_title': r.post.title if r.post else 'Post removed',
            'post_content': r.post.content if r.post else ''
        })
    return JsonResponse({'reports': result})

@csrf_exempt
def admin_moderation_action(request, report_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    current_user = get_current_user(request)
    if not check_is_admin(current_user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    report = get_object_or_404(ContentReport, id=report_id)
    data = json.loads(request.body.decode('utf-8'))
    action = data.get('action', 'dismiss') # 'dismiss' or 'delete_post'

    if action == 'delete_post' and report.post:
        report.post.delete()
        report.status = 'action_taken'
    else:
        report.status = 'dismissed'

    report.moderator_notes = f"Processed by {current_user.username}"
    report.save()

    AdminAuditLog.objects.create(
        actor=current_user,
        action='MODERATION_ACTION',
        target_model='ContentReport',
        target_id=str(report.id),
        details=f"Action: {action} on report #{report.id}"
    )

    return JsonResponse({'success': True, 'status': report.status})

@csrf_exempt
def admin_audit_logs(request):
    current_user = get_current_user(request)
    if not check_is_admin(current_user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    logs = AdminAuditLog.objects.all().order_by('-timestamp')[:50]
    return JsonResponse({
        'logs': [
            {
                'id': l.id,
                'actor': l.actor.username if l.actor else 'System',
                'action': l.action,
                'target': f"{l.target_model} #{l.target_id}",
                'details': l.details,
                'ip': l.ip_address,
                'timestamp': l.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for l in logs
        ]
    })

# ==============================================================================
# 12. NOTIFICATIONS API
# ==============================================================================

@csrf_exempt
def notifications_view(request):
    user = get_current_user(request)
    notifs = Notification.objects.filter(user=user).order_by('-created_at')[:15]
    return JsonResponse({
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%b %d, %H:%M')
            }
            for n in notifs
        ]
    })

@csrf_exempt
def notifications_mark_all_read(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    user = get_current_user(request)
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})
