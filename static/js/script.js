/**
 * FactVerify AI - Production Client JavaScript Framework
 */

document.addEventListener('DOMContentLoaded', () => {
    initTextareaHandlers();
    initMobileNav();
    initFormSubmissions();
    initHistoryFilters();
});

/**
 * Fills textarea with example claim and focuses input
 */
function fillExample(claimText) {
    const textarea = document.getElementById('claimInput');
    if (textarea) {
        textarea.value = claimText;
        updateCharCount(textarea);
        textarea.focus();
        
        // Smooth scroll to verify section if needed
        const verifySection = document.getElementById('verifySection');
        if (verifySection) {
            verifySection.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

/**
 * Character count and clear button handlers
 */
function initTextareaHandlers() {
    const textarea = document.getElementById('claimInput');
    const clearBtn = document.getElementById('clearBtn');

    if (textarea) {
        textarea.addEventListener('input', () => updateCharCount(textarea));
        updateCharCount(textarea);
    }

    if (clearBtn && textarea) {
        clearBtn.addEventListener('click', () => {
            textarea.value = '';
            updateCharCount(textarea);
            textarea.focus();
        });
    }
}

function updateCharCount(textarea) {
    const countSpan = document.getElementById('charCount');
    if (countSpan && textarea) {
        const len = textarea.value.length;
        const max = textarea.getAttribute('maxlength') || 500;
        countSpan.textContent = `${len} / ${max}`;
    }
}

/**
 * Mobile Navigation Menu Toggle
 */
function initMobileNav() {
    const toggleBtn = document.getElementById('mobileToggle');
    const navLinks = document.getElementById('navLinks');

    if (toggleBtn && navLinks) {
        toggleBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }
}

/**
 * Form Loading State & Spinner Prevention
 */
function initFormSubmissions() {
    const verifyForm = document.getElementById('verifyForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnSpinner = document.getElementById('btnSpinner');
    const loadingState = document.getElementById('loadingState');

    if (verifyForm) {
        verifyForm.addEventListener('submit', (e) => {
            const textarea = document.getElementById('claimInput');
            if (!textarea || !textarea.value.trim()) {
                e.preventDefault();
                alert('Please enter a statement to verify.');
                return;
            }

            // Trigger visual loading states
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.7';
            }
            if (btnSpinner) {
                btnSpinner.style.display = 'inline-block';
            }
            if (loadingState) {
                loadingState.style.display = 'block';
            }
        });
    }
}

/**
 * History Live Search & Category Filtering
 */
function initHistoryFilters() {
    const searchInput = document.getElementById('historySearch');
    const filterChips = document.querySelectorAll('.filter-chip');
    const historyItems = document.querySelectorAll('.history-card-item');

    let currentCategory = 'all';

    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }

    filterChips.forEach(chip => {
        chip.addEventListener('click', () => {
            filterChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentCategory = chip.getAttribute('data-filter-val') || 'all';
            applyFilters();
        });
    });

    function applyFilters() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

        historyItems.forEach(item => {
            const domain = item.getAttribute('data-domain') || '';
            const searchData = item.getAttribute('data-text') || '';

            const matchesCategory = (currentCategory === 'all') || (domain.toLowerCase() === currentCategory.toLowerCase());
            const matchesQuery = !query || searchData.includes(query);

            if (matchesCategory && matchesQuery) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
}
