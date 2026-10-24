from django.db import models
from django.contrib.auth.models import User
import json

# ==============================================================================
# 1. ROLES, PERMISSIONS & STUDENT PROFILES
# ==============================================================================

class RolePermission(models.Model):
    role_name = models.CharField(max_length=50, unique=True) # 'student', 'moderator', 'admin'
    display_name = models.CharField(max_length=100)
    permissions = models.JSONField(default=list)

    def __str__(self):
        return f"{self.display_name} ({self.role_name})"


class StudentProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('moderator', 'Community Moderator'),
        ('admin', 'Administrator'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    college = models.CharField(max_length=255, default='Anna University / Engineering Institute')
    department = models.CharField(max_length=150, default='Computer Science & Engineering')
    graduation_year = models.IntegerField(default=2026)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True, default='Passionate engineer preparing for top campus placements.')
    avatar = models.CharField(max_length=255, default='alex_avatar')
    primary_language = models.CharField(max_length=50, default='Python')
    target_role = models.CharField(max_length=100, default='Full Stack SDE')
    target_companies = models.CharField(max_length=255, default='Zoho, TCS Digital, Amazon, Infosys')
    current_streak = models.IntegerField(default=14)
    best_streak = models.IntegerField(default=28)
    total_points = models.IntegerField(default=1850)
    is_active_account = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# ==============================================================================
# 2. AI MENTOR CONVERSATIONS & MESSAGES
# ==============================================================================

class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=255, default='Placement Prep Mentorship')
    language = models.CharField(max_length=50, default='Python')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class AIMessage(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    code_snippet = models.TextField(blank=True)
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}..."


# ==============================================================================
# 3. ONLINE CODING COMPILER & PROBLEMS (CODELAB)
# ==============================================================================

class CodingProblem(models.Model):
    DIFFICULTY_CHOICES = (
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Medium')
    category = models.CharField(max_length=100, default='Arrays & Strings')
    company_tags = models.CharField(max_length=255, default='Zoho, TCS, Amazon')
    description = models.TextField()
    input_format = models.TextField()
    output_format = models.TextField()
    constraints = models.TextField()
    sample_input = models.TextField()
    sample_output = models.TextField()
    starter_templates = models.JSONField(default=dict)
    time_limit_ms = models.IntegerField(default=2000)
    memory_limit_mb = models.IntegerField(default=256)
    points = models.IntegerField(default=100)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class TestCase(models.Model):
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"TestCase for {self.problem.title} (Hidden: {self.is_hidden})"


class CodeSubmission(models.Model):
    STATUS_CHOICES = (
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Compilation Error', 'Compilation Error'),
        ('Runtime Error', 'Runtime Error'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE, related_name='submissions')
    language = models.CharField(max_length=50, default='python')
    source_code = models.TextField()
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='Accepted')
    execution_time_ms = models.FloatField(default=24.0)
    memory_used_kb = models.IntegerField(default=15400)
    passed_test_cases = models.IntegerField(default=3)
    total_test_cases = models.IntegerField(default=3)
    error_output = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} - {self.status}"


# ==============================================================================
# 4. PERSONALIZED PLACEMENT ROADMAP
# ==============================================================================

class PlacementRoadmap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roadmaps')
    title = models.CharField(max_length=255, default='2026 Dream Placement Preparation Plan')
    education_level = models.CharField(max_length=100, default='B.E / B.Tech')
    department = models.CharField(max_length=100, default='Computer Science')
    grad_year = models.IntegerField(default=2026)
    target_role = models.CharField(max_length=100, default='Full Stack SDE')
    target_companies = models.CharField(max_length=255, default='Zoho, TCS, Amazon')
    current_skill_level = models.CharField(max_length=50, default='Intermediate')
    daily_hours = models.FloatField(default=2.5)
    deadline_date = models.DateField(null=True, blank=True)
    completion_percentage = models.FloatField(default=42.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Roadmap ({self.completion_percentage}%)"


class RoadmapTask(models.Model):
    PRIORITY_CHOICES = (
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    )
    roadmap = models.ForeignKey(PlacementRoadmap, on_delete=models.CASCADE, related_name='tasks')
    category = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    estimated_minutes = models.IntegerField(default=60)
    week_number = models.IntegerField(default=1)
    day_number = models.IntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    resource_url = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"[W{self.week_number}D{self.day_number}] {self.title} ({'✓' if self.is_completed else '○'})"


# ==============================================================================
# 5. SMART STUDENT ANALYTICS & SKILLS
# ==============================================================================

class StudentSkill(models.Model):
    STATUS_CHOICES = (
        ('needs_attention', 'Needs Attention'),
        ('developing', 'Developing'),
        ('proficient', 'Proficient'),
        ('not_enough_data', 'Not Enough Data'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, default='Core CS')
    proficiency_pct = models.FloatField(default=0.0)
    assessment_attempts = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='not_enough_data')
    trend = models.CharField(max_length=20, default='steady') # 'rising', 'steady', 'declining'
    recommended_tasks = models.JSONField(default=list)
    last_assessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.skill_name}: {self.proficiency_pct}%"


class SkillAssessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    assessment_name = models.CharField(max_length=255)
    skill_category = models.CharField(max_length=100)
    score = models.FloatField()
    max_score = models.FloatField()
    accuracy_pct = models.FloatField()
    time_taken_seconds = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.assessment_name}: {self.accuracy_pct}%"


class StudentAnalytics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    problems_attempted = models.IntegerField(default=48)
    problems_solved = models.IntegerField(default=39)
    aptitude_accuracy_pct = models.FloatField(default=84.5)
    interview_avg_score = models.FloatField(default=86.0)
    total_learning_minutes = models.IntegerField(default=2840)
    active_streak_days = models.IntegerField(default=14)
    best_streak_days = models.IntegerField(default=28)
    weekly_activity_json = models.JSONField(default=list)
    monthly_activity_json = models.JSONField(default=list)
    last_activity_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.user.username}"


# ==============================================================================
# 6. AI MOCK INTERVIEWS (INTERVIEW STUDIO)
# ==============================================================================

class MockInterview(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=60, default='Technical Interview')
    target_role = models.CharField(max_length=100, default='SDE-1')
    difficulty = models.CharField(max_length=30, default='Intermediate')
    duration_mins = models.IntegerField(default=20)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='in_progress')
    overall_score = models.FloatField(default=0.0)
    technical_score = models.FloatField(default=0.0)
    communication_score = models.FloatField(default=0.0)
    relevance_score = models.FloatField(default=0.0)
    feedback_summary = models.TextField(blank=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    recommended_topics = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.interview_type} ({self.status})"


class InterviewQuestion(models.Model):
    interview = models.ForeignKey(MockInterview, on_delete=models.CASCADE, related_name='questions')
    question_index = models.IntegerField(default=1)
    question_text = models.TextField()
    category = models.CharField(max_length=100, default='Technical Architecture')
    expected_key_points = models.JSONField(default=list)

    def __str__(self):
        return f"Q{self.question_index}: {self.question_text[:50]}..."


class InterviewAnswer(models.Model):
    question = models.OneToOneField(InterviewQuestion, on_delete=models.CASCADE, related_name='answer')
    student_answer = models.TextField()
    voice_input_used = models.BooleanField(default=False)
    ai_evaluation = models.TextField()
    score = models.FloatField(default=0.0)
    technical_accuracy = models.FloatField(default=0.0)
    relevance = models.FloatField(default=0.0)
    explanation_quality = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to Q{self.question.question_index} (Score: {self.score})"


# ==============================================================================
# 7. LIVE CODING COMPETITIONS (ARENA)
# ==============================================================================

class Competition(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    rules = models.TextField()
    difficulty = models.CharField(max_length=30, default='Medium')
    max_participants = models.IntegerField(default=500)
    is_published = models.BooleanField(default=True)
    is_practice_mode_available = models.BooleanField(default=True)
    problems = models.ManyToManyField(CodingProblem, related_name='competitions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} [{self.difficulty}]"


class CompetitionRegistration(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('competition', 'user')

    def __str__(self):
        return f"{self.user.username} registered for {self.competition.name}"


class CompetitionSubmission(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=50)
    status = models.CharField(max_length=30)
    points_awarded = models.IntegerField(default=0)
    penalty_seconds = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in {self.competition.name}: {self.status}"


class LeaderboardEntry(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True, related_name='leaderboard_entries')
    board_type = models.CharField(max_length=30, default='global') # 'global', 'weekly', 'monthly', 'competition'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    problems_solved = models.IntegerField(default=0)
    penalty_time_seconds = models.IntegerField(default=0)
    period = models.CharField(max_length=30, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rank #{self.rank} - {self.user.username} ({self.score} pts)"


# ==============================================================================
# 8. STUDENT COMMUNITY & DISCUSSION
# ==============================================================================

class CommunityPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    tag = models.CharField(max_length=50, default='DSA Discussion')
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author.username}"


class Comment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"


class Reaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    reaction_type = models.CharField(max_length=20, default='heart') # 'heart', 'bulb', 'fire', 'rocket'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type}"


class StudyGroup(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    focus_area = models.CharField(max_length=100, default='Campus Placements')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members_count = models.IntegerField(default=1)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.members_count} members)"


class GroupMembership(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=20, default='member') # 'admin', 'member'
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


class ContentReport(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
        ('action_taken', 'Action Taken'),
    )
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='filed_reports')
    post = models.ForeignKey(CommunityPost, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderator_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.id} by {self.reporter.username} ({self.status})"


# ==============================================================================
# 9. RESUME BUILDER & PORTFOLIO GENERATOR (CAREER PROFILE)
# ==============================================================================

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=255, default='Campus Placement Master Resume')
    template = models.CharField(max_length=50, default='modern_purple')
    full_name = models.CharField(max_length=255, default='Alex Rivera')
    email = models.CharField(max_length=255, default='alex.rivera@engineering.edu')
    phone = models.CharField(max_length=50, default='+91 98765 43210')
    location = models.CharField(max_length=100, default='Chennai, India')
    github_url = models.CharField(max_length=255, default='https://github.com/alexrivera-tech')
    linkedin_url = models.CharField(max_length=255, default='https://linkedin.com/in/alexrivera-dev')
    portfolio_url = models.CharField(max_length=255, default='https://dkoder.co.in/portfolio/alex')
    summary = models.TextField(default='Pre-final year Computer Science undergraduate passionate about full-stack web development, distributed systems, and competitive problem solving. Solved 300+ placement problems across Zoho, TCS, and Amazon hiring patterns.')
    education = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    projects = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    achievements = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    ats_score = models.FloatField(default=92.0)
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resume: {self.full_name} ({self.template})"


class ResumeVersion(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='versions')
    version_label = models.CharField(max_length=100)
    snapshot_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resume.full_name} - {self.version_label}"


class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    slug = models.SlugField(unique=True)
    display_name = models.CharField(max_length=255, default='Alex Rivera')
    headline = models.CharField(max_length=255, default='Full Stack Engineer & Aspiring Cloud Architect')
    about_me = models.TextField(default='Passionate about building highly scalable systems and beautiful, reactive user experiences with modern stacks.')
    theme = models.CharField(max_length=50, default='dkoder_purple_gold')
    is_public = models.BooleanField(default=True)
    hide_contact_info = models.BooleanField(default=False)
    view_count = models.IntegerField(default=142)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Portfolio: {self.slug} ({'Public' if self.is_public else 'Private'})"


class PortfolioProject(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255)
    description = models.TextField()
    tech_stack = models.JSONField(default=list)
    github_link = models.CharField(max_length=255, blank=True)
    live_link = models.CharField(max_length=255, blank=True)
    featured = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} for {self.portfolio.display_name}"


# ==============================================================================
# 10. ADMIN DASHBOARD, AUDIT LOGS, NOTIFICATIONS & SYSTEM SETTINGS
# ==============================================================================

class AdminAuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100) # 'CREATE_QUESTION', 'SUSPEND_USER', 'RESOLVE_REPORT', etc.
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100, blank=True)
    details = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True, default='127.0.0.1')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} by {self.actor.username if self.actor else 'System'}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='system') # 'submission', 'competition', 'community', 'interview'
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notice to {self.user.username}: {self.title}"


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} = {self.value}"
