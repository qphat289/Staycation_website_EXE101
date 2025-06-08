// Main JavaScript for Horin

document.addEventListener('DOMContentLoaded', function() {
    // Không đặt lại ngôn ngữ mặc định để tôn trọng lựa chọn của người dùng
    // Chỉ đặt ngôn ngữ mặc định nếu chưa có giá trị
    if (!localStorage.getItem('language')) {
        localStorage.setItem('language', 'vi');
    }
    
    // Initialize Bootstrap dropdowns
    const dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    const dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    
    // Debug dropdown functionality
    const navbarDropdown = document.getElementById('navbarDropdown');
    if (navbarDropdown) {
        console.log('Avatar dropdown element found:', navbarDropdown);
        
        // Add click event listener for debugging
        navbarDropdown.addEventListener('click', function(e) {
            console.log('Avatar dropdown clicked!');
            console.log('Event target:', e.target);
            console.log('Bootstrap dropdown instance:', bootstrap.Dropdown.getInstance(navbarDropdown));
        });
        
        // Add shown/hidden event listeners
        navbarDropdown.addEventListener('shown.bs.dropdown', function () {
            console.log('Dropdown shown');
        });
        
        navbarDropdown.addEventListener('hidden.bs.dropdown', function () {
            console.log('Dropdown hidden');
        });
    } else {
        console.log('Avatar dropdown element not found!');
    }
    
    // Add Bootstrap validation for forms
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Function to preview image before upload
function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            document.getElementById(previewElement).src = e.target.result;
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Function to format currency
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}