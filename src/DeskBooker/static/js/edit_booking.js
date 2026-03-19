
// JavaScript for edit bookings page
(() => {
    const cfg = window.CONFIG || {};
    const apiUrl = cfg.apiUrl;
    const desks = cfg.desks || [];
    let currentPage = cfg.initialPage || 1;
    let perPage = cfg.initialPerPage || 10;
    let totalPages = cfg.initialTotalPages || 1;
    let totalResults = cfg.initialTotal || 0;

    const typeDelay = 300;
    let typingTimer = null;

    // Code to render the bookings table with editable fields and update buttons
    function renderTable(data) {
        const container = document.getElementById('bookings-table-container');
        if (!data.bookings || data.bookings.length === 0) {
            container.innerHTML = '<p>No bookings found.</p>';
            document.getElementById('bookings-pagination').innerHTML = '';
            return;
        }

        // Build the HTML table with booking data and editable fields for desk, start time, and end time, along with update buttons
        let html = '<table border="1" cellpadding="5"><tr><th>Desk</th><th>User</th><th>Start Time</th><th>End Time</th><th>Action</th></tr>';
        data.bookings.forEach(b => {
            html += '<tr>';
            html += '<td><select data-booking-id="' + b.booking_id + '" class="desk-select">';
            desks.forEach(d => {
                html += '<option value="' + d.id + '"' + (d.id == b.desk_id ? ' selected' : '') + '>' + d.desk_number + '</option>';
            });
            html += '</select></td>';
            html += '<td>' + (b.user_name || '') + '</td>';
            html += '<td><input type="datetime-local" class="start-input" value="' + (b.start_time.replace(' ', 'T')) + '"></td>';
            html += '<td><input type="datetime-local" class="end-input" value="' + (b.end_time.replace(' ', 'T')) + '"></td>';
            html += '<td><button class="update-btn" data-booking-id="' + b.booking_id + '">Update</button></td>';
            html += '</tr>';
        });
        html += '</table>';
        container.innerHTML = html;

        // update pagination state
        totalPages = data.total_pages;
        currentPage = data.page;
        totalResults = data.total || 0;
        renderPagination();

        // set up update buttons
        document.querySelectorAll('.update-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                const bid = this.dataset.bookingId;
                const row = this.closest('tr');
                const deskSel = row.querySelector('.desk-select');
                const start = row.querySelector('.start-input').value;
                const end = row.querySelector('.end-input').value;

                document.getElementById('form_booking_id').value = bid;
                document.getElementById('form_desk_id').value = deskSel.value;
                document.getElementById('form_start_time').value = start;
                document.getElementById('form_end_time').value = end;
                document.getElementById('update-form').submit();
            });
        });
    }

    //Code to setup the pagination controls
    function renderPagination() {
        const el = document.getElementById('bookings-pagination');
        if (totalPages <= 1) { el.innerHTML = ''; return; }
        let html = '';
        if (currentPage > 1) html += '<button id="prev-page">< Prev</button>';
        html += ' Page ' + currentPage + ' of ' + totalPages + ' (' + (totalResults) + ' results) ';
        if (currentPage < totalPages) html += '<button id="next-page">Next ></button>';
        el.innerHTML = html;
        const prev = document.getElementById('prev-page'); if (prev) prev.addEventListener('click', () => { fetchPage(currentPage-1); });
        const next = document.getElementById('next-page'); if (next) next.addEventListener('click', () => { fetchPage(currentPage+1); });
    }

    function fetchPage(page=1) {
        const qEl = document.getElementById('search_q');
        const q = qEl ? qEl.value : '';
        const adminChk = document.getElementById('admin_view_chk');
        const admin_view = adminChk ? (adminChk.checked ? '1' : '0') : '0';
        const perEl = document.getElementById('per_page');
        const per = perEl ? perEl.value : perPage;
        const url = new URL(apiUrl, window.location.origin);
        url.searchParams.set('page', page);
        url.searchParams.set('per_page', per);
        url.searchParams.set('admin_view', admin_view);
        if (q) url.searchParams.set('q', q);

        fetch(url.toString()).then(r => r.json()).then(data => {
            renderTable(data);
            document.getElementById('admin_view_field').value = admin_view === '1' ? '1' : '';
        }).catch(() => {});
    }

    const searchInput = document.getElementById('search_q');
    if (searchInput) searchInput.addEventListener('input', () => { clearTimeout(typingTimer); typingTimer = setTimeout(() => fetchPage(1), typeDelay); });
    const perInput = document.getElementById('per_page');
    if (perInput) { perInput.addEventListener('input', () => { clearTimeout(typingTimer); typingTimer = setTimeout(() => fetchPage(1), typeDelay); }); perInput.addEventListener('change', () => fetchPage(1)); }
    const adminChk = document.getElementById('admin_view_chk');
    // Ensure controls are hidden on initial load when admin view is not checked
    if (adminChk) {
        const searchEl = document.getElementById('search_q');
        const perLabel = document.getElementById('per_page_label');
        // Set initial hidden/shown state
        if (!adminChk.checked) {
            if (searchEl) searchEl.style.display = 'none';
            if (perLabel) perLabel.style.display = 'none';
        }
        // Reflect initial checkbox in hidden form field
        const adminField = document.getElementById('admin_view_field');
        if (adminField) adminField.value = adminChk.checked ? '1' : '';

        adminChk.addEventListener('change', () => {
            // toggle visibility and refresh page results when admin checkbox changes
            fetchPage(1);
            if (!adminChk.checked) {
                if (searchEl) searchEl.style.display = 'none';
                if (perLabel) perLabel.style.display = 'none';
            } else {
                if (searchEl) searchEl.style.display = '';
                if (perLabel) perLabel.style.display = '';
            }
            if (adminField) adminField.value = adminChk.checked ? '1' : '';
        });
    }

    // initial load
    fetchPage(currentPage);
})();