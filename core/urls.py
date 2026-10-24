from django.urls import path
from core import views

urlpatterns = [
    # 1. Auth & Session
    path('auth/me', views.auth_me, name='auth_me'),
    path('auth/login', views.auth_login, name='auth_login'),
    path('auth/register', views.auth_register, name='auth_register'),
    path('auth/logout', views.auth_logout, name='auth_logout'),
    path('auth/switch-user', views.auth_switch_user, name='auth_switch_user'),

    # 2. AI Mentor
    path('ai/chat', views.ai_chat, name='ai_chat'),
    path('ai/conversations', views.ai_conversations, name='ai_conversations'),
    path('ai/conversations/<int:conversation_id>', views.ai_conversation_messages, name='ai_conversation_messages'),
    path('ai/clear', views.ai_clear_history, name='ai_clear_history'),

    # 3. CodeLab Compiler
    path('compiler/problems', views.compiler_problems, name='compiler_problems'),
    path('compiler/problems/<slug:slug>', views.compiler_problem_detail, name='compiler_problem_detail'),
    path('compiler/run', views.compiler_run, name='compiler_run'),
    path('compiler/submit', views.compiler_submit, name='compiler_submit'),
    path('compiler/submissions', views.compiler_submissions, name='compiler_submissions'),

    # 4. Placement Roadmap
    path('roadmap', views.roadmap_view, name='roadmap_view'),
    path('roadmap/generate', views.roadmap_generate, name='roadmap_generate'),
    path('roadmap/toggle-task', views.roadmap_toggle_task, name='roadmap_toggle_task'),

    # 5. Student Analytics
    path('analytics', views.analytics_view, name='analytics_view'),

    # 6. AI Mock Interview Studio
    path('interview/start', views.interview_start, name='interview_start'),
    path('interview/answer', views.interview_answer, name='interview_answer'),
    path('interview/finish', views.interview_finish, name='interview_finish'),
    path('interview/history', views.interview_history, name='interview_history'),

    # 7. Live Coding Arena
    path('arena/competitions', views.arena_competitions, name='arena_competitions'),
    path('arena/competitions/<slug:slug>/register', views.arena_register, name='arena_register'),
    path('arena/competitions/<slug:slug>/leaderboard', views.arena_leaderboard, name='arena_leaderboard'),

    # 8. Skill Gap Analyzer
    path('skills/analysis', views.skills_analysis, name='skills_analysis'),
    path('skillgap', views.skills_analysis, name='skillgap_alias'),

    # 9. Community & Leaderboards
    path('community/posts', views.community_posts, name='community_posts'),
    path('community/posts/create', views.community_create_post, name='community_create_post'),
    path('community/posts/<int:post_id>/comment', views.community_comment, name='community_comment'),
    path('community/posts/<int:post_id>/react', views.community_react, name='community_react'),
    path('community/report', views.community_report, name='community_report'),
    path('community/leaderboards', views.community_leaderboards, name='community_leaderboards'),

    # 10. Career Profile (Resume & Portfolio)
    path('career/resume', views.career_resume, name='career_resume'),
    path('career/portfolio', views.career_portfolio, name='career_portfolio'),
    path('career/portfolio/public/<slug:slug>', views.career_portfolio_public, name='career_portfolio_public'),

    # 11. Admin Dashboard
    path('admin/stats', views.admin_stats, name='admin_stats'),
    path('admin/metrics', views.admin_stats, name='admin_metrics_alias'),
    path('admin/users', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/toggle-status', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin/questions/save', views.admin_save_question, name='admin_save_question'),
    path('admin/questions/<int:question_id>/delete', views.admin_delete_question, name='admin_delete_question'),
    path('admin/moderation', views.admin_moderation, name='admin_moderation'),
    path('admin/moderation/<int:report_id>/action', views.admin_moderation_action, name='admin_moderation_action'),
    path('admin/audit-logs', views.admin_audit_logs, name='admin_audit_logs'),

    # 12. Notifications
    path('notifications', views.notifications_view, name='notifications_view'),
    path('notifications/mark-all-read', views.notifications_mark_all_read, name='notifications_mark_all_read'),
]
