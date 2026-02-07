/**
 * Order Form Logic
 * Handles dynamic item rows, price fetching, and stock hints.
 */

(function() {
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

    function updateStockHint(row) {
        const sel = row.querySelector('.product-select');
        const qty = row.querySelector('.qty-input');
        const hint = row.querySelector('.stock-hint');
        
        if (!sel || !qty || !hint) return;
        
        const opt = sel.options[sel.selectedIndex];
        const stock = opt && opt.dataset.stock ? parseInt(opt.dataset.stock) : null;
        
        if (stock !== null) {
            hint.textContent = 'Available: ' + stock;
            
            if (qty.value && parseInt(qty.value) > stock) {
                qty.classList.add('is-invalid');
                hint.classList.add('text-danger');
            } else {
                qty.classList.remove('is-invalid');
                hint.classList.remove('text-danger');
            }
        } else {
            hint.textContent = '';
            qty.classList.remove('is-invalid');
            hint.classList.remove('text-danger');
        }
    }

    function createRow() {
        const row = document.createElement('div');
        row.className = 'row mb-2 align-items-start item-row';
        row.innerHTML = `
            <div class="col-md-7">
                <label class="form-label small d-md-none">Product</label>
                <select name="product_id" class="form-select product-select" data-item="${itemCount}">
                    ${productOptions}
                </select>
                <small class="text-muted stock-hint d-block mt-1"></small>
            </div>
            <div class="col-md-3">
                <label class="form-label small d-md-none">Quantity</label>
                <input type="number" name="quantity" class="form-control qty-input" min="1" placeholder="${config.qtyPlaceholder}" value="">
            </div>
            <div class="col-md-2">
                <label class="form-label small d-md-none invisible">Remove</label>
                <button type="button" class="btn btn-outline-danger remove-item" title="Remove">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        
        const sel = row.querySelector('.product-select');
        const qty = row.querySelector('.qty-input');
        const removeBtn = row.querySelector('.remove-item');
        
        sel.addEventListener('change', () => updateStockHint(row));
        qty.addEventListener('input', () => updateStockHint(row));
        removeBtn.addEventListener('click', () => {
            row.remove();
            checkRemoveButtons();
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
        addItemBtn.onclick = function() {
            const row = createRow();
            document.getElementById('items').appendChild(row);
            itemCount++;
            checkRemoveButtons();
            updatePrices(); // Apply current customer prices to new row
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
                document.querySelectorAll('.product-select').forEach(sel => {
                    const currentVal = sel.value;
                    Array.from(sel.options).forEach(opt => {
                        if (opt.value && data.prices && data.prices[opt.value]) {
                            let text = opt.text;
                            text = text.replace(/ \([\d,]+ MMK\)$/, '');
                            opt.text = text + ' (' + data.prices[opt.value] + ' MMK)';
                        }
                    });
                    sel.value = currentVal;
                });
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
    
    // Global delegation for existing rows
    document.getElementById('items').addEventListener('click', function(e) {
        if (e.target.closest('.remove-item')) {
            const row = e.target.closest('.item-row');
            if (row) {
                row.remove();
                checkRemoveButtons();
            }
        }
    });

    document.querySelectorAll('.product-select').forEach(sel => {
        sel.addEventListener('change', () => updateStockHint(sel.closest('.item-row')));
    });

    document.querySelectorAll('.qty-input').forEach(inp => {
        inp.addEventListener('input', () => updateStockHint(inp.closest('.item-row')));
    });
    
    // Initial check
    checkRemoveButtons();

    // Form submit loading state
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', function() {
            const btn = document.getElementById('submitBtn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';
            }
        });
    }

})();
