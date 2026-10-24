/**
 * DKODER 2.0 — APPLICATION CONTROLLER & INTERACTIVE SUITE
 * Coordinates all 10 platform modules, Chart.js visualizations,
 * Speech-to-Text, CodeLab sandbox, and Workspace navigation.
 */

const DKoderApp = (function() {
  let currentUser = null;
  let activeModule = null;
  let activeProblem = null;
  let activeInterview = null;
  let activeInterviewQuestion = null;
  let speechRecognizer = null;
  let isRecording = false;

  // Chart instances
  let activityChartInstance = null;
  let skillsChartInstance = null;
  let accuracyChartInstance = null;

  // Init
  async function init() {
    console.log("DKoder 2.0 Application Initializing...");
    await refreshCurrentUser();
    setupNavigationListeners();
    setupSpeechRecognition();
  }

  // ---------------------------------------------------------------------------
  // User Authentication & Session
  // ---------------------------------------------------------------------------
  async function refreshCurrentUser() {
    const data = await DKoderAPI.getMe();
    if (data && data.authenticated) {
      currentUser = data.user;
      renderUserCapsule(currentUser);
      renderAdminAccess(currentUser.role === 'admin');
    }
  }

  function renderUserCapsule(user) {
    const capsule = document.getElementById('user-session-capsule');
    if (!capsule) return;

    const roleBadgeClass = user.role === 'admin' 
      ? 'bg-rose-500 text-white' 
      : (user.role === 'moderator' ? 'bg-indigo-500 text-white' : 'bg-dkoder-yellow text-dkoder-dark');

    capsule.innerHTML = `
      <div class="flex items-center space-x-2.5 bg-[#1E0D47]/80 border-2 border-dkoder-yellow/40 rounded-full px-3 py-1.5 shadow-sm">
        <div class="w-8 h-8 rounded-full bg-dkoder-yellow text-dkoder-dark font-extrabold flex items-center justify-center text-xs border border-white shadow-sm">
          ${user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
        </div>
        <div class="hidden sm:flex flex-col text-left">
          <div class="flex items-center space-x-1.5">
            <span class="text-xs font-bold text-white leading-none">${user.full_name || user.username}</span>
            <span class="text-[9px] font-black uppercase px-1.5 py-0.2 rounded-full ${roleBadgeClass}">
              ${user.role}
            </span>
          </div>
          <span class="text-[10px] text-dkoder-yellow font-extrabold tracking-tight">⭐ ${user.points || 1850} pts &bull; 🔥 ${user.streak || 14}d streak</span>
        </div>
        <button onclick="DKoderApp.openNotificationDrawer()" class="relative p-1.5 text-dkoder-purpleSoft hover:text-dkoder-yellow transition-colors" title="Notifications">
          <i class="fa-solid fa-bell text-sm"></i>
          ${user.unread_notifications ? `<span class="absolute top-0 right-0 w-2 h-2 rounded-full bg-rose-500 animate-ping"></span><span class="absolute top-0 right-0 w-2 h-2 rounded-full bg-rose-500"></span>` : ''}
        </button>
        <button onclick="DKoderApp.openAuthModal()" class="px-2.5 py-1 text-xs font-bold text-white hover:text-dkoder-yellow bg-white/10 hover:bg-white/20 rounded-full transition-colors" title="Switch User / Login">
          <i class="fa-solid fa-arrow-right-arrow-left text-[11px] mr-1"></i> Switch
        </button>
      </div>
    `;
  }

  function renderAdminAccess(isAdmin) {
    const adminLink = document.getElementById('nav-admin-link');
    if (adminLink) {
      adminLink.style.display = 'flex';
      if (isAdmin) {
        adminLink.classList.remove('opacity-60');
      }
    }
  }

  async function quickSwitchUser(username) {
    await DKoderAPI.switchUser(username);
    await refreshCurrentUser();
    closeModal('auth-modal');
    showToast(`Switched account to ${username.toUpperCase()}`, 'success');
    if (activeModule) {
      loadModule(activeModule);
    }
  }

  // ---------------------------------------------------------------------------
  // Workspace Navigation (Homepage <-> 10 Modules)
  // ---------------------------------------------------------------------------
  function setupNavigationListeners() {
    window.addEventListener('hashchange', handleRouteHash);
    if (window.location.hash) {
      handleRouteHash();
    }
  }

  function handleRouteHash() {
    const hash = window.location.hash.replace('#', '');
    const validModules = ['ai-mentor', 'codelab', 'roadmap', 'analytics', 'interview', 'arena', 'skills', 'community', 'career', 'admin'];
    if (validModules.includes(hash)) {
      openWorkspace(hash);
    } else if (hash === 'home' || hash === '') {
      closeWorkspace();
    }
  }

  function openWorkspace(moduleKey) {
    activeModule = moduleKey;
    window.location.hash = moduleKey;

    const homeContainer = document.getElementById('dkoder-homepage-content');
    const workspaceContainer = document.getElementById('dkoder-2-workspace');
    if (homeContainer && workspaceContainer) {
      homeContainer.classList.add('hidden');
      workspaceContainer.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update Workspace Header Active Module Title
    const moduleTitles = {
      'ai-mentor': { title: 'DKoder AI Mentor', icon: 'fa-robot', desc: 'Placement Intelligence & Code Tutor' },
      'codelab': { title: 'DKoder CodeLab IDE', icon: 'fa-code', desc: 'Online Isolated Multi-Language Sandbox' },
      'roadmap': { title: 'My Placement Roadmap', icon: 'fa-map-location-dot', desc: 'Personalized 12-Category Dream Company Plan' },
      'analytics': { title: 'Smart Student Analytics', icon: 'fa-chart-line', desc: 'Interactive Performance, Streak & Submission Data' },
      'interview': { title: 'Interview Studio', icon: 'fa-microphone-lines', desc: 'AI-Evaluated Technical & HR Mock Rounds' },
      'arena': { title: 'DKoder Arena', icon: 'fa-trophy', desc: 'Live Coding Competitions & Real-Time Podium' },
      'skills': { title: 'Skill Gap Analyzer', icon: 'fa-bullseye', desc: 'Proficiency Diagnostics Across 14 Core Skills' },
      'community': { title: 'DKoder Community', icon: 'fa-users', desc: 'Peer Discussions, Study Groups & Leaderboards' },
      'career': { title: 'Career Profile (Resume & Portfolio)', icon: 'fa-id-card-clip', desc: 'ATS-Optimized Resume & Live Public Portfolio' },
      'admin': { title: 'Admin Command Center', icon: 'fa-shield-halved', desc: 'Role-Based Management, Moderation & Audit Logs' }
    };

    const info = moduleTitles[moduleKey] || { title: 'DKoder 2.0', icon: 'fa-cubes', desc: 'Engineering Platform' };
    const titleEl = document.getElementById('ws-current-title');
    const descEl = document.getElementById('ws-current-desc');
    const iconEl = document.getElementById('ws-current-icon');
    const selectEl = document.getElementById('ws-module-select');

    if (titleEl) titleEl.innerText = info.title;
    if (descEl) descEl.innerText = info.desc;
    if (iconEl) iconEl.className = `fa-solid ${info.icon} text-dkoder-yellow text-xl`;
    if (selectEl) selectEl.value = moduleKey;

    // Show selected module view, hide others
    document.querySelectorAll('.module-workspace-view').forEach(view => {
      view.classList.add('hidden');
    });
    const targetView = document.getElementById(`view-${moduleKey}`);
    if (targetView) {
      targetView.classList.remove('hidden');
    }

    // Load data for specific module
    loadModule(moduleKey);
  }

  function closeWorkspace() {
    activeModule = null;
    window.location.hash = 'home';
    const homeContainer = document.getElementById('dkoder-homepage-content');
    const workspaceContainer = document.getElementById('dkoder-2-workspace');
    if (homeContainer && workspaceContainer) {
      workspaceContainer.classList.add('hidden');
      homeContainer.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function loadModule(moduleKey) {
    switch (moduleKey) {
      case 'ai-mentor': loadAIMentor(); break;
      case 'codelab': loadCodeLab(); break;
      case 'roadmap': loadRoadmap(); break;
      case 'analytics': loadAnalytics(); break;
      case 'interview': loadInterviewStudio(); break;
      case 'arena': loadArena(); break;
      case 'skills': loadSkills(); break;
      case 'community': loadCommunity(); break;
      case 'career': loadCareerProfile(); break;
      case 'admin': loadAdminDashboard(); break;
    }
  }

  // ---------------------------------------------------------------------------
  // 1. FEATURE ONE: AI MENTOR
  // ---------------------------------------------------------------------------
  let currentConvoId = null;

  async function loadAIMentor() {
    const listEl = document.getElementById('ai-convo-list');
    const data = await DKoderAPI.getConversations();
    if (listEl && data.conversations) {
      listEl.innerHTML = data.conversations.map(c => `
        <button onclick="DKoderApp.selectAIConversation(${c.id})" class="w-full text-left p-2.5 rounded-xl hover:bg-white/10 transition-colors flex items-center space-x-2.5 ${currentConvoId === c.id ? 'bg-white/15 border border-dkoder-yellow/50' : ''}">
          <i class="fa-regular fa-message text-xs text-dkoder-yellow"></i>
          <div class="truncate flex-1">
            <p class="text-xs font-bold text-white truncate">${escapeHtml(c.title)}</p>
            <p class="text-[10px] text-dkoder-purpleSoft">${c.updated_at}</p>
          </div>
        </button>
      `).join('');
    }

    // Set Provider badge
    const provEl = document.getElementById('ai-provider-badge');
    if (provEl && data.provider_info) {
      provEl.innerHTML = `
        <span class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold ${data.provider_info.is_mock ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'}">
          <span class="w-2 h-2 rounded-full ${data.provider_info.is_mock ? 'bg-amber-400' : 'bg-emerald-400'} animate-pulse"></span>
          <span>${data.provider_info.provider}</span>
        </span>
      `;
    }
  }

  async function selectAIConversation(convoId) {
    currentConvoId = convoId;
    const data = await DKoderAPI.getConversationMessages(convoId);
    const stream = document.getElementById('ai-message-stream');
    if (stream && data.messages) {
      stream.innerHTML = data.messages.map(m => renderAIMessageHTML(m.role, m.content, m.created_at)).join('');
      stream.scrollTop = stream.scrollHeight;
    }
    loadAIMentor();
  }

  function startNewAIConversation() {
    currentConvoId = null;
    const stream = document.getElementById('ai-message-stream');
    if (stream) {
      stream.innerHTML = `
        <div class="text-center py-10 px-4">
          <div class="w-16 h-16 rounded-2xl bg-dkoder-yellow text-dkoder-dark flex items-center justify-center text-3xl font-black mx-auto mb-4 border-2 border-white shadow-brutal">
            <i class="fa-solid fa-robot"></i>
          </div>
          <h3 class="font-display font-extrabold text-xl text-white">DKoder AI Mentor Active</h3>
          <p class="text-xs text-dkoder-purpleSoft max-w-md mx-auto mt-2">
            Ask any question on Zoho/TCS patterns, paste compiler errors for instant line-by-line debugging, or request aptitude speed shortcuts.
          </p>
        </div>
      `;
    }
  }

  async function sendAIMessage() {
    const input = document.getElementById('ai-chat-input');
    const langSelect = document.getElementById('ai-lang-select');
    const stream = document.getElementById('ai-message-stream');
    if (!input || !input.value.trim()) return;

    const userText = input.value.trim();
    const lang = langSelect ? langSelect.value : 'Python';
    input.value = '';

    // Append User Message to Stream
    stream.innerHTML += renderAIMessageHTML('user', userText, 'Just now');
    stream.scrollTop = stream.scrollHeight;

    // Append Typing Indicator
    const typingId = 'typing-' + Date.now();
    stream.innerHTML += `
      <div id="${typingId}" class="flex items-start space-x-3 my-4">
        <div class="w-8 h-8 rounded-xl bg-dkoder-yellow text-dkoder-dark font-black flex items-center justify-center text-xs shrink-0 border border-white">
          <i class="fa-solid fa-robot"></i>
        </div>
        <div class="bg-[#1E0D47] border border-dkoder-yellow/40 rounded-2xl px-4 py-3 text-xs text-dkoder-purpleSoft flex items-center space-x-2">
          <span>AI Mentor is thinking</span>
          <span class="typing-cursor"></span>
        </div>
      </div>
    `;
    stream.scrollTop = stream.scrollHeight;

    const res = await DKoderAPI.chatAI(userText, lang, currentConvoId);
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    if (res && res.success) {
      currentConvoId = res.conversation_id;
      stream.innerHTML += renderAIMessageHTML('assistant', res.response, 'Just now');
      stream.scrollTop = stream.scrollHeight;
      loadAIMentor();
    } else {
      stream.innerHTML += renderAIMessageHTML('assistant', '⚠️ An error occurred while generating the response. Please try again.', 'Now');
    }
  }

  function handlePromptChip(chipText) {
    const input = document.getElementById('ai-chat-input');
    if (input) {
      input.value = chipText;
      sendAIMessage();
    }
  }

  function renderAIMessageHTML(role, text, time) {
    const isUser = role === 'user';
    const formattedContent = formatMarkdownCodeBlocks(text);

    return `
      <div class="flex items-start space-x-3 my-4 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}">
        <div class="w-8 h-8 rounded-xl ${isUser ? 'bg-indigo-600 text-white' : 'bg-dkoder-yellow text-dkoder-dark'} font-black flex items-center justify-center text-xs shrink-0 border border-white shadow-sm">
          ${isUser ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>'}
        </div>
        <div class="max-w-[85%] md:max-w-[75%] ${isUser ? 'bg-[#280F57] text-white border-white/20' : 'bg-[#190835] text-dkoder-purpleSoft border-dkoder-yellow/40'} border rounded-2xl p-4 shadow-sm text-xs leading-relaxed">
          <div class="flex items-center justify-between mb-1.5 opacity-60 text-[10px] font-space font-bold">
            <span>${isUser ? 'You' : 'DKoder Mentor'}</span>
            <span>${time || ''}</span>
          </div>
          <div class="prose prose-invert max-w-none text-xs space-y-2">
            ${formattedContent}
          </div>
        </div>
      </div>
    `;
  }

  function formatMarkdownCodeBlocks(content) {
    if (!content) return '';
    // Format ```code``` blocks with copy buttons
    return content.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, function(match, lang, code) {
      const escaped = escapeHtml(code.trim());
      const copyId = 'code-' + Math.random().toString(36).substring(2, 9);
      return `
        <div class="my-3 rounded-xl overflow-hidden border border-dkoder-yellow/40 bg-[#0d041c]">
          <div class="flex items-center justify-between px-3 py-1.5 bg-[#140628] border-b border-white/10 text-[11px] font-mono text-dkoder-yellow">
            <span>${lang || 'code'}</span>
            <button onclick="DKoderApp.copyCode('${copyId}')" class="hover:text-white transition-colors flex items-center space-x-1">
              <i class="fa-regular fa-copy"></i>
              <span>Copy</span>
            </button>
          </div>
          <pre class="p-3 text-xs font-mono text-white overflow-x-auto"><code id="${copyId}">${escaped}</code></pre>
        </div>
      `;
    }).replace(/\n/g, '<br/>');
  }

  function copyCode(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
      navigator.clipboard.writeText(el.innerText).then(() => {
        showToast('Code snippet copied to clipboard!', 'success');
      });
    }
  }

  async function clearAIChat() {
    if (confirm("Are you sure you want to clear your AI conversation history?")) {
      await DKoderAPI.clearAIHistory();
      startNewAIConversation();
      loadAIMentor();
      showToast('Conversation history cleared.', 'info');
    }
  }

  // ---------------------------------------------------------------------------
  // 2. FEATURE TWO: CODELAB COMPILER
  // ---------------------------------------------------------------------------
  let currentProblemData = null;

  async function loadCodeLab() {
    const selectEl = document.getElementById('codelab-problem-select');
    const data = await DKoderAPI.getProblems();
    if (data && data.problems && data.problems.length > 0) {
      if (selectEl) {
        selectEl.innerHTML = data.problems.map(p => `
          <option value="${p.slug}">${p.title} (${p.difficulty} · ${p.company_tags})</option>
        `).join('');
      }
      activeProblem = data.problems[0].slug;
      await selectCodeLabProblem(activeProblem);
    }
    loadSubmissionsHistory();
  }

  async function selectCodeLabProblem(slug) {
    const p = await DKoderAPI.getProblemDetail(slug);
    currentProblemData = p;

    // Render problem details
    const titleEl = document.getElementById('codelab-p-title');
    const diffEl = document.getElementById('codelab-p-diff');
    const tagsEl = document.getElementById('codelab-p-tags');
    const descEl = document.getElementById('codelab-p-desc');
    const sampleInEl = document.getElementById('codelab-p-sample-in');
    const sampleOutEl = document.getElementById('codelab-p-sample-out');

    if (titleEl) titleEl.innerText = p.title;
    if (diffEl) {
      diffEl.innerText = p.difficulty;
      diffEl.className = `px-2 py-0.5 rounded text-[10px] font-black uppercase ${p.difficulty === 'Easy' ? 'bg-emerald-400 text-dkoder-dark' : (p.difficulty === 'Medium' ? 'bg-dkoder-yellow text-dkoder-dark' : 'bg-rose-500 text-white')}`;
    }
    if (tagsEl) tagsEl.innerText = p.company_tags;
    if (descEl) descEl.innerText = p.description;
    if (sampleInEl) sampleInEl.innerText = p.sample_input;
    if (sampleOutEl) sampleOutEl.innerText = p.sample_output;

    // Load code template for current language
    changeCodeLabLanguage();
  }

  function changeCodeLabLanguage() {
    const langSelect = document.getElementById('codelab-lang-select');
    const editor = document.getElementById('codelab-editor');
    if (!langSelect || !editor || !currentProblemData) return;

    const lang = langSelect.value.toLowerCase();
    const templates = currentProblemData.starter_templates || {};
    editor.value = templates[lang] || `# Starter code for ${currentProblemData.title} in ${lang}\n\ndef solve():\n    pass\n`;

    // Also populate custom input with sample input by default
    const customIn = document.getElementById('codelab-custom-input');
    if (customIn && !customIn.value) {
      customIn.value = currentProblemData.sample_input || '';
    }
  }

  async function runCodeLabCode() {
    const langSelect = document.getElementById('codelab-lang-select');
    const editor = document.getElementById('codelab-editor');
    const customIn = document.getElementById('codelab-custom-input');
    const consoleEl = document.getElementById('codelab-console');
    const runBtn = document.getElementById('codelab-run-btn');

    if (!editor) return;
    const lang = langSelect.value;
    const code = editor.value;
    const inp = customIn ? customIn.value : '';

    if (runBtn) {
      runBtn.disabled = true;
      runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Running...`;
    }
    if (consoleEl) {
      consoleEl.innerHTML = `<span class="text-dkoder-yellow">Executing ${lang.toUpperCase()} in sandboxed container...</span>`;
    }

    const res = await DKoderAPI.runCode(lang, code, inp);

    if (runBtn) {
      runBtn.disabled = false;
      runBtn.innerHTML = `<i class="fa-solid fa-play text-xs mr-1.5"></i> Run Code`;
    }

    if (consoleEl) {
      const isErr = res.status === 'Runtime Error' || res.status === 'Compilation Error' || res.status === 'Time Limit Exceeded';
      consoleEl.innerHTML = `
        <div class="mb-2 flex items-center justify-between text-[11px] pb-1 border-b border-white/10 font-mono">
          <span class="${isErr ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}">${res.status || 'Success'}</span>
          <span class="text-dkoder-purpleSoft">${res.execution_time_ms || 18} ms · ${res.memory_kb || 14000} KB</span>
        </div>
        <pre class="text-xs font-mono whitespace-pre-wrap ${isErr ? 'text-rose-300' : 'text-white'}">${escapeHtml(res.stdout || res.stderr || 'No output produced.')}</pre>
      `;
    }
  }

  async function submitCodeLabSolution() {
    const langSelect = document.getElementById('codelab-lang-select');
    const editor = document.getElementById('codelab-editor');
    const submitBtn = document.getElementById('codelab-submit-btn');
    const consoleEl = document.getElementById('codelab-console');

    if (!currentProblemData || !editor) return;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Evaluating Test Cases...`;
    }

    const res = await DKoderAPI.submitCode(currentProblemData.id, langSelect.value, editor.value);

    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<i class="fa-solid fa-cloud-arrow-up text-xs mr-1.5"></i> Submit Solution`;
    }

    if (consoleEl && res) {
      const isAccepted = res.status === 'Accepted';
      if (isAccepted && window.confetti) {
        window.confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
        showToast('Accepted! All test cases passed successfully! ⭐ +100 Points', 'success');
      }

      consoleEl.innerHTML = `
        <div class="mb-3 p-3 rounded-xl border ${isAccepted ? 'bg-emerald-950/40 border-emerald-500/50' : 'bg-rose-950/40 border-rose-500/50'}">
          <div class="flex items-center justify-between">
            <span class="text-base font-extrabold ${isAccepted ? 'text-emerald-400' : 'text-rose-400'}">
              ${isAccepted ? '✓ Accepted' : '✗ ' + res.status}
            </span>
            <span class="text-xs font-mono text-dkoder-yellow font-bold">${res.passed_test_cases}/${res.total_test_cases} Testcases Passed</span>
          </div>
          <p class="text-[11px] text-dkoder-purpleSoft mt-1">Execution Time: ${res.execution_time_ms} ms · Memory: ${res.memory_used_kb} KB</p>
        </div>
        <div class="space-y-1.5">
          ${(res.test_results || []).map(tr => `
            <div class="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/10 text-[11px] font-mono">
              <span class="text-white">Testcase #${tr.index} ${tr.is_hidden ? '(Hidden Evaluation)' : ''}</span>
              <span class="${tr.status === 'Passed' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}">${tr.status}</span>
            </div>
          `).join('')}
        </div>
      `;
    }

    loadSubmissionsHistory();
    refreshCurrentUser();
  }

  async function loadSubmissionsHistory() {
    const listEl = document.getElementById('codelab-submissions-list');
    const data = await DKoderAPI.getSubmissions();
    if (listEl && data.submissions) {
      listEl.innerHTML = data.submissions.map(s => `
        <tr class="border-b border-white/5 hover:bg-white/5 text-xs">
          <td class="py-2.5 px-3 font-semibold text-white">${escapeHtml(s.problem_title)}</td>
          <td class="py-2.5 px-3 text-dkoder-yellow uppercase font-mono">${s.language}</td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${s.status === 'Accepted' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}">
              ${s.status}
            </span>
          </td>
          <td class="py-2.5 px-3 font-mono text-dkoder-purpleSoft">${s.exec_time}</td>
          <td class="py-2.5 px-3 text-dkoder-purpleSoft">${s.submitted_at}</td>
        </tr>
      `).join('');
    }
  }

  // ---------------------------------------------------------------------------
  // 3. FEATURE THREE: PLACEMENT ROADMAP
  // ---------------------------------------------------------------------------
  async function loadRoadmap() {
    const data = await DKoderAPI.getRoadmap();
    const container = document.getElementById('roadmap-weeks-container');
    const pctEl = document.getElementById('roadmap-pct-text');
    const barEl = document.getElementById('roadmap-progress-bar');
    const statsEl = document.getElementById('roadmap-stats-label');

    if (!data || !data.has_roadmap) {
      if (container) {
        container.innerHTML = `
          <div class="text-center py-12 bg-[#1E0D47]/50 rounded-2xl border-2 border-dashed border-dkoder-yellow/40 p-6">
            <i class="fa-solid fa-map-location-dot text-4xl text-dkoder-yellow mb-3"></i>
            <h4 class="text-lg font-bold text-white">No Active Placement Roadmap</h4>
            <p class="text-xs text-dkoder-purpleSoft max-w-sm mx-auto mt-1 mb-4">Click below to generate a tailored 12-category placement plan for Zoho, TCS, and Amazon.</p>
            <button onclick="DKoderApp.openRoadmapModal()" class="btn-dk-yellow px-5 py-2.5 rounded-full text-xs">Generate My Placement Roadmap</button>
          </div>
        `;
      }
      return;
    }

    const rm = data.roadmap;
    if (pctEl) pctEl.innerText = `${rm.completion_percentage}%`;
    if (barEl) barEl.style.width = `${rm.completion_percentage}%`;
    if (statsEl) statsEl.innerText = `${rm.completed_tasks} of ${rm.total_tasks} Placement Milestones Completed`;

    if (container && rm.weeks) {
      container.innerHTML = Object.entries(rm.weeks).map(([weekTitle, tasks]) => `
        <div class="bg-[#1E0D47]/80 border-2 border-white/10 rounded-2xl p-5 mb-5 shadow-sm">
          <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/10">
            <h4 class="font-display font-extrabold text-base text-dkoder-yellow flex items-center space-x-2">
              <i class="fa-regular fa-calendar-check text-xs"></i>
              <span>${weekTitle}</span>
            </h4>
            <span class="text-xs font-space font-bold text-dkoder-purpleSoft">${tasks.filter(t => t.is_completed).length}/${tasks.length} Completed</span>
          </div>
          <div class="space-y-3">
            ${tasks.map(t => `
              <div class="flex items-start space-x-3 p-3 rounded-xl bg-[#140628]/60 border border-white/10 hover:border-dkoder-yellow/40 transition-colors">
                <input type="checkbox" ${t.is_completed ? 'checked' : ''} onchange="DKoderApp.toggleRoadmapTask(${t.id})" class="dk-checkbox shrink-0 mt-0.5" />
                <div class="flex-1 min-w-0">
                  <div class="flex flex-wrap items-center gap-2 mb-1">
                    <span class="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-dkoder-yellow/20 text-dkoder-yellow font-space">${t.category}</span>
                    <span class="text-[10px] font-bold px-1.5 py-0.2 rounded ${t.priority === 'High' ? 'bg-rose-500/20 text-rose-300' : 'bg-white/10 text-white'}">${t.priority} Priority</span>
                    <span class="text-[10px] text-dkoder-purpleSoft"><i class="fa-regular fa-clock mr-1"></i>${t.estimated_minutes} min</span>
                  </div>
                  <h5 class="text-xs font-bold ${t.is_completed ? 'line-through text-dkoder-purpleSoft' : 'text-white'}">${escapeHtml(t.title)}</h5>
                  <p class="text-[11px] text-dkoder-purpleSoft mt-0.5">${escapeHtml(t.description)}</p>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('');
    }
  }

  async function toggleRoadmapTask(taskId) {
    const res = await DKoderAPI.toggleRoadmapTask(taskId);
    if (res && res.success) {
      if (res.is_completed && window.confetti) {
        window.confetti({ particleCount: 30, spread: 45, origin: { y: 0.7 } });
      }
      loadRoadmap();
    }
  }

  function openRoadmapModal() {
    openModal('roadmap-generator-modal');
  }

  async function submitGenerateRoadmap(e) {
    e.preventDefault();
    const form = e.target;
    const payload = {
      target_role: form.target_role.value,
      target_companies: form.target_companies.value,
      daily_hours: form.daily_hours.value,
      skill_level: form.skill_level.value
    };
    await DKoderAPI.generateRoadmap(payload);
    closeModal('roadmap-generator-modal');
    showToast('Placement Roadmap generated successfully!', 'success');
    loadRoadmap();
  }

  // ---------------------------------------------------------------------------
  // 4. FEATURE FOUR: SMART ANALYTICS
  // ---------------------------------------------------------------------------
  async function loadAnalytics() {
    const data = await DKoderAPI.getAnalytics();
    if (!data) return;

    const m = data.metrics;
    document.getElementById('stat-total-attempted').innerText = m.total_attempted;
    document.getElementById('stat-total-accepted').innerText = m.total_accepted;
    document.getElementById('stat-success-rate').innerText = `${m.success_rate}%`;
    document.getElementById('stat-aptitude-accuracy').innerText = `${m.aptitude_accuracy}%`;
    document.getElementById('stat-interview-score').innerText = `${m.interview_avg_score}/100`;
    document.getElementById('stat-learning-hours').innerText = `${m.total_hours} hrs`;
    document.getElementById('stat-active-streak').innerText = `${m.active_streak} Days`;

    // Render Chart.js
    if (window.Chart) {
      renderActivityChart(data.weekly_activity);
      renderSkillsChart(data.skills_breakdown);
    }
  }

  function renderActivityChart(weekly) {
    const ctx = document.getElementById('chart-activity-canvas');
    if (!ctx) return;
    if (activityChartInstance) activityChartInstance.destroy();

    const labels = weekly.map(w => w.day);
    const problemsData = weekly.map(w => w.problems);

    activityChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Problems Solved',
          data: problemsData,
          borderColor: '#FCC419',
          backgroundColor: 'rgba(252, 196, 25, 0.15)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointBackgroundColor: '#FCC419',
          pointRadius: 5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#B7AEDA' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#B7AEDA', stepSize: 2 } }
        }
      }
    });
  }

  function renderSkillsChart(skills) {
    const ctx = document.getElementById('chart-skills-canvas');
    if (!ctx) return;
    if (skillsChartInstance) skillsChartInstance.destroy();

    const labels = (skills || []).map(s => s.name);
    const values = (skills || []).map(s => s.proficiency);

    skillsChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Proficiency %',
          data: values,
          backgroundColor: '#FCC419',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#B7AEDA', font: { size: 10 } } },
          y: { max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#B7AEDA' } }
        }
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 5. FEATURE FIVE: AI MOCK INTERVIEW STUDIO
  // ---------------------------------------------------------------------------
  function loadInterviewStudio() {
    document.getElementById('interview-setup-screen').classList.remove('hidden');
    document.getElementById('interview-room-screen').classList.add('hidden');
    document.getElementById('interview-report-screen').classList.add('hidden');
  }

  async function startMockInterview(type) {
    const data = await DKoderAPI.startInterview({
      interview_type: type,
      target_role: 'Software Developer (Campus Placement)',
      difficulty: 'Medium'
    });

    if (data && data.success) {
      activeInterview = data.interview_id;
      activeInterviewQuestion = data.current_question;

      document.getElementById('interview-setup-screen').classList.add('hidden');
      document.getElementById('interview-room-screen').classList.remove('hidden');
      document.getElementById('interview-report-screen').classList.add('hidden');

      renderActiveInterviewQuestion(data.current_question, 1, data.total_questions);
    }
  }

  function renderActiveInterviewQuestion(q, currentIdx, total) {
    document.getElementById('interview-q-index').innerText = `Question ${q.index || currentIdx} of ${total || 5}`;
    document.getElementById('interview-q-category').innerText = q.category;
    document.getElementById('interview-q-text').innerText = q.text;
    document.getElementById('interview-answer-input').value = '';
    document.getElementById('interview-feedback-box').classList.add('hidden');
    document.getElementById('interview-submit-btn').classList.remove('hidden');
    document.getElementById('interview-next-btn').classList.add('hidden');
  }

  async function submitInterviewAnswer() {
    const ansInput = document.getElementById('interview-answer-input');
    const submitBtn = document.getElementById('interview-submit-btn');
    if (!ansInput || !ansInput.value.trim()) {
      showToast('Please type or speak your answer before submitting.', 'info');
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> AI Evaluating Answer...`;
    }

    const res = await DKoderAPI.submitInterviewAnswer({
      interview_id: activeInterview,
      question_id: activeInterviewQuestion.id,
      answer_text: ansInput.value.trim(),
      voice_used: false
    });

    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `Submit Answer for Evaluation`;
    }

    if (res && res.success) {
      const fbBox = document.getElementById('interview-feedback-box');
      fbBox.classList.remove('hidden');
      document.getElementById('interview-fb-score').innerText = `${res.evaluation.overall_score}/100`;
      document.getElementById('interview-fb-text').innerText = res.evaluation.feedback;
      document.getElementById('interview-fb-tips').innerText = res.evaluation.suggested_improvements || 'State time complexity explicitly.';

      document.getElementById('interview-submit-btn').classList.add('hidden');
      const nextBtn = document.getElementById('interview-next-btn');
      nextBtn.classList.remove('hidden');

      if (res.has_next && res.next_question) {
        activeInterviewQuestion = res.next_question;
        nextBtn.innerText = 'Next Question →';
        nextBtn.onclick = () => renderActiveInterviewQuestion(res.next_question);
      } else {
        nextBtn.innerText = 'Complete Interview & View Full Report ✓';
        nextBtn.onclick = finishMockInterview;
      }
    }
  }

  async function finishMockInterview() {
    const res = await DKoderAPI.finishInterview(activeInterview);
    if (res && res.success) {
      if (window.confetti) window.confetti({ particleCount: 80, spread: 60 });
      document.getElementById('interview-room-screen').classList.add('hidden');
      document.getElementById('interview-report-screen').classList.remove('hidden');

      const r = res.report;
      document.getElementById('rep-overall-score').innerText = `${r.overall_score}/100`;
      document.getElementById('rep-tech-score').innerText = `${r.technical_score}/100`;
      document.getElementById('rep-comm-score').innerText = `${r.communication_score}/100`;
      document.getElementById('rep-summary').innerText = r.feedback_summary;
      document.getElementById('rep-strengths').innerHTML = (r.strengths || []).map(s => `<li>✓ ${escapeHtml(s)}</li>`).join('');
      document.getElementById('rep-weaknesses').innerHTML = (r.weaknesses || []).map(w => `<li>○ ${escapeHtml(w)}</li>`).join('');
    }
  }

  // Speech Recognition for Voice Input
  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      speechRecognizer = new SpeechRecognition();
      speechRecognizer.continuous = true;
      speechRecognizer.interimResults = true;
      speechRecognizer.lang = 'en-US';

      speechRecognizer.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        const ansInput = document.getElementById('interview-answer-input');
        if (ansInput) {
          ansInput.value = (ansInput.value + ' ' + transcript).trim();
        }
      };

      speechRecognizer.onerror = () => {
        stopVoiceRecording();
      };
    }
  }

  function toggleVoiceRecording() {
    if (!speechRecognizer) {
      alert("Speech recognition is not supported in this browser. Please use Chrome/Edge or type your response.");
      return;
    }
    if (!isRecording) {
      speechRecognizer.start();
      isRecording = true;
      document.getElementById('voice-wave-anim').classList.remove('hidden');
      document.getElementById('voice-record-btn').classList.add('bg-rose-500', 'text-white');
      showToast('Voice recording active. Speak clearly.', 'info');
    } else {
      stopVoiceRecording();
    }
  }

  function stopVoiceRecording() {
    if (speechRecognizer && isRecording) {
      speechRecognizer.stop();
      isRecording = false;
      const wave = document.getElementById('voice-wave-anim');
      if (wave) wave.classList.add('hidden');
      const btn = document.getElementById('voice-record-btn');
      if (btn) btn.classList.remove('bg-rose-500', 'text-white');
    }
  }

  // ---------------------------------------------------------------------------
  // 6. FEATURE SIX: ARENA COMPETITIONS
  // ---------------------------------------------------------------------------
  async function loadArena() {
    const listEl = document.getElementById('arena-competitions-list');
    const data = await DKoderAPI.getCompetitions();
    if (listEl && data.competitions) {
      listEl.innerHTML = data.competitions.map(c => `
        <div class="p-5 rounded-2xl bg-[#1E0D47]/80 border-2 border-white/10 hover:border-dkoder-yellow/50 transition-all shadow-sm">
          <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${c.status === 'Live Now' ? 'bg-emerald-400 text-dkoder-dark animate-pulse' : 'bg-white/10 text-white'}">
              ${c.status}
            </span>
            <span class="text-xs font-mono text-dkoder-yellow font-bold">${c.difficulty}</span>
          </div>
          <h4 class="font-display font-extrabold text-base text-white">${escapeHtml(c.name)}</h4>
          <p class="text-xs text-dkoder-purpleSoft mt-1 mb-4 leading-relaxed">${escapeHtml(c.description)}</p>
          <div class="flex items-center justify-between pt-3 border-t border-white/10">
            <span class="text-[11px] text-dkoder-purpleSoft"><i class="fa-solid fa-users mr-1"></i>${c.participants_count} Registered</span>
            <button onclick="DKoderApp.registerForArena('${c.slug}')" class="btn-dk-yellow px-4 py-1.5 rounded-full text-xs font-extrabold">
              ${c.is_registered ? 'Enter Arena Room →' : 'Register Now (Free)'}
            </button>
          </div>
        </div>
      `).join('');
    }
    loadArenaPodium('national-placement-sprint-14');
  }

  async function registerForArena(slug) {
    const res = await DKoderAPI.registerCompetition(slug);
    if (res && res.success) {
      showToast(res.message, 'success');
      loadArena();
    }
  }

  async function loadArenaPodium(slug) {
    const tableEl = document.getElementById('arena-podium-rows');
    const data = await DKoderAPI.getArenaLeaderboard(slug);
    if (tableEl && data.leaderboard) {
      tableEl.innerHTML = data.leaderboard.map(e => `
        <tr class="border-b border-white/5 hover:bg-white/5 text-xs">
          <td class="py-2.5 px-3 font-extrabold ${e.rank === 1 ? 'text-dkoder-yellow text-sm' : 'text-white'}">#${e.rank}</td>
          <td class="py-2.5 px-3 font-bold text-white">${escapeHtml(e.full_name)}</td>
          <td class="py-2.5 px-3 text-dkoder-purpleSoft">${escapeHtml(e.college)}</td>
          <td class="py-2.5 px-3 font-mono font-bold text-dkoder-yellow">${e.score} pts</td>
          <td class="py-2.5 px-3 font-mono text-emerald-400 font-bold">${e.problems_solved} Solved</td>
          <td class="py-2.5 px-3 font-mono text-dkoder-purpleSoft">${e.penalty}</td>
        </tr>
      `).join('');
    }
  }

  // ---------------------------------------------------------------------------
  // 7. FEATURE SEVEN: SKILL GAP ANALYZER
  // ---------------------------------------------------------------------------
  async function loadSkills() {
    const data = await DKoderAPI.getSkillsAnalysis();
    if (!data) return;

    renderSkillCategoryGroup('skills-needs-attention-container', data.needs_attention, 'border-rose-500/40 bg-rose-950/20');
    renderSkillCategoryGroup('skills-developing-container', data.developing, 'border-amber-500/40 bg-amber-950/20');
    renderSkillCategoryGroup('skills-proficient-container', data.proficient, 'border-emerald-500/40 bg-emerald-950/20');
  }

  function renderSkillCategoryGroup(elementId, items, borderClass) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (!items || items.length === 0) {
      el.innerHTML = `<p class="text-xs text-dkoder-purpleSoft italic">No skills currently in this tier.</p>`;
      return;
    }
    el.innerHTML = items.map(s => `
      <div class="p-4 rounded-xl border ${borderClass} mb-3">
        <div class="flex items-center justify-between mb-1.5">
          <h5 class="text-xs font-bold text-white">${escapeHtml(s.name)}</h5>
          <span class="text-xs font-mono font-extrabold text-dkoder-yellow">${s.proficiency}%</span>
        </div>
        <div class="w-full h-2 rounded-full bg-white/10 overflow-hidden mb-2">
          <div class="h-full bg-dkoder-yellow rounded-full transition-all duration-500" style="width: ${s.proficiency}%"></div>
        </div>
        <div class="flex items-center justify-between text-[11px] text-dkoder-purpleSoft">
          <span>${s.attempts} Assessments &bull; Trend: ${s.trend.toUpperCase()}</span>
          <button onclick="DKoderApp.addSkillToRoadmap('${escapeHtml(s.name)}')" class="text-dkoder-yellow hover:underline font-bold">+ Add to Roadmap</button>
        </div>
      </div>
    `).join('');
  }

  function addSkillToRoadmap(skillName) {
    showToast(`Added target tasks for "${skillName}" to your Placement Roadmap!`, 'success');
  }

  // ---------------------------------------------------------------------------
  // 8. FEATURE EIGHT: COMMUNITY & LEADERBOARDS
  // ---------------------------------------------------------------------------
  async function loadCommunity() {
    const feed = document.getElementById('community-posts-feed');
    const data = await DKoderAPI.getCommunityPosts();
    if (feed && data.posts) {
      feed.innerHTML = data.posts.map(p => `
        <div class="p-5 rounded-2xl bg-[#1E0D47]/80 border-2 border-white/10 mb-4 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-2">
              <span class="w-7 h-7 rounded-full bg-dkoder-yellow text-dkoder-dark font-black flex items-center justify-center text-xs">
                ${p.author.full_name ? p.author.full_name.charAt(0) : 'U'}
              </span>
              <div>
                <span class="text-xs font-bold text-white">${escapeHtml(p.author.full_name)}</span>
                <span class="text-[10px] text-dkoder-purpleSoft block">${escapeHtml(p.author.college)}</span>
              </div>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-dkoder-yellow/20 text-dkoder-yellow font-space uppercase">${escapeHtml(p.tag)}</span>
          </div>
          <h4 class="font-display font-extrabold text-sm text-white mb-1">${escapeHtml(p.title)}</h4>
          <p class="text-xs text-dkoder-purpleSoft leading-relaxed">${escapeHtml(p.content)}</p>
          <div class="flex items-center justify-between pt-3 mt-3 border-t border-white/10">
            <div class="flex items-center space-x-4 text-xs font-bold">
              <button onclick="DKoderApp.reactCommunityPost(${p.id}, this)" class="text-rose-400 hover:scale-110 transition-transform flex items-center space-x-1">
                <i class="fa-solid fa-heart"></i>
                <span id="post-likes-${p.id}">${p.likes_count}</span>
              </button>
              <span class="text-dkoder-purpleSoft"><i class="fa-regular fa-comment mr-1"></i>${p.comments_count}</span>
            </div>
            <button onclick="DKoderApp.openReportModal(${p.id})" class="text-[11px] text-dkoder-purpleSoft hover:text-rose-400 transition-colors">
              <i class="fa-regular fa-flag mr-1"></i> Report
            </button>
          </div>
        </div>
      `).join('');
    }
  }

  async function reactCommunityPost(postId, btn) {
    const res = await DKoderAPI.reactPost(postId);
    if (res && res.success) {
      const countEl = document.getElementById(`post-likes-${postId}`);
      if (countEl) countEl.innerText = res.new_likes;
    }
  }

  function openCreatePostModal() {
    openModal('community-post-modal');
  }

  async function submitCommunityPost(e) {
    e.preventDefault();
    const form = e.target;
    await DKoderAPI.createPost({
      title: form.title.value,
      content: form.content.value,
      tag: form.tag.value
    });
    closeModal('community-post-modal');
    showToast('Post shared with the DKoder Community!', 'success');
    loadCommunity();
  }

  function openReportModal(postId) {
    const input = document.getElementById('report-post-id');
    if (input) input.value = postId;
    openModal('community-report-modal');
  }

  async function submitReportPost(e) {
    e.preventDefault();
    const form = e.target;
    await DKoderAPI.reportPost(form.post_id.value, form.reason.value);
    closeModal('community-report-modal');
    showToast('Report submitted for moderator review.', 'info');
  }

  // ---------------------------------------------------------------------------
  // 9. FEATURE NINE: CAREER PROFILE (RESUME & PORTFOLIO)
  // ---------------------------------------------------------------------------
  async function loadCareerProfile() {
    const data = await DKoderAPI.getResume();
    if (data && data.resume) {
      renderResumePreview(data.resume);
      populateResumeForm(data.resume);
    }
  }

  function populateResumeForm(r) {
    const form = document.getElementById('resume-editor-form');
    if (!form) return;
    if (form.full_name) form.full_name.value = r.full_name || '';
    if (form.email) form.email.value = r.email || '';
    if (form.phone) form.phone.value = r.phone || '';
    if (form.location) form.location.value = r.location || '';
    if (form.summary) form.summary.value = r.summary || '';
    if (form.github_url) form.github_url.value = r.github_url || '';
    if (form.linkedin_url) form.linkedin_url.value = r.linkedin_url || '';
  }

  function renderResumePreview(r) {
    const container = document.getElementById('resume-preview-container');
    if (!container) return;

    container.innerHTML = `
      <div class="bg-white text-gray-900 p-8 rounded-xl shadow-lg font-sans text-xs max-w-2xl mx-auto leading-relaxed border">
        <!-- Header -->
        <div class="border-b-2 border-[#1E0D47] pb-4 mb-4 text-center">
          <h2 class="text-2xl font-black text-[#1E0D47] tracking-tight uppercase">${escapeHtml(r.full_name || 'Alex Rivera')}</h2>
          <p class="text-[11px] text-gray-600 font-medium mt-1">
            ${escapeHtml(r.email || '')} &bull; ${escapeHtml(r.phone || '')} &bull; ${escapeHtml(r.location || '')}
          </p>
          <p class="text-[10px] text-[#1E0D47] font-bold mt-0.5">
            ${escapeHtml(r.github_url || '')} &bull; ${escapeHtml(r.linkedin_url || '')}
          </p>
        </div>

        <!-- Summary -->
        <div class="mb-4">
          <h3 class="text-xs font-black uppercase text-[#1E0D47] border-b border-gray-300 pb-1 mb-1">Professional Summary</h3>
          <p class="text-gray-700 leading-normal text-[11px]">${escapeHtml(r.summary || '')}</p>
        </div>

        <!-- Education -->
        <div class="mb-4">
          <h3 class="text-xs font-black uppercase text-[#1E0D47] border-b border-gray-300 pb-1 mb-1.5">Education</h3>
          ${(r.education || []).map(e => `
            <div class="flex justify-between items-start mb-1 text-[11px]">
              <div>
                <span class="font-bold text-gray-900">${escapeHtml(e.degree)}</span>
                <p class="text-gray-600 text-[10px]">${escapeHtml(e.institution)}</p>
              </div>
              <span class="text-gray-500 font-mono text-[10px]">${escapeHtml(e.year)}</span>
            </div>
          `).join('')}
        </div>

        <!-- Technical Skills -->
        <div class="mb-4">
          <h3 class="text-xs font-black uppercase text-[#1E0D47] border-b border-gray-300 pb-1 mb-1.5">Technical Skills</h3>
          <p class="text-gray-800 text-[11px]">
            <strong class="text-gray-900">Languages & Tools:</strong> ${(r.skills || []).join(', ')}
          </p>
        </div>

        <!-- Projects -->
        <div class="mb-4">
          <h3 class="text-xs font-black uppercase text-[#1E0D47] border-b border-gray-300 pb-1 mb-1.5">Key Projects</h3>
          ${(r.projects || []).map(p => `
            <div class="mb-2 text-[11px]">
              <div class="flex justify-between font-bold">
                <span class="text-gray-900">${escapeHtml(p.name)}</span>
                <span class="text-gray-500 text-[10px] font-mono">${escapeHtml(p.tech)}</span>
              </div>
              <ul class="list-disc list-inside text-gray-700 text-[10px] mt-0.5">
                ${(p.bullets || []).map(b => `<li>${escapeHtml(b)}</li>`).join('')}
              </ul>
            </div>
          `).join('')}
        </div>

        <!-- Certifications -->
        <div>
          <h3 class="text-xs font-black uppercase text-[#1E0D47] border-b border-gray-300 pb-1 mb-1">Certifications & Achievements</h3>
          <p class="text-gray-700 text-[10px]">${(r.certifications || []).join(' &bull; ')}</p>
        </div>
      </div>
    `;
  }

  async function saveResumeChanges(e) {
    e.preventDefault();
    const form = e.target;
    const payload = {
      full_name: form.full_name.value,
      email: form.email.value,
      phone: form.phone.value,
      location: form.location.value,
      summary: form.summary.value,
      github_url: form.github_url.value,
      linkedin_url: form.linkedin_url.value
    };
    await DKoderAPI.saveResume(payload);
    showToast('Resume saved successfully!', 'success');
    loadCareerProfile();
  }

  function printResume() {
    window.print();
  }

  // ---------------------------------------------------------------------------
  // 10. FEATURE TEN: ADMIN DASHBOARD
  // ---------------------------------------------------------------------------
  async function loadAdminDashboard() {
    if (!currentUser || currentUser.role !== 'admin') {
      const notice = document.getElementById('admin-unauth-notice');
      const content = document.getElementById('admin-dashboard-content');
      if (notice) notice.classList.remove('hidden');
      if (content) content.classList.add('hidden');
      return;
    }

    const notice = document.getElementById('admin-unauth-notice');
    const content = document.getElementById('admin-dashboard-content');
    if (notice) notice.classList.add('hidden');
    if (content) content.classList.remove('hidden');

    // Load admin stats
    const statsData = await DKoderAPI.getAdminStats();
    if (statsData && statsData.stats) {
      const s = statsData.stats;
      document.getElementById('ad-stat-students').innerText = s.total_students;
      document.getElementById('ad-stat-problems').innerText = s.total_problems;
      document.getElementById('ad-stat-submissions').innerText = s.total_submissions;
      document.getElementById('ad-stat-passrate').innerText = `${s.pass_rate}%`;
      document.getElementById('ad-stat-reports').innerText = s.pending_reports;
    }

    loadAdminUsersList();
    loadAdminModerationQueue();
    loadAdminAuditLogs();
  }

  async function loadAdminUsersList() {
    const listEl = document.getElementById('admin-users-table');
    const data = await DKoderAPI.getAdminUsers();
    if (listEl && data.users) {
      listEl.innerHTML = data.users.map(u => `
        <tr class="border-b border-white/5 hover:bg-white/5 text-xs">
          <td class="py-2.5 px-3 font-bold text-white">${escapeHtml(u.full_name)}</td>
          <td class="py-2.5 px-3 text-dkoder-purpleSoft">${escapeHtml(u.email)}</td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase ${u.role === 'admin' ? 'bg-rose-500 text-white' : 'bg-dkoder-yellow text-dkoder-dark'}">
              ${u.role}
            </span>
          </td>
          <td class="py-2.5 px-3 text-dkoder-purpleSoft">${escapeHtml(u.college)}</td>
          <td class="py-2.5 px-3">
            <button onclick="DKoderApp.toggleUserStatus(${u.id})" class="px-2.5 py-1 rounded text-[11px] font-bold ${u.is_active ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">
              ${u.is_active ? 'Active' : 'Suspended'}
            </button>
          </td>
        </tr>
      `).join('');
    }
  }

  async function toggleUserStatus(userId) {
    const res = await DKoderAPI.toggleUserStatus(userId);
    if (res && res.success) {
      showToast(`User status updated to ${res.is_active ? 'Active' : 'Suspended'}`, 'info');
      loadAdminUsersList();
    }
  }

  async function loadAdminModerationQueue() {
    const listEl = document.getElementById('admin-moderation-list');
    const data = await DKoderAPI.getModerationQueue();
    if (listEl && data.reports) {
      if (data.reports.length === 0) {
        listEl.innerHTML = `<p class="text-xs text-dkoder-purpleSoft italic">No pending moderation reports in queue.</p>`;
        return;
      }
      listEl.innerHTML = data.reports.map(r => `
        <div class="p-4 rounded-xl bg-white/5 border border-white/10 mb-3 flex items-start justify-between">
          <div>
            <h5 class="text-xs font-bold text-white">Report on: "${escapeHtml(r.post_title)}"</h5>
            <p class="text-[11px] text-rose-400 mt-1">Reason: ${escapeHtml(r.reason)}</p>
            <p class="text-[10px] text-dkoder-purpleSoft">Filed by ${escapeHtml(r.reporter)} on ${r.created_at}</p>
          </div>
          <div class="flex items-center space-x-2">
            <button onclick="DKoderApp.handleModerationAction(${r.id}, 'dismiss')" class="px-3 py-1 bg-white/10 hover:bg-white/20 text-white rounded text-xs">Dismiss</button>
            <button onclick="DKoderApp.handleModerationAction(${r.id}, 'delete_post')" class="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-bold">Remove Post</button>
          </div>
        </div>
      `).join('');
    }
  }

  async function handleModerationAction(reportId, action) {
    await DKoderAPI.actionModeration(reportId, action);
    showToast(`Moderation action "${action}" completed.`, 'info');
    loadAdminModerationQueue();
  }

  async function loadAdminAuditLogs() {
    const listEl = document.getElementById('admin-audit-logs-list');
    const data = await DKoderAPI.getAuditLogs();
    if (listEl && data.logs) {
      listEl.innerHTML = data.logs.map(l => `
        <tr class="border-b border-white/5 hover:bg-white/5 text-[11px] font-mono">
          <td class="py-2 px-3 text-dkoder-purpleSoft">${l.timestamp}</td>
          <td class="py-2 px-3 font-bold text-dkoder-yellow">${escapeHtml(l.actor)}</td>
          <td class="py-2 px-3 text-white">${escapeHtml(l.action)}</td>
          <td class="py-2 px-3 text-dkoder-purpleSoft truncate max-w-xs">${escapeHtml(l.details)}</td>
        </tr>
      `).join('');
    }
  }

  function openNewQuestionModal() {
    openModal('admin-question-modal');
  }

  async function submitAdminQuestion(e) {
    e.preventDefault();
    const form = e.target;
    await DKoderAPI.saveQuestion({
      title: form.title.value,
      difficulty: form.difficulty.value,
      category: form.category.value,
      company_tags: form.company_tags.value,
      description: form.description.value,
      sample_input: form.sample_input.value,
      sample_output: form.sample_output.value,
      points: form.points.value
    });
    closeModal('admin-question-modal');
    showToast('New Coding Question published to DKoder CodeLab!', 'success');
    loadAdminDashboard();
  }

  // ---------------------------------------------------------------------------
  // Modal & Toast Utilities
  // ---------------------------------------------------------------------------
  function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
  }

  function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  }

  function openAuthModal() {
    openModal('auth-modal');
  }

  async function openNotificationDrawer() {
    openModal('notifications-modal');
    const listEl = document.getElementById('notifications-drawer-list');
    const data = await DKoderAPI.getNotifications();
    if (listEl && data.notifications) {
      listEl.innerHTML = data.notifications.map(n => `
        <div class="p-3 rounded-xl bg-white/5 border border-white/10 mb-2.5">
          <h5 class="text-xs font-bold text-white flex items-center justify-between">
            <span>${escapeHtml(n.title)}</span>
            <span class="text-[10px] text-dkoder-purpleSoft">${n.created_at}</span>
          </h5>
          <p class="text-[11px] text-dkoder-purpleSoft mt-1 leading-normal">${escapeHtml(n.message)}</p>
        </div>
      `).join('');
    }
    await DKoderAPI.markAllNotificationsRead();
  }

  function showToast(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-6 right-6 z-50 px-4 py-3 rounded-2xl text-xs font-bold shadow-brutal flex items-center space-x-2 transition-all transform translate-y-0 ${type === 'success' ? 'bg-emerald-400 text-dkoder-dark' : (type === 'error' ? 'bg-rose-500 text-white' : 'bg-dkoder-yellow text-dkoder-dark')}`;
    toast.innerHTML = `<i class="fa-solid ${type === 'success' ? 'fa-check' : 'fa-circle-info'}"></i><span>${escapeHtml(msg)}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function scrollToCollegeMOU(event) {
    if (event) event.preventDefault();
    closeWorkspace();
    setTimeout(() => {
      const mouSec = document.getElementById('college-mou');
      if (mouSec) {
        mouSec.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  }

  async function runInteractiveDemo(featureKey) {
    showToast(`Launching Interactive Demo: ${featureKey.toUpperCase()}...`, 'info');
    openWorkspace(featureKey);

    // Feature-specific demo actions
    if (featureKey === 'ai-mentor') {
      const inputEl = document.getElementById('ai-message-input');
      if (inputEl) {
        inputEl.value = 'How does QuickSort work and what is its average vs worst-case complexity?';
        setTimeout(() => sendAIMessage(), 400);
      }
    } else if (featureKey === 'codelab') {
      setTimeout(() => {
        selectCodeLabProblem(1);
        setTimeout(() => {
          runCodeLabCode();
          setTimeout(() => {
            submitCodeLabSolution();
          }, 1500);
        }, 800);
      }, 300);
    } else if (featureKey === 'interview') {
      setTimeout(() => {
        startMockInterview();
        setTimeout(() => {
          const ansEl = document.getElementById('interview-answer-input');
          if (ansEl) {
            ansEl.value = 'Binary search trees offer O(log N) lookup and insertion by maintaining left < root < right ordering. When stored on disk, B-Trees are preferred over BSTs because B-Trees have a higher branching factor, significantly reducing disk I/O seek operations.';
            submitInterviewAnswer();
          }
        }, 1200);
      }, 500);
    } else if (featureKey === 'arena') {
      setTimeout(() => {
        showToast('Viewing Live Arena: Zoho Premier CodeFest 2026 is LIVE!', 'info');
        const list = document.getElementById('arena-competitions-list');
        if (list) list.scrollIntoView({ behavior: 'smooth' });
      }, 400);
    } else if (featureKey === 'roadmap') {
      setTimeout(() => {
        toggleRoadmapTask(203);
      }, 600);
    } else if (featureKey === 'skills') {
      setTimeout(() => {
        showToast('Skill Gap Analyzer evaluated 14 competencies.', 'info');
      }, 400);
    } else if (featureKey === 'community') {
      setTimeout(() => {
        reactCommunityPost(1);
      }, 600);
    } else if (featureKey === 'admin') {
      await quickSwitchUser('admin');
      setTimeout(() => {
        showToast('Admin Command Center unlocked with full privileges.', 'success');
      }, 400);
    }
  }

  return {
    init,
    openWorkspace,
    closeWorkspace,
    loadModule,
    quickSwitchUser,
    openAuthModal,
    openNotificationDrawer,
    closeModal,
    showToast,
    scrollToCollegeMOU,
    runInteractiveDemo,

    // AI Mentor
    selectAIConversation,
    startNewAIConversation,
    sendAIMessage,
    handlePromptChip,
    copyCode,
    clearAIChat,

    // CodeLab
    selectCodeLabProblem,
    changeCodeLabLanguage,
    runCodeLabCode,
    submitCodeLabSolution,

    // Roadmap
    toggleRoadmapTask,
    openRoadmapModal,
    submitGenerateRoadmap,

    // Interview
    startMockInterview,
    submitInterviewAnswer,
    finishMockInterview,
    toggleVoiceRecording,

    // Arena
    registerForArena,

    // Skills
    addSkillToRoadmap,

    // Community
    reactCommunityPost,
    openCreatePostModal,
    submitCommunityPost,
    openReportModal,
    submitReportPost,

    // Career
    saveResumeChanges,
    printResume,

    // Admin
    toggleUserStatus,
    handleModerationAction,
    openNewQuestionModal,
    submitAdminQuestion
  };
})();

// Auto-run on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  DKoderApp.init();
});

