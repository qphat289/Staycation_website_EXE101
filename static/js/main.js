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
    
    // Navbar scroll effect - áp dụng cho tất cả trang
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        function handleNavbarScroll() {
            if (window.scrollY > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            // Adjust text color after scroll state changes
            adjustNavbarTextColor();
        }
        
        // Xử lý khi scroll
        window.addEventListener('scroll', handleNavbarScroll);
        
        // Xử lý lần đầu load trang
        handleNavbarScroll();
    }
    
    // Auto-adjust navbar text color based on background brightness
    adjustNavbarTextColor();
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

// Function to calculate background brightness and adjust navbar text color automatically
function adjustNavbarTextColor() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    // Get computed background color
    const computedStyle = window.getComputedStyle(navbar);
    const backgroundColor = computedStyle.backgroundColor;
    
    // Function to parse RGB values from background color
    function getRGBValues(color) {
        const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        return match ? [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])] : [255, 255, 255];
    }
    
    // Calculate luminance (brightness) using the relative luminance formula
    function getLuminance(r, g, b) {
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }
    
    // Get RGB values
    const [r, g, b] = getRGBValues(backgroundColor);
    
    // Calculate luminance
    const luminance = getLuminance(r, g, b);
    
    // Set CSS custom properties for dynamic text color
    const root = document.documentElement;
    
    // Check if background is transparent or bright
    const isTransparent = backgroundColor === 'rgba(0, 0, 0, 0)' || backgroundColor === 'transparent';
    const isBright = luminance > 0.5;
    
    if (isTransparent || isBright) {
        // Bright/transparent background - use dark text
        root.style.setProperty('--navbar-text-color', 'black');
        root.style.setProperty('--navbar-hover-color', '#8bc34a');
        navbar.setAttribute('data-theme', 'light');
    } else {
        // Dark background - use light text  
        root.style.setProperty('--navbar-text-color', 'white');
        root.style.setProperty('--navbar-hover-color', '#f1b55f');
        navbar.setAttribute('data-theme', 'dark');
    }
    
    // Adjust language toggle styling
    const languageToggle = document.getElementById('languageToggle');
    if (languageToggle) {
        if (isTransparent || isBright) {
            languageToggle.style.background = 'rgba(255, 255, 255, 0.8)';
            languageToggle.style.border = '1px solid rgba(0, 0, 0, 0.2)';
            languageToggle.style.color = 'black';
        } else {
            languageToggle.style.background = 'rgba(255, 255, 255, 0.2)';
            languageToggle.style.border = '1px solid rgba(255, 255, 255, 0.3)';
            languageToggle.style.color = 'white';
        }
    }
    
    console.log(`Navbar background: ${backgroundColor}, Luminance: ${luminance.toFixed(3)}, Theme: ${navbar.getAttribute('data-theme')}`);
}