document.addEventListener('DOMContentLoaded', function() {
    // Logo preview on file select
    var logoInput = document.getElementById('id_logo');
    var logoPreview = document.getElementById('logo-preview');
    var container = document.getElementById('logo-preview-container');
    var existingLogoUrl = container ? (container.getAttribute('data-existing-url') || '') : '';
    
    if (logoInput && logoPreview) {
        logoInput.addEventListener('change', function() {
            var file = this.files[0];
            if (file && file.type.startsWith('image/')) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    logoPreview.src = e.target.result;
                    logoPreview.classList.remove('d-none');
                };
                reader.readAsDataURL(file);
            } else if (file) {
                logoPreview.src = '';
                logoPreview.classList.add('d-none');
                alert('Please select an image file (PNG, JPG, etc.).');
            } else {
                if (existingLogoUrl) {
                    logoPreview.src = existingLogoUrl;
                    logoPreview.classList.remove('d-none');
                } else {
                    logoPreview.src = '';
                    logoPreview.classList.add('d-none');
                }
            }
        });
    }
});
