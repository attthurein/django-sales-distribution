/**
 * region_township.js
 * Handles cascading dropdowns for Country -> Region -> Township.
 * 
 * Expectations:
 * 1. Three select elements: #id_country, #id_region, #id_township
 * 2. #id_region options have 'data-country-id' attribute
 * 3. #id_township options have 'data-region-id' attribute
 */

document.addEventListener('DOMContentLoaded', function() {
    const countrySelect = document.getElementById('id_country');
    const regionSelect = document.getElementById('id_region');
    const townshipSelect = document.getElementById('id_township');

    // Store all original options
    let allRegionOptions = [];
    if (regionSelect) {
        allRegionOptions = Array.from(regionSelect.options);
    }

    let allTownshipOptions = [];
    if (townshipSelect) {
        allTownshipOptions = Array.from(townshipSelect.options);
    }

    // Function to filter regions based on selected country
    function filterRegions() {
        if (!countrySelect || !regionSelect) return;

        const selectedCountryId = countrySelect.value;
        const currentRegionId = regionSelect.value;

        // Clear current options
        regionSelect.innerHTML = '';

        // Add default/placeholder option
        const defaultOption = allRegionOptions.find(opt => !opt.value);
        if (defaultOption) {
            regionSelect.appendChild(defaultOption.cloneNode(true));
        }

        // Add matching options
        allRegionOptions.forEach(option => {
            if (option.value && option.dataset.countryId === selectedCountryId) {
                const newOption = option.cloneNode(true);
                regionSelect.appendChild(newOption);
            }
        });

        // Restore selection if valid, otherwise reset
        if (currentRegionId && Array.from(regionSelect.options).some(opt => opt.value === currentRegionId)) {
            regionSelect.value = currentRegionId;
        } else {
            regionSelect.value = '';
        }
        
        // Trigger township update since region might have changed
        filterTownships();
    }

    // Function to filter townships based on selected region
    function filterTownships() {
        if (!regionSelect || !townshipSelect) return;

        const selectedRegionId = regionSelect.value;
        const currentTownshipId = townshipSelect.value;

        // Clear current options
        townshipSelect.innerHTML = '';

        // Add default/placeholder option
        const defaultOption = allTownshipOptions.find(opt => !opt.value);
        if (defaultOption) {
            townshipSelect.appendChild(defaultOption.cloneNode(true));
        }

        // Add matching options
        allTownshipOptions.forEach(option => {
            if (option.value && option.dataset.regionId === selectedRegionId) {
                const newOption = option.cloneNode(true);
                townshipSelect.appendChild(newOption);
            }
        });

        // Restore selection if valid
        if (currentTownshipId && Array.from(townshipSelect.options).some(opt => opt.value === currentTownshipId)) {
            townshipSelect.value = currentTownshipId;
        } else {
            townshipSelect.value = '';
        }
    }

    // Initialize
    if (countrySelect && regionSelect) {
        // Initial filter on load
        filterRegions();
        
        // Add change listener
        countrySelect.addEventListener('change', filterRegions);
    }
    
    if (regionSelect && townshipSelect) {
        // Initial filter (called by filterRegions, but good to have explicit call if country not present)
        if (!countrySelect) {
            filterTownships();
        }
        
        regionSelect.addEventListener('change', filterTownships);
    }
});
