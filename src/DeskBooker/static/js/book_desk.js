document.addEventListener('DOMContentLoaded', function() {
    const siteSelect = document.getElementById('site-select');
    const deskSelect = document.getElementById('desk-select');

    // Populate desk options based on selected site
    siteSelect.addEventListener('change', function() {
        const siteId = this.value;
        deskSelect.innerHTML = '<option value="">Select a desk</option>';

        window.ALL_DESKS.forEach(desk => {
            if (String(desk.site_id) === String(siteId)) {
                const option = document.createElement('option');
                option.value = desk.id;
                option.text = desk.desk_number;
                deskSelect.add(option);
            }
        });
    });
});