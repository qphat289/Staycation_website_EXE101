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
    
    // Initialize global search components
    initializeGlobalSearch();
});

// Function to initialize the global search components
function initializeGlobalSearch() {
    // Setup global search tabs
    const hourlyTab = document.getElementById('hourly-tab');
    const dailyTab = document.getElementById('daily-tab');
    
    if (hourlyTab && dailyTab) {
        // Initialize date/time placeholders
        initializeDateTimePlaceholders();
        
        // Initialize guest selectors
        initializeGuestSelectors();
        
        // Initialize location search
        initializeLocationSearch();
    }
}

// Function to switch between global search tabs (hourly and daily)
function switchTabGlobal(tabType) {
    // Remove active class from all tabs and forms
    document.querySelectorAll('.search-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.search-form').forEach(form => {
        form.classList.remove('active');
    });
    
    // Add active class to selected tab and form
    document.querySelector(`[data-tab="${tabType}"]`).classList.add('active');
    
    if (tabType === 'hourly') {
        document.getElementById('global-hourly-form').classList.add('active');
    } else {
        document.getElementById('global-daily-form').classList.add('active');
    }
}

// Function to initialize date/time placeholders
function initializeDateTimePlaceholders() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const timeInputs = document.querySelectorAll('input[type="time"]');
    
    dateInputs.forEach(input => {
        // Always ensure text is visible
        input.style.color = '#212529';
        
        input.addEventListener('change', function() {
            toggleCustomPlaceholder(this);
            console.log(`Date input ${this.id} changed to ${this.value}`);
            // Force text to be visible after change
            this.style.color = '#212529';
        });
        
        input.addEventListener('focus', function() {
            this.style.color = '#212529';
        });
        
        input.addEventListener('blur', function() {
            // Ensure text stays visible even after losing focus
            this.style.color = '#212529';
        });
        
        // Initial check
        toggleCustomPlaceholder(input);
    });
    
    timeInputs.forEach(input => {
        // Always ensure text is visible
        input.style.color = '#212529';
        
        input.addEventListener('change', function() {
            toggleCustomPlaceholder(this);
            console.log(`Time input ${this.id} changed to ${this.value}`);
            // Force text to be visible after change
            this.style.color = '#212529';
        });
        
        input.addEventListener('focus', function() {
            this.style.color = '#212529';
        });
        
        input.addEventListener('blur', function() {
            // Ensure text stays visible even after losing focus
            this.style.color = '#212529';
        });
        
        // Initial check
        toggleCustomPlaceholder(input);
    });
    
    // Fix for booking form inputs which might not have custom placeholders
    const bookingFormDateInputs = document.querySelectorAll('#booking-form input[type="date"], #booking-form input[type="time"]');
    bookingFormDateInputs.forEach(input => {
        input.style.color = '#212529';
    });
}

// Function to toggle custom placeholder visibility
function toggleCustomPlaceholder(input) {
    const placeholder = document.querySelector(`.custom-placeholder[data-for="${input.id}"]`);
    if (placeholder) {
        if (input.value) {
            placeholder.classList.add('hidden');
            input.style.color = '#212529';
            input.setAttribute('data-has-value', 'true');
            console.log(`${input.id}: Value set, showing actual value`);
        } else {
            placeholder.classList.remove('hidden');
            // Don't set color to transparent anymore - always show text
            input.style.color = '#212529';
            input.setAttribute('data-has-value', 'false');
            console.log(`${input.id}: No value, showing placeholder`);
        }
    }
}

// Function to initialize guest selectors for global search
function initializeGuestSelectors() {
    // Guest displays
    const guestDisplays = document.querySelectorAll('.guest-display');
    guestDisplays.forEach(display => {
        display.addEventListener('click', function() {
            const dropdownId = this.id.replace('guests-rooms', 'guest-dropdown');
            document.getElementById(dropdownId).classList.toggle('show');
        });
    });
    
    // Guest count buttons
    const decreaseButtons = document.querySelectorAll('.btn-decrease');
    const increaseButtons = document.querySelectorAll('.btn-increase');
    
    decreaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            const formType = this.getAttribute('data-form');
            updateGuestCount(formType, target, 'decrease');
        });
    });
    
    increaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            const formType = this.getAttribute('data-form');
            updateGuestCount(formType, target, 'increase');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.guest-selector') && !event.target.matches('.guest-display')) {
            document.querySelectorAll('.guest-dropdown').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
}

// Function to update guest counts
function updateGuestCount(formType, target, action) {
    const countElement = document.getElementById(`${formType}-${target}-count-${formType}`);
    const inputElement = document.getElementById(`${formType}-${target}-input-${formType}`);
    
    if (!countElement || !inputElement) return;
    
    let count = parseInt(countElement.textContent);
    
    if (action === 'increase') {
        count += 1;
    } else if (action === 'decrease') {
        if (target === 'adults' && count <= 1) {
            return; // Don't allow less than 1 adult
        }
        if (count > 0) count -= 1;
    }
    
    // Update the display and input value
    countElement.textContent = count;
    inputElement.value = count;
    
    // Update the guest display text
    updateGuestDisplay(formType);
    
    // Enable/disable decrease buttons based on count
    const decreaseButton = countElement.closest('.guest-controls').querySelector('.btn-decrease');
    if (decreaseButton) {
        if (target === 'adults') {
            decreaseButton.disabled = count <= 1;
        } else {
            decreaseButton.disabled = count <= 0;
        }
    }
}

// Function to update the guest display text
function updateGuestDisplay(formType) {
    const adultsCount = parseInt(document.getElementById(`${formType}-adults-count-${formType}`).textContent);
    const childrenCount = parseInt(document.getElementById(`${formType}-children-count-${formType}`).textContent);
    
    document.getElementById(`${formType}-guests-rooms-${formType}`).value = 
        `${adultsCount} người lớn, ${childrenCount} Trẻ em`;
}

// Function to initialize location search
function initializeLocationSearch() {
    const locationInputs = document.querySelectorAll('.location-input');
    
    locationInputs.forEach(input => {
        const dropdownId = input.id.replace('location', 'location-dropdown');
        const dropdown = document.getElementById(dropdownId);
        
        if (!dropdown) return;
        
        input.addEventListener('focus', function() {
            fetchLocations(this.value, dropdown);
            dropdown.classList.add('show');
        });
        
        input.addEventListener('input', function() {
            fetchLocations(this.value, dropdown);
            dropdown.classList.add('show');
        });
        
        // Close when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.location-selector') && !event.target.matches(input.id)) {
                dropdown.classList.remove('show');
            }
        });
    });
}

// Function to fetch locations from API
function fetchLocations(query, dropdownElement) {
    // Clear current options
    dropdownElement.innerHTML = '';
    
    if (query.trim().length < 2) {
        // Add default locations
        const defaultLocations = ['Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng', 'Nha Trang', 'Đà Lạt', 'Phú Quốc'];
        defaultLocations.forEach(location => {
            addLocationOption(location, dropdownElement);
        });
        return;
    }
    
    // In a real application, you would fetch from API
    // For demonstration, we'll use some mock data
    const mockData = [
        'Hà Nội', 'Hà Giang', 'Hà Tĩnh', 'Hà Nam',
        'TP. Hồ Chí Minh', 'Hồ Tây', 'Hồ Xuân Hương',
        'Đà Nẵng', 'Đà Lạt', 'Đắk Lắk', 'Đắk Nông',
        'Nha Trang', 'Ninh Bình', 'Ninh Thuận',
        'Phú Quốc', 'Phú Thọ', 'Phú Yên'
    ];
    
    const filteredLocations = mockData.filter(location => 
        location.toLowerCase().includes(query.toLowerCase())
    );
    
    filteredLocations.forEach(location => {
        addLocationOption(location, dropdownElement);
    });
}

// Function to add a location option to the dropdown
function addLocationOption(location, dropdownElement) {
    const option = document.createElement('div');
    option.className = 'location-option';
    option.textContent = location;
    
    option.addEventListener('click', function() {
        const inputId = dropdownElement.id.replace('dropdown', 'input');
        const input = document.getElementById(inputId.replace('-dropdown', ''));
        if (input) {
            input.value = location;
            dropdownElement.classList.remove('show');
        }
    });
    
    dropdownElement.appendChild(option);
}

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
    
    // User dropdown text color is handled by CSS based on body.homepage class
    // No JavaScript override needed - CSS specificity handles it
    
    console.log(`Navbar background: ${backgroundColor}, Luminance: ${luminance.toFixed(3)}, Theme: ${navbar.getAttribute('data-theme')}`);
}

// Hiển thị chi tiết tài khoản user trong modal
function viewUserDetails(element) {
    const fullName = element.getAttribute('data-full-name');
    const email = element.getAttribute('data-email');
    const phone = element.getAttribute('data-phone');
    const role = element.getAttribute('data-role');
    const status = element.getAttribute('data-status');

    document.getElementById('modalUserFullName').textContent = fullName;
    document.getElementById('modalUserEmail').textContent = email;
    document.getElementById('modalUserPhone').textContent = phone;
    document.getElementById('modalUserRole').textContent = role;
    document.getElementById('modalUserStatus').textContent = status;

    // Hiển thị modal
    const userDetailModal = new bootstrap.Modal(document.getElementById('userDetailModal'));
    userDetailModal.show();
}