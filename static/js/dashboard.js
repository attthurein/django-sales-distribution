document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-stack]').forEach(function (table) {
        var headers = Array.from(table.querySelectorAll('thead th')).map(function (th) { return th.textContent.trim(); });
        table.querySelectorAll('tbody tr').forEach(function (tr) {
            Array.from(tr.children).forEach(function (td, i) {
                td.setAttribute('data-label', headers[i] || '');
            });
        });
    });
    var search = document.getElementById('expShopSearch');
    if (search) {
        search.addEventListener('input', function () {
            var q = this.value.toLowerCase();
            document.querySelectorAll('#expShopTable tbody tr').forEach(function (tr) {
                var text = tr.textContent.toLowerCase();
                tr.style.display = text.indexOf(q) !== -1 ? '' : 'none';
            });
        });
    }
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
