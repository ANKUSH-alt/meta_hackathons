document.addEventListener('DOMContentLoaded', () => {
    let currentTaskId = 'easy';
    let currentReward = 0.0;

    const taskBtns = document.querySelectorAll('.task-btn');
    const resetBtn = document.getElementById('reset-btn');
    const clearLogBtn = document.getElementById('clear-log');
    const resourceDisplay = document.getElementById('resource-display');
    const actionLog = document.getElementById('action-log');
    const manualInput = document.getElementById('manual-input');
    const runBtn = document.getElementById('run-action');
    const currentTaskDisplay = document.getElementById('current-task-display');
    const currentRewardDisplay = document.getElementById('current-reward');
    const envStatus = document.getElementById('env-status');
    const resourceCount = document.getElementById('resource-count');

    // --- Core API Functions ---

    async function resetEnv(taskId) {
        log(`Resetting environment for task: ${taskId}...`, 'system');
        envStatus.textContent = 'Resetting...';
        envStatus.className = 'status-badge';
        currentReward = 0.0;
        currentRewardDisplay.textContent = '0.00';
        try {
            const response = await fetch('/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: taskId })
            });
            const data = await response.json();
            const obs = data.observation || data;
            updateUIFromObs(obs, false, data);
            log(`Environment ready. ${obs.info || ''}`, 'system');
            showToast(`✅ Task "${taskId}" loaded`);
        } catch (err) {
            log(`Error resetting: ${err.message}`, 'error');
            envStatus.textContent = 'Error';
        }
    }

    async function stepEnv(actionObj) {
        log(`▶ Executing: ${formatAction(actionObj)}`, 'action');
        envStatus.textContent = 'Processing...';
        try {
            const response = await fetch('/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionObj })
            });
            const data = await response.json();
            const obs = data.observation || data;
            const reward = data.reward !== undefined ? data.reward : (obs.reward || 0);
            const done = data.done !== undefined ? data.done : (obs.done || false);
            updateUIFromObs(obs, true, data);

            if (obs.status) {
                log(`Response: ${obs.status}`, 'system');
            }
            if (obs.info) {
                log(`ℹ️ ${obs.info}`, 'system');
            }
            if (reward > 0) {
                log(`🏆 Reward: +${reward.toFixed(2)}`, 'reward');
            }
            if (done) {
                log(`🎯 Task Completed!`, 'reward');
                showToast('🎯 Task Completed Successfully!');
            }
        } catch (err) {
            log(`❌ Execution failed: ${err.message}`, 'error');
            envStatus.textContent = 'Error';
        }
    }

    // --- UI Update ---

    function updateUIFromObs(obs, isStep, data) {
        const reward = data ? (data.reward !== undefined ? data.reward : 0) : 0;
        const done = data ? (data.done !== undefined ? data.done : false) : false;

        // Update reward
        if (isStep && reward !== undefined) {
            currentReward += reward;
            currentRewardDisplay.textContent = currentReward.toFixed(2);
            if (currentReward > 0) {
                currentRewardDisplay.classList.add('reward-positive');
            }
        }

        // Update status badge
        if (done) {
            envStatus.textContent = '✓ Completed';
            envStatus.className = 'status-badge completed';
        } else {
            envStatus.textContent = 'Active';
            envStatus.className = 'status-badge active';
        }

        // Update Resources
        const resources = obs.resources || [];
        if (resources.length > 0) {
            resourceCount.textContent = `${resources.length} Resources`;
            resourceDisplay.innerHTML = resources.map(r => createResourceCard(r)).join('');
            // Animate cards in
            document.querySelectorAll('.resource-card').forEach((card, i) => {
                card.style.animationDelay = `${i * 0.08}s`;
                card.classList.add('fade-in');
            });
        }

        // Update Details (for describe actions)
        if (obs.details) {
            const detail = obs.details;
            resourceCount.textContent = '1 Resource (Detail)';
            resourceDisplay.innerHTML = createDetailCard(detail);
        }

        // Update Logs (for log actions)
        if (obs.logs && obs.logs.length > 0) {
            obs.logs.forEach(entry => {
                const color = entry.action === 'DeleteStorage' ? 'error' : 'system';
                log(`  [${entry.timestamp}] ${entry.user} → ${entry.action} (IP: ${entry.ip})`, color);
            });
        }

        actionLog.scrollTop = actionLog.scrollHeight;
    }

    function createResourceCard(r) {
        const isVulnerable = r.public === true || hasOpenPorts(r);
        const type = detectResourceType(r);
        const id = r.id || 'unknown';

        let tagsHtml = '';
        if (r.tags) {
            tagsHtml = Object.entries(r.tags).map(([k, v]) =>
                `<span class="tag ${k === 'env' && v === 'prod' ? 'env-prod' : ''}">${k}: ${v}</span>`
            ).join('');
        }
        if (r.public) {
            tagsHtml += '<span class="tag status-public">⚠ PUBLIC</span>';
        }
        if (r.state) {
            tagsHtml += `<span class="tag">${r.state}</span>`;
        }
        if (r.region) {
            tagsHtml += `<span class="tag">${r.region}</span>`;
        }

        // Security groups info for EC2
        let sgHtml = '';
        if (r.security_groups) {
            const ports = r.security_groups.flatMap(sg => sg.rules.map(rule => rule.port));
            const dangerPorts = [3389, 445, 23]; // RDP, SMB, Telnet
            const openDangerPorts = ports.filter(p => dangerPorts.includes(p));
            if (openDangerPorts.length > 0) {
                sgHtml = `<div class="sg-warning">🔓 Dangerous ports open: ${openDangerPorts.join(', ')}</div>`;
            } else {
                sgHtml = `<div class="sg-info">🔒 Ports: ${ports.join(', ')}</div>`;
            }
        }

        return `
            <div class="resource-card ${isVulnerable ? 'vulnerable' : 'secure'}">
                <div class="card-status-dot ${isVulnerable ? 'dot-danger' : 'dot-safe'}"></div>
                <span class="resource-type">${type}</span>
                <span class="resource-id">${id}</span>
                ${sgHtml}
                <div class="resource-tags">${tagsHtml}</div>
            </div>
        `;
    }

    function createDetailCard(detail) {
        return `
            <div class="resource-card detail-card">
                <span class="resource-type">${detectResourceType(detail)}</span>
                <span class="resource-id">${detail.id}</span>
                <pre class="detail-json">${JSON.stringify(detail, null, 2)}</pre>
            </div>
        `;
    }

    function detectResourceType(r) {
        if (r.id && r.id.startsWith('i-')) return 'EC2 Instance';
        if (r.id && r.id.includes('prod-')) return 'S3 Bucket';
        if (r.id && r.id.includes('dev-')) return 'S3 Bucket';
        if (r.type) return r.type.toUpperCase();
        return 'Resource';
    }

    function hasOpenPorts(r) {
        if (!r.security_groups) return false;
        return r.security_groups.some(sg =>
            sg.rules.some(rule => rule.port === 3389 && rule.cidr === '0.0.0.0/0')
        );
    }

    function formatAction(obj) {
        let str = obj.action;
        if (obj.resource_type) str += ` ${obj.resource_type}`;
        if (obj.resource_id) str += ` → ${obj.resource_id}`;
        if (obj.answer) str += ` (answer: ${obj.answer})`;
        return str;
    }

    // --- Logging ---

    function log(msg, type = 'system') {
        const div = document.createElement('div');
        div.className = `log-entry ${type}`;
        const time = new Date().toLocaleTimeString([], {
            hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
        div.textContent = `[${time}] ${msg}`;
        actionLog.appendChild(div);
        actionLog.scrollTop = actionLog.scrollHeight;
    }

    function showToast(msg) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.remove('hidden');
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            toast.classList.add('hidden');
        }, 3000);
    }

    // --- Manual Action Parser ---
    // Supports: list s3, list ec2, describe <id>, logs <name>, submit <answer>
    function parseManualAction(input) {
        const parts = input.trim().split(/\s+/);
        const cmd = parts[0]?.toLowerCase();

        switch (cmd) {
            case 'list':
                return { action: 'list', resource_type: parts[1] || 's3' };
            case 'describe':
                return { action: 'describe', resource_id: parts.slice(1).join(' ') };
            case 'logs':
                return { action: 'logs', resource_id: parts.slice(1).join(' ') || 'auth-logs' };
            case 'submit':
                return { action: 'submit', answer: parts.slice(1).join(' ') };
            case 'modify':
                // For modify, just pass raw — advanced users can use JSON
                return { action: 'modify', resource_id: parts[1], patch: {} };
            default:
                return { action: cmd, resource_type: parts[1] || '' };
        }
    }

    // --- Event Listeners ---

    taskBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            taskBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTaskId = btn.dataset.task;
            currentTaskDisplay.textContent = btn.querySelector('.task-name').textContent;
            resourceDisplay.innerHTML = '<div class="empty-state">No resources discovered. Run "list" to see resources.</div>';
            resourceCount.textContent = '0 Resources';
            resetEnv(currentTaskId);
        });
    });

    resetBtn.addEventListener('click', () => {
        resourceDisplay.innerHTML = '<div class="empty-state">No resources discovered. Run "list" to see resources.</div>';
        resourceCount.textContent = '0 Resources';
        resetEnv(currentTaskId);
    });

    clearLogBtn.addEventListener('click', () => {
        actionLog.innerHTML = '';
        log('Log cleared.', 'system');
    });

    runBtn.addEventListener('click', () => {
        const val = manualInput.value.trim();
        if (!val) return;
        const actionObj = parseManualAction(val);
        stepEnv(actionObj);
        manualInput.value = '';
    });

    manualInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            runBtn.click();
        }
    });

    // --- Initial Load ---
    currentTaskDisplay.textContent = 'S3 Public Audit';
    resetEnv('easy');
});
