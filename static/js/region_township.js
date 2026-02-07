document.addEventListener('DOMContentLoaded', function() {
    var regionSelect = document.getElementById('id_region');
    var townshipSelect = document.getElementById('id_township');
    
    if (!regionSelect || !townshipSelect) return;
    
    // Support both direct children options and options within optgroups if structure changes,
    // but current template uses direct options or loop.
    // The template has: <option value="..." data-region-id="...">...</option>
    var townshipOptions = Array.from(townshipSelect.querySelectorAll('option'));

    function filterTownships() {
        var regionId = regionSelect.value;
        townshipOptions.forEach(function(opt) {
            var regionAttr = opt.getAttribute('data-region-id');
            // Show option if:
            // 1. It has no data-region-id (like the empty "Select Township" option)
            // 2. No region is selected (regionId is empty) - OPTIONAL: usually we hide townships if no region. 
            //    But here let's follow logic: if no region, maybe show all or none. 
            //    User said "region selected but all shown".
            //    Let's assume: if regionId is present, only show matches. If regionId empty, show all (or hide specific ones).
            
            // Logic:
            // - If opt has no data-region-id (e.g. placeholder), always show.
            // - If regionId is empty, show all (or keep previous behavior).
            // - If regionId is set, show only matches.
            
            var isPlaceholder = !regionAttr;
            var show = isPlaceholder || !regionId || regionAttr === regionId;
            
            if (show) {
                opt.removeAttribute('hidden');
                opt.style.display = '';
                opt.disabled = false;
            } else {
                opt.setAttribute('hidden', 'hidden');
                opt.style.display = 'none';
                opt.disabled = true;
            }
        });
        
        // If current selection is hidden, reset it
        var curVal = townshipSelect.value;
        if (curVal) {
            var curOpt = townshipSelect.querySelector('option[value="' + curVal + '"]');
            if (curOpt && curOpt.disabled) {
                townshipSelect.value = '';
            }
        }
    }

    regionSelect.addEventListener('change', filterTownships);
    // Initial filter
    filterTownships();
});
