// M/S Sandip Kumar - JJM Bihar Accounts & Finance Management App

document.addEventListener('DOMContentLoaded', () => {
    initMobileNav();
    initTransactionModal();
    initSiteModal();
    initCategoryModal();
    initKeyboardShortcuts();
    initLiveSearch();
    initFilters();
    initMagicBento();
});

// Mobile navigation toggle
function initMobileNav() {
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });

        // Close sidebar on outside click
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('mobile-open') && 
                !sidebar.contains(e.target) && 
                !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }
}

// Transaction Modal Logic
function initTransactionModal() {
    const modal = document.getElementById('txModal');
    const openBtn = document.getElementById('btnNewTransaction');
    const closeBtns = document.querySelectorAll('.close-tx-modal');
    const form = document.getElementById('txForm');
    const typeCreditBtn = document.getElementById('typeCreditBtn');
    const typeDebitBtn = document.getElementById('typeDebitBtn');
    const txTypeInput = document.getElementById('txTypeInput');
    const partyLabel = document.getElementById('partyLabel');
    const categorySelect = document.getElementById('categorySelect');

    if (!modal) return;

    function openModal(mode = 'create', data = null) {
        modal.classList.add('active');
        if (mode === 'create') {
            document.getElementById('modalTitle').textContent = 'New Transaction Entry (Credit / Debit)';
            form.reset();
            document.getElementById('txIdInput').value = '';
            document.getElementById('txDateInput').value = new Date().toISOString().split('T')[0];
            setTxType('DEBIT'); // default to debit (expense)

            // Fetch auto voucher number
            fetch('/api/next_voucher')
                .then(res => res.json())
                .then(data => {
                    if (data.voucher_no) {
                        document.getElementById('voucherNoInput').value = data.voucher_no;
                    }
                })
                .catch(err => console.error('Error fetching voucher no:', err));
        } else if (mode === 'edit' && data) {
            document.getElementById('modalTitle').textContent = `Edit Transaction Entry (${data.voucher_no})`;
            document.getElementById('txIdInput').value = data.id;
            document.getElementById('voucherNoInput').value = data.voucher_no;
            document.getElementById('txDateInput').value = data.tx_date;
            document.getElementById('siteSelect').value = data.site_id;
            document.getElementById('partyNameInput').value = data.party_name;
            document.getElementById('amountInput').value = data.amount;
            document.getElementById('paymentModeSelect').value = data.payment_mode;
            document.getElementById('referenceNoInput').value = data.reference_no || '';
            document.getElementById('narrationInput').value = data.narration || '';
            setTxType(data.tx_type);
            document.getElementById('categorySelect').value = data.category;
        }
    }

    function closeModal() {
        modal.classList.remove('active');
    }

    if (openBtn) {
        openBtn.addEventListener('click', () => openModal('create'));
    }

    closeBtns.forEach(btn => btn.addEventListener('click', closeModal));

    // Outside click to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Credit / Debit Switcher
    function setTxType(type) {
        txTypeInput.value = type;
        const siteGroup = document.getElementById('siteSelectGroup');
        const siteSelect = document.getElementById('siteSelect');
        const creditNotice = document.getElementById('creditPersonNotice');
        const partyInput = document.getElementById('partyNameInput');

        if (type === 'CREDIT') {
            typeCreditBtn.classList.add('active-credit');
            typeDebitBtn.classList.remove('active-debit');
            partyLabel.innerHTML = '👤 Received From / Individual Person (Inflow) <span style="color:red">*</span>';
            if (partyInput) partyInput.placeholder = 'e.g. Client / Sandip Kumar / Individual Payer';
            if (siteGroup) siteGroup.style.display = 'none'; // Credit is from individual into central pool
            if (siteSelect) siteSelect.value = '1'; // Head Office / Central Pool
            if (creditNotice) creditNotice.style.display = 'block';
            filterCategoriesByType('CREDIT');
        } else {
            typeDebitBtn.classList.add('active-debit');
            typeCreditBtn.classList.remove('active-credit');
            partyLabel.innerHTML = '🏢 Paid To / Vendor / Contractor / Person (Expense) <span style="color:red">*</span>';
            if (partyInput) partyInput.placeholder = 'e.g. Sunil Contractor / Jindal / Driver / Cement Agency';
            if (siteGroup) siteGroup.style.display = 'block'; // Debit is spent on a specific project site
            if (creditNotice) creditNotice.style.display = 'none';
            filterCategoriesByType('DEBIT');
        }
    }

    if (typeCreditBtn && typeDebitBtn) {
        typeCreditBtn.addEventListener('click', () => setTxType('CREDIT'));
        typeDebitBtn.addEventListener('click', () => setTxType('DEBIT'));
    }

    function filterCategoriesByType(type) {
        if (!categorySelect) return;
        const options = categorySelect.querySelectorAll('option');
        options.forEach(opt => {
            const optType = opt.getAttribute('data-type');
            if (opt.value === '__add_new_purpose__' || !optType || optType === 'BOTH' || optType === type) {
                opt.style.display = '';
            } else {
                opt.style.display = 'none';
            }
        });
        // Select first visible real category
        for (let opt of options) {
            if (opt.style.display !== 'none' && opt.value !== '' && opt.value !== '__add_new_purpose__') {
                categorySelect.value = opt.value;
                break;
            }
        }
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            if (e.target.value === '__add_new_purpose__') {
                const currentType = txTypeInput ? txTypeInput.value : 'DEBIT';
                if (window.openCategoryModal) {
                    window.openCategoryModal(currentType);
                }
                filterCategoriesByType(currentType);
            }
        });
    }

    // Submit Handler
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';

            const formData = new FormData(form);
            const isEdit = !!document.getElementById('txIdInput').value;
            const endpoint = isEdit 
                ? `/api/transaction/${document.getElementById('txIdInput').value}/update` 
                : '/api/transaction/create';

            fetch(endpoint, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(result => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Transaction';
                if (result.success) {
                    closeModal();
                    // Show confirmation and reload
                    window.location.reload();
                } else {
                    alert('Error: ' + (result.message || 'Could not save transaction'));
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Transaction';
                alert('Network Error: ' + err.message);
            });
        });
    }

    // Global hook for editing
    window.openEditTransaction = function(txId) {
        fetch(`/api/transaction/${txId}`)
            .then(res => res.json())
            .then(data => {
                if (data.transaction) {
                    openModal('edit', data.transaction);
                } else {
                    alert('Transaction not found');
                }
            })
            .catch(err => alert('Error loading transaction details'));
    };

    // Global hook for duplicating / copying an existing transaction
    window.duplicateTransaction = function(txId) {
        fetch(`/api/transaction/${txId}`)
            .then(res => res.json())
            .then(data => {
                if (data.transaction) {
                    const tx = data.transaction;
                    const modal = document.getElementById('txModal');
                    const form = document.getElementById('txForm');
                    modal.classList.add('active');
                    document.getElementById('modalTitle').textContent = `Duplicate / Copy Entry (${tx.voucher_no})`;
                    form.reset();
                    document.getElementById('txIdInput').value = ''; // clean new ID
                    document.getElementById('txDateInput').value = new Date().toISOString().split('T')[0];

                    // Fetch next fresh auto voucher number
                    fetch('/api/next_voucher')
                        .then(r => r.json())
                        .then(vd => {
                            if (vd.voucher_no) document.getElementById('voucherNoInput').value = vd.voucher_no;
                        });

                    // Pre-populate fields
                    document.getElementById('partyNameInput').value = tx.party_name;
                    document.getElementById('amountInput').value = tx.amount;
                    document.getElementById('paymentModeSelect').value = tx.payment_mode;
                    document.getElementById('referenceNoInput').value = tx.reference_no || '';
                    document.getElementById('narrationInput').value = tx.narration ? `Copy of ${tx.voucher_no}: ${tx.narration}` : `Copy of ${tx.voucher_no}`;

                    if (tx.tx_type === 'CREDIT') {
                        document.getElementById('typeCreditBtn').click();
                    } else {
                        document.getElementById('typeDebitBtn').click();
                        document.getElementById('siteSelect').value = tx.site_id;
                    }

                    setTimeout(() => {
                        document.getElementById('categorySelect').value = tx.category;
                    }, 50);
                } else {
                    alert('Transaction not found');
                }
            })
            .catch(err => alert('Error duplicating transaction: ' + err.message));
    };

    // Global hook for deleting
    window.deleteTransaction = function(txId, voucherNo) {
        if (!confirm(`Are you sure you want to permanently delete Voucher ${voucherNo}?\n\nThis action cannot be undone.`)) {
            return;
        }

        fetch(`/api/transaction/${txId}/delete`, {
            method: 'POST'
        })
        .then(res => res.json())
        .then(res => {
            if (res.success) {
                window.location.reload();
            } else {
                alert('Delete Failed: ' + (res.message || 'Permission denied'));
            }
        })
        .catch(err => alert('Network Error during delete: ' + err.message));
    };
}

// Live Search in Table
function initLiveSearch() {
    const searchInput = document.getElementById('tableSearchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const rows = document.querySelectorAll('.data-table tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(query)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// Dynamic Filter Helpers (FY, Month, Site)
function initFilters() {
    const fySelect = document.getElementById('filterFY');
    const monthSelect = document.getElementById('filterMonth');
    const siteSelect = document.getElementById('filterSite');

    function applyFilters() {
        const url = new URL(window.location.href);
        if (fySelect) url.searchParams.set('fy', fySelect.value);
        if (monthSelect) url.searchParams.set('month', monthSelect.value);
        if (siteSelect) url.searchParams.set('site_id', siteSelect.value);
        window.location.href = url.toString();
    }

    if (fySelect) fySelect.addEventListener('change', applyFilters);
    if (monthSelect) monthSelect.addEventListener('change', applyFilters);
    if (siteSelect) siteSelect.addEventListener('change', applyFilters);
}

// Print Voucher / Daybook trigger
window.triggerPrint = function() {
    window.print();
};

// Keyboard Shortcuts (Feature 5)
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const activeTag = document.activeElement ? document.activeElement.tagName : '';
        const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(activeTag);

        // 1. '+' or Alt+N opens New Entry modal
        if ((e.key === '+' && !isInput) || (e.altKey && (e.key === 'n' || e.key === 'N'))) {
            e.preventDefault();
            const btn = document.getElementById('btnNewTransaction');
            if (btn) btn.click();
        }

        // 2. Alt+S opens Add New Site modal
        if (e.altKey && (e.key === 's' || e.key === 'S')) {
            e.preventDefault();
            if (window.openSiteModal) window.openSiteModal();
        }

        // 3. Alt+P opens Add New Purpose / Category modal
        if (e.altKey && (e.key === 'p' || e.key === 'P')) {
            e.preventDefault();
            if (window.openCategoryModal) window.openCategoryModal();
        }

        // 4. Escape closes any active modal
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal-overlay.active');
            if (activeModal) {
                activeModal.classList.remove('active');
            }
        }
    });
}

// Add New Site Modal Logic (Site Master Option)
function initSiteModal() {
    const siteModal = document.getElementById('siteModal');
    const openBtn = document.getElementById('btnOpenAddSite');
    const closeBtns = document.querySelectorAll('.close-site-modal');
    const form = document.getElementById('siteForm');

    window.openSiteModal = function() {
        if (!siteModal) return;
        siteModal.classList.add('active');
        if (form) form.reset();

        // Fetch auto next site code
        fetch('/api/next_site_code')
            .then(res => res.json())
            .then(data => {
                if (data.code) {
                    document.getElementById('newSiteCodeInput').value = data.code;
                }
            })
            .catch(err => console.error('Error fetching site code:', err));

        setTimeout(() => {
            const nameInput = document.getElementById('newSiteNameInput');
            if (nameInput) nameInput.focus();
        }, 150);
    };

    window.closeSiteModal = function() {
        if (siteModal) siteModal.classList.remove('active');
    };

    if (openBtn) {
        openBtn.addEventListener('click', window.openSiteModal);
    }

    closeBtns.forEach(btn => btn.addEventListener('click', window.closeSiteModal));

    if (siteModal) {
        siteModal.addEventListener('click', (e) => {
            if (e.target === siteModal) window.closeSiteModal();
        });
    }

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving Site...';

            const formData = new FormData(form);
            fetch('/api/site/create', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(result => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Site';
                if (result.success) {
                    window.closeSiteModal();

                    // Dynamically append new site to all site dropdowns without page reload
                    const siteSelects = [
                        document.getElementById('siteSelect'),
                        document.getElementById('siteLedgerSelect'),
                        document.getElementById('filterSite')
                    ];

                    siteSelects.forEach(sel => {
                        if (sel) {
                            const opt = document.createElement('option');
                            opt.value = result.site_id;
                            opt.textContent = `${result.code} — ${result.name} (${result.district})`;
                            sel.appendChild(opt);
                            sel.value = result.site_id;
                        }
                    });

                    alert(result.message);
                } else {
                    alert('Error: ' + (result.message || 'Could not add site'));
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Site';
                alert('Network Error: ' + err.message);
            });
        });
    }
}

// Add New Purpose / Category Modal Logic
function initCategoryModal() {
    const catModal = document.getElementById('categoryModal');
    const openBtn = document.getElementById('btnOpenAddCategory');
    const closeBtns = document.querySelectorAll('.close-cat-modal');
    const form = document.getElementById('categoryForm');
    const typeSelect = document.getElementById('newCatTypeSelect');
    const nameInput = document.getElementById('newCatNameInput');

    window.openCategoryModal = function(defaultType = null) {
        if (!catModal) return;
        catModal.classList.add('active');
        if (form) form.reset();

        // If not specified, infer from current transaction modal mode if active
        if (!defaultType) {
            const txTypeInput = document.getElementById('txTypeInput');
            if (txTypeInput && txTypeInput.value) {
                defaultType = txTypeInput.value;
            }
        }

        if (defaultType && typeSelect) {
            typeSelect.value = defaultType.toUpperCase();
        }

        setTimeout(() => {
            if (nameInput) nameInput.focus();
        }, 150);
    };

    window.closeCategoryModal = function() {
        if (catModal) catModal.classList.remove('active');
    };

    if (openBtn) {
        openBtn.addEventListener('click', () => window.openCategoryModal());
    }

    closeBtns.forEach(btn => btn.addEventListener('click', window.closeCategoryModal));

    if (catModal) {
        catModal.addEventListener('click', (e) => {
            if (e.target === catModal) window.closeCategoryModal();
        });
    }

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving Purpose...';

            const formData = new FormData(form);
            fetch('/api/category/create', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(result => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Purpose';
                if (result.success) {
                    window.closeCategoryModal();

                    // Dynamically append new purpose to #categorySelect in transaction modal
                    const catSelect = document.getElementById('categorySelect');
                    if (catSelect) {
                        let existingOpt = null;
                        for (let opt of catSelect.options) {
                            if (opt.value.toLowerCase() === result.name.toLowerCase()) {
                                existingOpt = opt;
                                break;
                            }
                        }

                        if (!existingOpt) {
                            const newOpt = document.createElement('option');
                            newOpt.value = result.name;
                            newOpt.textContent = `${result.name} (${result.type})`;
                            newOpt.setAttribute('data-type', result.type);

                            // Insert before the last "+ Add New" option
                            const addNewOpt = catSelect.querySelector('option[value="__add_new_purpose__"]');
                            if (addNewOpt) {
                                catSelect.insertBefore(newOpt, addNewOpt);
                            } else {
                                catSelect.appendChild(newOpt);
                            }
                            catSelect.value = result.name;
                        } else {
                            catSelect.value = existingOpt.value;
                        }
                    }

                    // Also dynamically append to #filterCategory if on transactions page
                    const filterCat = document.getElementById('filterCategory');
                    if (filterCat) {
                        let existsInFilter = false;
                        for (let opt of filterCat.options) {
                            if (opt.value.toLowerCase() === result.name.toLowerCase()) {
                                existsInFilter = true;
                                break;
                            }
                        }
                        if (!existsInFilter) {
                            const fOpt = document.createElement('option');
                            fOpt.value = result.name;
                            fOpt.textContent = result.name;
                            filterCat.appendChild(fOpt);
                        }
                    }

                    alert(result.message);
                } else {
                    alert('Error: ' + (result.message || 'Could not save purpose'));
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Purpose';
                alert('Network Error: ' + err.message);
            });
        });
    }
}

// ================= MAGIC BENTO INTERACTIVE ENGINE =================
function initMagicBento() {
    const cards = document.querySelectorAll('.kpi-card');
    if (!cards.length) return;

    cards.forEach(card => {
        // Inject spotlight & glowing border elements if not present
        if (!card.querySelector('.mb-light')) {
            const light = document.createElement('span');
            light.className = 'mb-light';
            card.appendChild(light);
        }
        if (!card.querySelector('.mb-border')) {
            const border = document.createElement('span');
            border.className = 'mb-border';
            card.appendChild(border);
        }

        // Mouse move tracking for 3D tilt & cursor spotlight
        card.addEventListener('mouseenter', () => {
            card.style.setProperty('--mb-hot', '1');
            card.style.setProperty('--mb-near', '1');
            card.style.setProperty('--mb-scale', '1.025');
        });

        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // 3D perspective tilt calculation (-5.5deg to +5.5deg)
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -5.5;
            const rotateY = ((x - centerX) / centerX) * 5.5;

            card.style.setProperty('--mb-x', `${x.toFixed(1)}px`);
            card.style.setProperty('--mb-y', `${y.toFixed(1)}px`);
            card.style.setProperty('--mb-rx', `${rotateX.toFixed(2)}deg`);
            card.style.setProperty('--mb-ry', `${rotateY.toFixed(2)}deg`);
        });

        card.addEventListener('mouseleave', () => {
            card.style.setProperty('--mb-hot', '0');
            card.style.setProperty('--mb-near', '0');
            card.style.setProperty('--mb-rx', '0deg');
            card.style.setProperty('--mb-ry', '0deg');
            card.style.setProperty('--mb-scale', '1');
        });

        // Click Ripple Wave Effect
        card.addEventListener('pointerdown', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const ripple = document.createElement('span');
            ripple.className = 'mb-ripple';
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            card.appendChild(ripple);
            setTimeout(() => {
                if (ripple.parentNode) ripple.remove();
            }, 680);
        });
    });
}
