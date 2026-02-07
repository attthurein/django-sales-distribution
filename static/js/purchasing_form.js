document.addEventListener('DOMContentLoaded', function () {
    const itemsBody = document.getElementById('itemsBody');
    const addRowBtn = document.getElementById('addRow');
    const grandTotalEl = document.getElementById('grandTotal');

    function calculateRowTotal(row) {
        const qty = parseFloat(row.querySelector('.quantity-input').value) || 0;
        const cost = parseFloat(row.querySelector('.cost-input').value) || 0;
        const total = qty * cost;
        row.querySelector('.item-total').textContent = total.toFixed(2);
        calculateGrandTotal();
    }

    function calculateGrandTotal() {
        let total = 0;
        document.querySelectorAll('.item-row').forEach(row => {
            const rowTotal = parseFloat(row.querySelector('.item-total').textContent) || 0;
            total += rowTotal;
        });
        grandTotalEl.textContent = total.toFixed(2);
    }

    if (itemsBody) {
        itemsBody.addEventListener('input', function (e) {
            if (e.target.classList.contains('quantity-input') || e.target.classList.contains('cost-input')) {
                calculateRowTotal(e.target.closest('.item-row'));
            }
        });

        itemsBody.addEventListener('click', function (e) {
            if (e.target.classList.contains('remove-row')) {
                if (itemsBody.querySelectorAll('.item-row').length > 1) {
                    e.target.closest('.item-row').remove();
                    calculateGrandTotal();
                }
            }
        });
    }

    if (addRowBtn) {
        addRowBtn.addEventListener('click', function () {
            const firstRow = itemsBody.querySelector('.item-row');
            if (firstRow) {
                const newRow = firstRow.cloneNode(true);
                newRow.querySelectorAll('input').forEach(input => input.value = '');
                newRow.querySelector('.item-total').textContent = '0.00';
                itemsBody.appendChild(newRow);
            }
        });
    }
});
