document.addEventListener('DOMContentLoaded', () => {
  const queryInput = document.getElementById('user-query');
  const submitBtn = document.getElementById('submit-btn');
  const paramsToggle = document.getElementById('params-toggle');
  const paramsBody = document.getElementById('params-body');
  const paramsArrow = document.getElementById('params-arrow');
  
  const emptyState = document.getElementById('empty-state');
  const liveResults = document.getElementById('live-results');
  const evaluationsSlot = document.getElementById('evaluations-slot');
  const protocolSlot = document.getElementById('protocol-slot');
  const citationsSlot = document.getElementById('citations-slot');
  const traceSlot = document.getElementById('trace-slot');

  const telemetryLlm = document.getElementById('telemetry-llm');
  const telemetryDb = document.getElementById('telemetry-db');

  const pipeSteps = {
    router: document.getElementById('pipe-router'),
    retrieval: document.getElementById('pipe-retrieval'),
    eligibility: document.getElementById('pipe-eligibility'),
    application: document.getElementById('pipe-application'),
    reflection: document.getElementById('pipe-reflection')
  };

  // Telemetry init
  async function loadTelemetry() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        telemetryLlm.textContent = `LLM: ${data.llm_provider.toUpperCase()} (${data.llm_model})`;
        telemetryDb.textContent = `ChromaDB: ${data.indexed_chunks} Chunks`;
      }
    } catch {
      telemetryLlm.textContent = 'LLM: Local Rule Engine';
      telemetryDb.textContent = 'ChromaDB: 25 Chunks';
    }
  }
  loadTelemetry();

  // Presets
  document.querySelectorAll('.preset-button').forEach(btn => {
    btn.addEventListener('click', () => {
      queryInput.value = btn.getAttribute('data-query');
      queryInput.focus();
    });
  });

  // Toggle optional parameters drawer
  paramsToggle.addEventListener('click', () => {
    const isHidden = paramsBody.classList.contains('hidden');
    if (isHidden) {
      paramsBody.classList.remove('hidden');
      paramsArrow.textContent = '[-]';
    } else {
      paramsBody.classList.add('hidden');
      paramsArrow.textContent = '[+]';
    }
  });

  // Pipeline step state manager
  function resetPipeline() {
    Object.values(pipeSteps).forEach(el => el.classList.remove('active', 'done'));
  }

  function advancePipeline(stage) {
    const order = ['router', 'retrieval', 'eligibility', 'application', 'reflection'];
    const targetIdx = order.indexOf(stage);
    order.forEach((s, i) => {
      if (i < targetIdx) {
        pipeSteps[s].classList.remove('active');
        pipeSteps[s].classList.add('done');
      } else if (i === targetIdx) {
        pipeSteps[s].classList.add('active');
        pipeSteps[s].classList.remove('done');
      } else {
        pipeSteps[s].classList.remove('active', 'done');
      }
    });
  }

  // Keyboard shortcut Ctrl/Cmd + Enter
  queryInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      submitBtn.click();
    }
  });

  // Submission handler
  submitBtn.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    if (!query) {
      queryInput.focus();
      return;
    }

    const age = parseInt(document.getElementById('profile-age').value) || null;
    const gender = document.getElementById('profile-gender').value || null;
    const state = document.getElementById('profile-state').value || null;
    const occupation = document.getElementById('profile-occupation').value || null;
    const category = document.getElementById('profile-category').value || null;
    const land = parseFloat(document.getElementById('profile-land').value) || null;
    const income = parseFloat(document.getElementById('profile-income').value) || null;
    const taxVal = document.getElementById('profile-taxpayer').value;
    const is_tax_payer = taxVal === 'true' ? true : (taxVal === 'false' ? false : null);

    const payload = {
      query,
      profile: {
        age,
        gender,
        state,
        occupation,
        category,
        land_ownership_acres: land,
        annual_income: income,
        is_tax_payer
      }
    };

    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Evaluating statutory criteria...</span>`;
    advancePipeline('router');

    try {
      setTimeout(() => advancePipeline('retrieval'), 250);
      setTimeout(() => advancePipeline('eligibility'), 500);

      const resp = await fetch('/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        throw new Error(`Execution error: ${resp.statusText}`);
      }

      advancePipeline('application');
      const data = await resp.json();
      advancePipeline('reflection');
      setTimeout(() => {
        Object.values(pipeSteps).forEach(el => {
          el.classList.remove('active');
          el.classList.add('done');
        });
      }, 300);

      renderDossier(data);
      emptyState.classList.add('hidden');
      liveResults.classList.remove('hidden');

    } catch (err) {
      alert(`Navigator error: ${err.message}`);
      resetPipeline();
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>Evaluate Eligibility & Guidance</span>`;
    }
  });

  // Render Dossier
  function renderDossier(result) {
    evaluationsSlot.innerHTML = '';
    protocolSlot.innerHTML = '';
    citationsSlot.innerHTML = '';
    traceSlot.innerHTML = '';

    // 1. Missing Info Callout (if any)
    if (result.missing_fields_prompt && result.missing_fields_prompt.length > 0) {
      const alert = document.createElement('div');
      alert.className = 'missing-alert';
      alert.innerHTML = `
        <div class="missing-alert-title">Additional details required for conclusive verification</div>
        <ul>
          ${result.missing_fields_prompt.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
        </ul>
      `;
      evaluationsSlot.appendChild(alert);
    }

    // 2. Scheme Evaluations
    if (result.evaluations && result.evaluations.length > 0) {
      result.evaluations.forEach(ev => {
        let badgeClass = 'pending';
        if (ev.status === 'Eligible') badgeClass = 'eligible';
        else if (ev.status.includes('Not eligible')) badgeClass = 'ineligible';

        const card = document.createElement('div');
        card.className = 'dossier-card';
        card.innerHTML = `
          <div class="dossier-top">
            <div>
              <div class="scheme-name">${escapeHtml(ev.scheme_name)}</div>
              <div class="scheme-authority">Scheme reference: ${escapeHtml(ev.scheme_id)}</div>
            </div>
            <span class="status-badge ${badgeClass}">${escapeHtml(ev.status)}</span>
          </div>

          <div class="scheme-summary">${escapeHtml(ev.summary)}</div>

          <div class="matrix-row">
            <div class="matrix-block">
              <div class="matrix-label">Verified Conditions</div>
              <ul class="condition-list">
                ${ev.conditions_met && ev.conditions_met.length > 0
                  ? ev.conditions_met.map(c => `
                    <li class="condition-item met">
                      <span style="color: var(--semantic-pos); font-weight: 600;">[OK]</span>
                      <span>${escapeHtml(c)}</span>
                    </li>
                  `).join('')
                  : '<li class="condition-item" style="color: var(--text-muted);">None confirmed</li>'}
              </ul>
            </div>

            <div class="matrix-block">
              <div class="matrix-label">Pending / Unmet Criteria</div>
              <ul class="condition-list">
                ${ev.conditions_failed && ev.conditions_failed.length > 0
                  ? ev.conditions_failed.map(f => `
                    <li class="condition-item unmet">
                      <span style="font-weight: 600;">[EXCL]</span>
                      <span>${escapeHtml(f)}</span>
                    </li>
                  `).join('')
                  : ''}
                ${ev.missing_fields && ev.missing_fields.length > 0
                  ? ev.missing_fields.map(m => `
                    <li class="condition-item missing">
                      <span style="font-weight: 600;">[NEED]</span>
                      <span>${escapeHtml(m)}</span>
                    </li>
                  `).join('')
                  : ''}
                ${(!ev.conditions_failed || ev.conditions_failed.length === 0) && (!ev.missing_fields || ev.missing_fields.length === 0)
                  ? '<li class="condition-item" style="color: var(--semantic-pos);">All statutory rules satisfied.</li>'
                  : ''}
              </ul>
            </div>
          </div>
        `;
        evaluationsSlot.appendChild(card);
      });
    } else if (result.response_text) {
      const card = document.createElement('div');
      card.className = 'dossier-card';
      card.innerHTML = `<div class="scheme-summary">${escapeHtml(result.response_text)}</div>`;
      evaluationsSlot.appendChild(card);
    }

    // 3. Application Protocol
    if (result.application_guidance) {
      const g = result.application_guidance;
      const proto = document.createElement('div');
      proto.className = 'protocol-card';
      proto.innerHTML = `
        <div class="protocol-head">
          <div>
            <div class="scheme-name">${escapeHtml(g.scheme_name)} Application Protocol</div>
            <div class="scheme-authority">Standard operating procedure from official guidelines</div>
          </div>
          <a href="${escapeHtml(g.official_portal_url)}" target="_blank" rel="noopener noreferrer" class="btn-secondary">
            Official Portal &nearr;
          </a>
        </div>

        ${g.offline_option ? `
          <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">
            Offline channel: ${escapeHtml(g.offline_option)}
          </div>
        ` : ''}

        <div class="steps-stack">
          ${g.steps.map((st, i) => `
            <div class="step-row">
              <span class="step-idx">${String(i + 1).padStart(2, '0')}</span>
              <span>${escapeHtml(st)}</span>
            </div>
          `).join('')}
        </div>

        <div class="matrix-label">Mandatory Documents</div>
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
          ${g.required_documents.map(d => `
            <span style="font-size: 11px; background: var(--surface-raised); border: 1px solid var(--hairline); padding: 4px 8px; border-radius: var(--radius-sm); color: var(--text-secondary);">
              ${escapeHtml(d)}
            </span>
          `).join('')}
        </div>

        ${g.important_notes ? `
          <div style="font-size: 11px; color: var(--semantic-amber); border-left: 2px solid var(--semantic-amber); padding: 6px 10px; background: var(--semantic-amber-bg); border-radius: 0 var(--radius-sm) var(--radius-sm) 0;">
            Condition: ${escapeHtml(g.important_notes)}
          </div>
        ` : ''}
      `;
      protocolSlot.appendChild(proto);
    }

    // 4. Citations
    if (result.citations && result.citations.length > 0) {
      result.citations.forEach(c => {
        const item = document.createElement('div');
        item.className = 'citation-entry';
        item.innerHTML = `
          <strong>${escapeHtml(c.scheme_name)}</strong> (${escapeHtml(c.section)})<br>
          ${escapeHtml(c.department)} &bull; <a href="${escapeHtml(c.official_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(c.official_url)}</a>
        `;
        citationsSlot.appendChild(item);
      });
    } else {
      citationsSlot.innerHTML = '<div style="font-size: 11px; color: var(--text-muted);">None retrieved</div>';
    }

    // 5. Execution Trace
    if (result.execution_trace && result.execution_trace.length > 0) {
      result.execution_trace.forEach(t => {
        const line = document.createElement('div');
        line.className = 'trace-entry';
        line.innerHTML = `[${escapeHtml(t.agent)}] <span>${escapeHtml(t.summary)}</span>`;
        traceSlot.appendChild(line);
      });
    }
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
});
