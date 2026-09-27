const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('prediction-form');
    const resultsSection = document.getElementById('results-section');
    const courseSearch = document.getElementById('course-search');
    const courseDropdown = document.getElementById('course-dropdown');
    const selectedTagsContainer = document.getElementById('selected-tags');
    const dataBadge = document.getElementById('data-badge');
    const dataYear = document.getElementById('data-year');
    const collegeCount = document.getElementById('college-count');

    let allCourses = [];
    let selectedCourses = [];
    let highlightedIndex = -1;

    // ─── Load Metadata ──────────────────────────────────────────
    async function loadMetadata() {
        try {
            const res = await fetch(`${API_BASE}/metadata`);
            if (!res.ok) throw new Error('Metadata fetch failed');
            const meta = await res.json();

            allCourses = meta.courses.sort();

            // Show data info badge
            dataYear.textContent = meta.data_year;
            collegeCount.textContent = meta.total_colleges;
            dataBadge.style.display = 'flex';

        } catch (err) {
            console.warn('Could not load metadata:', err);
            courseSearch.placeholder = 'Start the backend to load courses';
        }
    }
    loadMetadata();

    // ─── Multi-Select Course Tags ───────────────────────────────
    function renderTags() {
        selectedTagsContainer.innerHTML = '';
        selectedCourses.forEach(course => {
            const tag = document.createElement('span');
            tag.className = 'course-tag';
            tag.innerHTML = `${truncate(course, 35)}<button class="tag-remove" data-course="${course}">&times;</button>`;
            selectedTagsContainer.appendChild(tag);
        });

        // Bind remove buttons
        selectedTagsContainer.querySelectorAll('.tag-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const c = btn.dataset.course;
                selectedCourses = selectedCourses.filter(x => x !== c);
                renderTags();
            });
        });
    }

    function truncate(str, n) {
        return str.length > n ? str.substring(0, n - 1) + '…' : str;
    }

    function addCourse(course) {
        if (!selectedCourses.includes(course)) {
            selectedCourses.push(course);
            renderTags();
        }
        courseSearch.value = '';
        courseDropdown.classList.remove('active');
        courseSearch.focus();
    }

    // ─── Searchable Dropdown ────────────────────────────────────
    function renderDropdown(filter = '') {
        courseDropdown.innerHTML = '';
        highlightedIndex = -1;
        const query = filter.toLowerCase();
        const matched = query
            ? allCourses.filter(c => c.toLowerCase().includes(query))
            : allCourses;

        // Exclude already selected
        const available = matched.filter(c => !selectedCourses.includes(c));

        if (available.length === 0) {
            courseDropdown.innerHTML = '<div class="no-results">No more courses match</div>';
            courseDropdown.classList.add('active');
            return;
        }

        available.slice(0, 40).forEach((course, i) => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.textContent = course;
            item.dataset.index = i;
            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                addCourse(course);
            });
            courseDropdown.appendChild(item);
        });

        if (available.length > 40) {
            const more = document.createElement('div');
            more.className = 'no-results';
            more.textContent = `${available.length - 40} more — keep typing to narrow`;
            courseDropdown.appendChild(more);
        }

        courseDropdown.classList.add('active');
    }

    courseSearch.addEventListener('focus', () => renderDropdown(courseSearch.value));
    courseSearch.addEventListener('input', () => renderDropdown(courseSearch.value));
    courseSearch.addEventListener('blur', () => {
        setTimeout(() => courseDropdown.classList.remove('active'), 150);
    });

    courseSearch.addEventListener('keydown', (e) => {
        const items = courseDropdown.querySelectorAll('.dropdown-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
            updateHighlight(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            highlightedIndex = Math.max(highlightedIndex - 1, 0);
            updateHighlight(items);
        } else if (e.key === 'Enter' && highlightedIndex >= 0) {
            e.preventDefault();
            addCourse(items[highlightedIndex].textContent);
        } else if (e.key === 'Escape') {
            courseDropdown.classList.remove('active');
        } else if (e.key === 'Backspace' && courseSearch.value === '' && selectedCourses.length > 0) {
            selectedCourses.pop();
            renderTags();
        }
    });

    function updateHighlight(items) {
        items.forEach((el, i) => {
            el.classList.toggle('highlighted', i === highlightedIndex);
            if (i === highlightedIndex) el.scrollIntoView({ block: 'nearest' });
        });
    }

    // ─── Form Submission ────────────────────────────────────────
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (selectedCourses.length === 0) {
            courseSearch.focus();
            courseSearch.style.borderColor = 'var(--danger)';
            setTimeout(() => courseSearch.style.borderColor = '', 2000);
            return;
        }

        resultsSection.innerHTML = `
            <div class="loader-container">
                <div class="loader"></div>
                <div class="loader-text">Checking eligibility across all colleges...</div>
            </div>
        `;

        const payload = {
            rank: parseInt(document.getElementById('rank').value),
            category: document.getElementById('category').value,
            courses: selectedCourses,
            is_hk_region: document.getElementById('is_hk_region').checked,
            is_rural: document.getElementById('is_rural').checked,
            is_kannada: document.getElementById('is_kannada').checked,
        };

        try {
            const res = await fetch(`${API_BASE}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Check failed');
            }

            const data = await res.json();
            renderResults(data, payload);
        } catch (error) {
            console.error('Error:', error);
            resultsSection.innerHTML = `
                <div class="placeholder-state">
                    <div class="placeholder-icon">&#9888;</div>
                    <div class="placeholder-text" style="color: var(--danger);">Connection Failed</div>
                    <div class="placeholder-sub">${error.message || 'Ensure backend is running on port 8000.'}</div>
                </div>
            `;
        }
    });

    // ─── Render Results ─────────────────────────────────────────
    // ─── Tier display config ───────────────────────────────────────
    const TIER_CONFIG = {
        '1': { icon: '⭐', label: 'Tier 1 — Elite & Highly Competitive', cssClass: 'tier-header-1' },
        '2': { icon: '🏆', label: 'Tier 2 — Very Good & Well Established', cssClass: 'tier-header-2' },
        '3': { icon: '✅', label: 'Tier 3 — Good & Established', cssClass: 'tier-header-3' },
        '4': { icon: '📘', label: 'Tier 4 — Developing & Upcoming', cssClass: 'tier-header-4' },
        '5': { icon: '📋', label: 'Tier 5 — Emerging', cssClass: 'tier-header-5' },
        'other': { icon: '📂', label: 'Other Colleges', cssClass: 'tier-header-other' },
    };

    function extractTierNumber(tierStr) {
        if (!tierStr) return 'other';
        const m = tierStr.match(/Tier (\d+)/i);
        return m ? m[1] : 'other';
    }

    function renderResults(results, payload) {
        resultsSection.innerHTML = '';

        if (!results || results.length === 0) {
            resultsSection.innerHTML = `
                <div class="placeholder-state">
                    <div class="placeholder-icon">&#128269;</div>
                    <div class="placeholder-text">No eligible colleges found</div>
                    <div class="placeholder-sub">Your rank doesn't meet the cutoff for any college with these filters. Try different courses or category.</div>
                </div>
            `;
            return;
        }

        // Summary header
        const header = document.createElement('div');
        header.className = 'results-header';
        header.innerHTML = `
            <span class="results-count">${results.length} college${results.length !== 1 ? 's' : ''} you can get into</span>
            <span class="results-rank-tag">Your Rank: #${payload.rank.toLocaleString()}</span>
        `;
        resultsSection.appendChild(header);

        // Group results by tier
        const tierGroups = new Map();
        results.forEach(r => {
            const tierKey = extractTierNumber(r.tier);
            if (!tierGroups.has(tierKey)) tierGroups.set(tierKey, []);
            tierGroups.get(tierKey).push(r);
        });

        // Sort tier groups: 1, 2, 3, 4, 5, then 'other'
        const sortedKeys = [...tierGroups.keys()].sort((a, b) => {
            if (a === 'other') return 1;
            if (b === 'other') return -1;
            return parseInt(a) - parseInt(b);
        });

        // Track card index for staggered animation
        let globalCardIndex = 0;

        sortedKeys.forEach(tierKey => {
            const items = tierGroups.get(tierKey);
            const config = TIER_CONFIG[tierKey] || TIER_CONFIG['other'];

            // Create tier section
            const section = document.createElement('div');
            section.className = 'tier-section';

            // Create header
            const sectionHeader = document.createElement('div');
            sectionHeader.className = `tier-section-header ${config.cssClass}`;
            sectionHeader.innerHTML = `
                <div class="tier-header-left">
                    <span class="tier-header-icon">${config.icon}</span>
                    <span class="tier-header-title">${config.label}</span>
                    <span class="tier-header-count">${items.length}</span>
                </div>
                <span class="tier-header-chevron">▼</span>
            `;

            // Toggle collapse on click
            sectionHeader.addEventListener('click', () => {
                section.classList.toggle('collapsed');
            });

            // Create body with cards
            const sectionBody = document.createElement('div');
            sectionBody.className = 'tier-section-body';

            items.forEach(r => {
                sectionBody.appendChild(createCard(r, globalCardIndex, payload));
                globalCardIndex++;
            });

            section.appendChild(sectionHeader);
            section.appendChild(sectionBody);
            resultsSection.appendChild(section);
        });
    }

    function createCard(result, index, payload) {
        const card = document.createElement('div');
        card.className = 'result-card card-eligible';
        card.style.animationDelay = `${Math.min(index, 15) * 0.07}s`;

        const marginText = result.margin === 0
            ? 'Exact cutoff match!'
            : `+${result.margin.toLocaleString()} ranks safe`;

        const statusClass = 'status-yes';
        const statusIcon = '✓';

        // Tier badge
        let tierHtml = '';
        if (result.tier) {
            const tierShort = result.tier.replace(/Tier \d+:\s*/, '');
            const tierNum = result.tier.match(/Tier (\d+)/);
            const tierClass = tierNum ? `tier-${tierNum[1]}` : 'tier-default';
            tierHtml = `<span class="tier-badge ${tierClass}" title="${result.tier}">Tier ${tierNum ? tierNum[1] : '?'}</span>`;
        }

        // Qualifying pool badge
        let poolHtml = '';
        if (result.qualifying_pool) {
            poolHtml = `<span class="pool-badge" title="Qualified Quota Pool">${result.qualifying_pool}</span>`;
        }

        // Priority rank badge
        const rankBadge = result.priority_rank < 999
            ? `<span class="priority-badge" title="College Priority Ranking">#${result.priority_rank}</span>`
            : '';

        const displayName = (result.college_full || result.college).replace(/^E\d+\s*-\s*/i, '');

        card.innerHTML = `
            <div class="card-header">
                <div class="college-info">
                    <div class="college-name-row">
                        ${rankBadge}
                        <div class="college-name">
                            <span class="cet-code-tag">${result.cet_code || 'N/A'}</span>
                            ${displayName}
                        </div>
                    </div>
                    <div class="course-tier-row">
                        <div class="course-badge">${result.course}</div>
                        ${tierHtml}
                        ${poolHtml}
                    </div>
                </div>
                <div class="status-badge ${statusClass}">${statusIcon}</div>
            </div>
            <div class="card-body">
                <div class="stat-group">
                    <span class="stat-label">Cutoff (${result.year})</span>
                    <span class="stat-value">#${result.cutoff.toLocaleString()}</span>
                </div>
                <div class="stat-group">
                    <span class="stat-label">Your Rank</span>
                    <span class="stat-value">#${payload.rank.toLocaleString()}</span>
                </div>
                <div class="stat-group">
                    <span class="stat-label">Margin</span>
                    <span class="stat-value margin-value margin-safe">${marginText}</span>
                </div>
            </div>
        `;
        return card;
    }

    function cleanCollegeName(name) {
        let clean = name
            .replace(/\s+POST\s+BOX.*/i, '')
            .replace(/\s+P\.?O\.?\s+BOX.*/i, '')
            .replace(/\s+SURVEY\s+NO.*/i, '')
            .replace(/\s+PIN\s+\d{6}.*/i, '')
            .replace(/,\s*Karnataka\s+\d+/i, '')
            .replace(/\s{2,}/g, ' ')
            .trim();
        if (clean.length > 80) clean = clean.substring(0, 77) + '...';
        return clean;
    }
});
