// Main JavaScript for Horin

document.addEventListener('DOMContentLoaded', function() {
    // Không đặt lại ngôn ngữ mặc định để tôn trọng lựa chọn của người dùng
    // Chỉ đặt ngôn ngữ mặc định nếu chưa có giá trị
    if (!localStorage.getItem('language')) {
        localStorage.setItem('language', 'vi');
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