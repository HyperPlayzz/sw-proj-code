// JavaScript for delete booking page
(() => {
    const apiUrl = window.CONFIG && window.CONFIG.apiBookingsUrl ? window.CONFIG.apiBookingsUrl : '/api/bookings';
    let currentPage = 1;
    let perPage = 10;
    let totalPages = 1;
    let totalResults = 0;
    const typeDelay = 300;
    let typingTimer = null;

    // Create and render the bookings table with delete buttons
    function renderDeleteTable(data) {
        const container = document.getElementById('delete-table-container');
        if (!data.bookings || data.bookings.length === 0) {
            container.innerHTML = '<p>No bookings found.</p>';
            document.getElementById('delete-pagination').innerHTML = '';
            return;
        }

        // Build the HTML table with booking data and delete buttons
        let html = '<table border="1" cellpadding="5"><tr><th>Desk</th><th>User</th><th>Start Time</th><th>End Time</th><th>Action</th></tr>';
        data.bookings.forEach(b => {
            html += '<tr>';
            html += '<td>' + (b.desk_number || '') + '</td>';
            html += '<td>' + (b.user_name || '') + '</td>';
            html += '<td>' + (b.start_time || '') + '</td>';
            html += '<td>' + (b.end_time || '') + '</td>';
            html += '<td><button class="delete-btn" data-booking-id="' + b.booking_id + '">Delete</button></td>';
            html += '</tr>';
        });
        html += '</table>';
        container.innerHTML = html;

        totalPages = data.total_pages;
        currentPage = data.page;
        totalResults = data.total || 0;
        renderDeletePagination();

        // Make delete buttons functional by submitting the delete form with the booking ID
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const bid = this.dataset.bookingId;
                document.getElementById('del_form_booking_id').value = bid;
                const admin_view = document.getElementById('admin_view_chk') ? (document.getElementById('admin_view_chk').checked ? '1' : '') : '';
                document.getElementById('del_admin_view_field').value = admin_view;
                document.getElementById('delete-form').submit();
            });
        });
    }

    // Render pagination controls based on current page and total pages, and wire up their click events to fetch the appropriate page of bookings
    function renderDeletePagination() {
        const el = document.getElementById('delete-pagination');
        if (totalPages <= 1) { el.innerHTML = ''; return; }
        let html = '';
        if (currentPage > 1) html += '<button id="prev-page">< Prev</button>';
        html += ' Page ' + currentPage + ' of ' + totalPages + ' (' + totalResults + ' results) ';
        if (currentPage < totalPages) html += '<button id="next-page">Next ></button>';
        el.innerHTML = html;
        const prev = document.getElementById('prev-page'); if (prev) prev.addEventListener('click', () => { fetchDeletePage(currentPage-1); });
        const next = document.getElementById('next-page'); if (next) next.addEventListener('click', () => { fetchDeletePage(currentPage+1); });
    }

    function fetchDeletePage(page=1) {
        const q = document.getElementById('search_q') ? document.getElementById('search_q').value : '';
        const admin_view = document.getElementById('admin_view_chk') ? (document.getElementById('admin_view_chk').checked ? '1' : '0') : '0';
        const per = document.getElementById('per_page') ? document.getElementById('per_page').value : perPage;
        const url = new URL(apiUrl, window.location.origin);
        url.searchParams.set('page', page);
        url.searchParams.set('per_page', per);
        url.searchParams.set('admin_view', admin_view);
        if (q) url.searchParams.set('q', q);
        fetch(url.toString()).then(r => r.json()).then(data => renderDeleteTable(data)).catch(() => {});
    }

    const searchInput = document.getElementById('search_q'); 
    if (searchInput) { 
        searchInput.addEventListener('input', () => { 
            clearTimeout(typingTimer); 
            typingTimer = setTimeout(() => fetchDeletePage(1), typeDelay); 
        }); 
    }

    const perInput = document.getElementById('per_page'); 
    if (perInput) { 
        perInput.addEventListener('input', () => { 
            clearTimeout(typingTimer); 
            typingTimer = setTimeout(() => fetchDeletePage(1), typeDelay); 
        }); 
        perInput.addEventListener('change', () => fetchDeletePage(1)); 
    }

    const adminChk = document.getElementById('admin_view_chk'); 
    if (adminChk) { 
        if (!adminChk.checked) { 
            const searchEl = document.getElementById('search_q'); 
            const perLabel = document.getElementById('per_page_label'); 
            if (searchEl) searchEl.style.display='none'; 
            if (perLabel) perLabel.style.display='none'; 
        } 
        adminChk.addEventListener('change', () => { 
            const searchEl = document.getElementById('search_q'); 
            const perLabel = document.getElementById('per_page_label'); 
            if (adminChk.checked) { 
                if (searchEl) searchEl.style.display=''; 
                if (perLabel) perLabel.style.display=''; 
                fetchDeletePage(1); 
            } else { 
                if (searchEl) searchEl.style.display='none'; 
                if (perLabel) perLabel.style.display='none'; 
                fetchDeletePage(1); 
            } 
        }); 
    }

    // initial fetch
    fetchDeletePage();
})();