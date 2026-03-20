// Manage desks script: search, paging and simple edit/delete flow
(() => {
    const apiUrl = window.CONFIG && window.CONFIG.apiUrl ? window.CONFIG.apiUrl : '/api/desks';
    let currentPage = 1;
    let perPage = 10;
    let totalPages = 1;
    let totalResults = 0;
    const typeDelay = 300;
    let typingTimer = null;

    // Code to fetch desks from the API with current filters and pagination, then render the table
    function fetchDesks(page=1) {
        const q = document.getElementById('search_q').value;
        const site = document.getElementById('site_filter').value;
        const per = document.getElementById('per_page').value;
        const url = new URL(apiUrl, window.location.origin);
        url.searchParams.set('page', page);
        url.searchParams.set('per_page', per);
        if (q) url.searchParams.set('q', q);
        if (site) url.searchParams.set('site_id', site);
        fetch(url.toString())
            .then(r => r.json())
            .then(data => renderDesksTable(data))
            .catch(() => {});
    }

    function renderDesksTable(data) {
        const container = document.getElementById('desks-table');
        if (!data.desks || data.desks.length === 0) {
            container.innerHTML = '<p>No desks found.</p>';
            document.getElementById('desks-pagination').innerHTML = '';
            return;
        }
        // Build the HTML table with desk data and edit/delete buttons
        let html = '<table border="1" cellpadding="5"><tr><th>Desk Number</th><th>Floor</th><th>Site</th><th>Actions</th></tr>';
        data.desks.forEach(d => {
            html += `<tr data-site-id="${d.site_id}" data-site-name="${d.site_name}">`;
            html += `<td>${d.desk_number}</td>`;
            html += `<td>${d.floor}</td>`;
            html += `<td>${d.site_name}</td>`;
            html += `<td><button class="edit-desk" data-id="${d.id}">Edit</button> <button class="delete-desk" data-id="${d.id}">Delete</button></td>`;
            html += `</tr>`;
        });
        html += '</table>';
        container.innerHTML = html;

        totalPages = data.total_pages;
        currentPage = data.page;
        totalResults = data.total || 0;
        renderDesksPagination();

        // Setup edit buttons
        document.querySelectorAll('.edit-desk').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const row = btn.closest('tr');
                const deskNumber = row.children[0].innerText;
                const floor = row.children[1].innerText;
                const siteId = row.dataset.siteId || '';
                document.getElementById('desk-form-title').innerText = 'Edit Desk';
                document.getElementById('desk_action_field').value = 'update';
                document.getElementById('desk_id').value = id;
                document.getElementById('desk_number').value = deskNumber;
                document.getElementById('floor').value = floor;
                document.getElementById('site_id_select').value = siteId;
                document.getElementById('desk_submit_btn').innerText = 'Update Desk';
                const cancelBtn = document.getElementById('cancel-edit-btn');
                if (cancelBtn) cancelBtn.style.display = 'inline-block';
            });
        });

        // Setup delete buttons
        document.querySelectorAll('.delete-desk').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!confirm('Delete this desk?')) return;
                const id = btn.dataset.id;
                document.getElementById('desk_action_field').value = 'delete';
                document.getElementById('desk_id').value = id;
                const confirmField = document.getElementById('desk_confirm_delete_field');
                if (confirmField) confirmField.value = 'yes';
                document.getElementById('desk-main-form').submit();
            });
        });
    }

    // Code to setup the pagination controls
    function renderDesksPagination() {
        const el = document.getElementById('desks-pagination');
        if (totalPages <= 1) { el.innerHTML = ''; return; }
        let html = '';
        if (currentPage > 1) html += '<button id="prev-page">< Prev</button>';
        html += ' Page ' + currentPage + ' of ' + totalPages + ' (' + totalResults + ' results) ';
        if (currentPage < totalPages) html += '<button id="next-page">Next ></button>';
        el.innerHTML = html;
        const prev = document.getElementById('prev-page'); if (prev) prev.addEventListener('click', () => fetchDesks(currentPage-1));
        const next = document.getElementById('next-page'); if (next) next.addEventListener('click', () => fetchDesks(currentPage+1));
    }

    const searchInput = document.getElementById('search_q');
    if (searchInput) searchInput.addEventListener('input', () => {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => fetchDesks(1), typeDelay);
    });
    const perInput = document.getElementById('per_page');
    if (perInput) {
        perInput.addEventListener('input', () => { clearTimeout(typingTimer); typingTimer = setTimeout(() => fetchDesks(1), typeDelay); });
        perInput.addEventListener('change', () => fetchDesks(1));
    }
    const siteSelect = document.getElementById('site_filter');
    if (siteSelect) siteSelect.addEventListener('change', () => fetchDesks(1));

    const cancelBtn = document.getElementById('cancel-edit-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            document.getElementById('desk-form-title').innerText = 'Create Desk';
            document.getElementById('desk_action_field').value = 'create';
            document.getElementById('desk_id').value = '';
            const confirmDesk = document.getElementById('desk_confirm_delete_field');
            if (confirmDesk) confirmDesk.value = '';
            document.getElementById('desk_number').value = '';
            document.getElementById('floor').value = '';
            document.getElementById('site_id_select').value = '';
            document.getElementById('desk_submit_btn').innerText = 'Create Desk';
            cancelBtn.style.display = 'none';
        });
    }

    fetchDesks();
})();