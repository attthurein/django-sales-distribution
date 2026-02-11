/**
 * Enhanced Order Form Logic
 * Handles dynamic item rows, price fetching, stock hints, and live total calculation.
 */

(function () {
    // Configuration provided by the template
    const config = window.orderFormConfig || {
        itemCount: 0,
        productsUrl: '', // URL to fetch prices
        isLocked: false,
        qtyPlaceholder: 'Qty'
    };

    if (config.isLocked) return;

    // Get the product options HTML template
    let productOptions = '';
    const templateEl = document.getElementById('productOptionsTemplate');
    if (templateEl) {
        productOptions = templateEl.innerHTML;
    } else {
        // Fallback for create page where template might be the first select
        const firstSelect = document.querySelector('.product-select');
        if (firstSelect) {
            productOptions = firstSelect.innerHTML;
        }
    }

    let itemCount = config.itemCount;
    let productPrices = {}; // Store product prices

    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    function calculateRowTotal(row) {
        const sel = row.querySelector('.product-select');
        const qty = row.querySelector('.qty-input');
        const totalEl = row.querySelector('.row-total');

        if (!sel || !qty) return 0;

        const productId = sel.value;
        const quantity = parseInt(qty.value) || 0;
        const price = productPrices[productId] || 0;
        const total = price * quantity;

        if (totalEl) {
            totalEl.textContent = formatCurrency(total);
        }

        return total;
    }

    function updateGrandTotal() {
        let subtotal = 0;
        document.querySelectorAll('.item-row').forEach(row => {
            subtotal += calculateRowTotal(row);
        });

        const discountEl = document.querySelector('[name="discount_amount"]');
        const discount = parseFloat(discountEl?.value) || 0;
        const grandTotal = Math.max(0, subtotal - discount);

        // Update summary display
        const subtotalEl = document.getElementById('orderSubtotal');
        const discountDisplayEl = document.getElementById('orderDiscount');
        const grandTotalEl = document.getElementById('orderGrandTotal');

        if (subtotalEl) subtotalEl.textContent = formatCurrency(subtotal);
        if (discountDisplayEl) discountDisplayEl.textContent = formatCurrency(discount);
        if (grandTotalEl) grandTotalEl.textContent = formatCurrency(grandTotal);
    }

    function updateStockHint(row) {
        const sel = row.querySelector('.product-select');
        const qty = row.querySelector('.qty-input');
        const hint = row.querySelector('.stock-hint');

        if (!sel || !qty || !hint) return;

        const opt = sel.options[sel.selectedIndex];
        const stock = opt && opt.dataset.stock ? parseInt(opt.dataset.stock) : null;

        if (stock !== null) {
            const qtyVal = parseInt(qty.value) || 0;
            hint.innerHTML = `<i class="bi bi-box-seam"></i> Available: ${stock}`;

            if (qtyVal > stock) {
                qty.classList.add('is-invalid');
                hint.classList.add('text-danger');
                hint.classList.remove('text-success');
                hint.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Insufficient stock! (Available: ${stock})`;
            } else if (qtyVal > 0 && qtyVal <= stock) {
                qty.classList.remove('is-invalid');
                qty.classList.add('is-valid');
                hint.classList.remove('text-danger');
                hint.classList.add('text-success');
            } else {
                qty.classList.remove('is-invalid', 'is-valid');
                hint.classList.remove('text-danger', 'text-success');
            }
        } else {
            hint.textContent = '';
            qty.classList.remove('is-invalid', 'is-valid');
            hint.classList.remove('text-danger', 'text-success');
        }

        updateGrandTotal();
    }

    function createRow() {
        const row = document.createElement('div');
        row.className = 'row mb-3 align-items-start item-row p-3 bg-light rounded border';
        row.innerHTML = `
            <div class="col-md-5">
                <label class="form-label small fw-semibold d-md-none">Product</label>
                <select name="product_id" class="form-select product-select" data-item="${itemCount}">
                    ${productOptions}
                </select>
                <small class="text-muted stock-hint d-block mt-1"></small>
            </div>
            <div class="col-md-2">
                <label class="form-label small fw-semibold d-md-none">Quantity</label>
                <input type="number" name="quantity" class="form-control qty-input" min="1" placeholder="${config.qtyPlaceholder}" value="">
            </div>
            <div class="col-md-3">
                <label class="form-label small fw-semibold d-md-none">Total</label>
                <div class="input-group">
                    <span class="input-group-text bg-white"><i class="bi bi-currency-dollar"></i></span>
                    <input type="text" class="form-control row-total bg-white" value="0" readonly>
                </div>
            </div>
            <div class="col-md-2 text-end">
                <label class="form-label small invisible d-md-none">Remove</label>
                <button type="button" class="btn btn-outline-danger remove-item" title="Remove">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;

        const sel = row.querySelector('.product-select');
        const qty = row.querySelector('.qty-input');
        const removeBtn = row.querySelector('.remove-item');

        sel.addEventListener('change', () => {
            updateStockHint(row);
            updateGrandTotal();
        });
        qty.addEventListener('input', () => {
            updateStockHint(row);
            updateGrandTotal();
        });
        removeBtn.addEventListener('click', () => {
            row.style.transition = 'opacity 0.3s';
            row.style.opacity = '0';
            setTimeout(() => {
                row.remove();
                checkRemoveButtons();
                updateGrandTotal();
            }, 300);
        });

        return row;
    }

    function checkRemoveButtons() {
        const rows = document.querySelectorAll('.item-row');
        const removeBtns = document.querySelectorAll('.remove-item');
        if (rows.length <= 1) {
            removeBtns.forEach(btn => btn.classList.add('d-none'));
        } else {
            removeBtns.forEach(btn => btn.classList.remove('d-none'));
        }
    }

    // Initialize Event Listeners
    const addItemBtn = document.getElementById('addItem');
    if (addItemBtn) {
        addItemBtn.onclick = function () {
            const row = createRow();
            document.getElementById('items').appendChild(row);
            itemCount++;
            checkRemoveButtons();
            updatePrices(); // Apply current customer prices to new row

            // Add animation
            row.style.opacity = '0';
            setTimeout(() => {
                row.style.transition = 'opacity 0.3s';
                row.style.opacity = '1';
            }, 10);
        };
    }

    let customerEl = document.getElementById('customer_id');
    if (!customerEl) {
        customerEl = document.getElementById('id_customer');
    }

    function updatePrices() {
        if (!customerEl) return;

        const cid = customerEl.value;
        const loading = document.getElementById('priceLoading');

        if (!cid) {
            if (loading) loading.classList.add('d-none');
            return;
        }

        if (loading) loading.classList.remove('d-none');

        fetch(config.productsUrl + '?customer_id=' + cid)
            .then(r => r.json())
            .then(data => {
                productPrices = data.prices || {};

                document.querySelectorAll('.product-select').forEach(sel => {
                    const currentVal = sel.value;
                    Array.from(sel.options).forEach(opt => {
                        if (opt.value && productPrices[opt.value]) {
                            let text = opt.text;
                            text = text.replace(/ \([\d,]+ MMK\)$/, '');
                            opt.text = text + ' (' + formatCurrency(productPrices[opt.value]) + ' MMK)';
                        }
                    });
                    sel.value = currentVal;
                });

                updateGrandTotal();
            })
            .catch(err => console.error('Error fetching prices:', err))
            .finally(() => {
                if (loading) loading.classList.add('d-none');
            });
    }

    if (customerEl) {
        customerEl.addEventListener('change', updatePrices);
        if (customerEl.value) {
            updatePrices();
        }
    }

    // Discount field listener
    const discountEl = document.querySelector('[name="discount_amount"]');
    if (discountEl) {
        discountEl.addEventListener('input', updateGrandTotal);
    }

    // Global delegation for existing rows
    document.getElementById('items')?.addEventListener('click', function (e) {
        if (e.target.closest('.remove-item')) {
            const row = e.target.closest('.item-row');
            if (row) {
                row.style.transition = 'opacity 0.3s';
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                    checkRemoveButtons();
                    updateGrandTotal();
                }, 300);
            }
        }
    });

    document.querySelectorAll('.product-select').forEach(sel => {
        sel.addEventListener('change', () => {
            updateStockHint(sel.closest('.item-row'));
            updateGrandTotal();
        });
    });

    document.querySelectorAll('.qty-input').forEach(inp => {
        inp.addEventListener('input', () => {
            updateStockHint(inp.closest('.item-row'));
            updateGrandTotal();
        });
    });

    // Initial check
    checkRemoveButtons();
    updateGrandTotal();

    // Form submit loading state
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', function () {
            const btn = document.getElementById('submitBtn');
            if (btn) {
                btn.disabled = true;
                btn.classList.add('btn-loading');
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing...';
            }
        });
    }

})();
