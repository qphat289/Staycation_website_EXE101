// Main JavaScript for Homi

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
        
        // Initialize form validation
        initializeSearchFormValidation();
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
    return new Intl.NumberFormat('vi-VN').format(parseFloat(amount)) + ' VND';
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

// Daily Date Time Selector for Home page
function setupDailyDateTimeSelector() {
    console.log('Setting up daily date time selector for home page...');
    
    const checkinInput = document.getElementById('datetime-daily');
    const checkoutInput = document.getElementById('checkout-display-daily');
    const calendarDropdown = document.getElementById('datetime-dropdown-daily');
    
    if (!checkinInput || !checkoutInput || !calendarDropdown) {
        console.log('Daily form elements not found:', {
            checkinInput: !!checkinInput,
            checkoutInput: !!checkoutInput, 
            calendarDropdown: !!calendarDropdown
        });
        return;
    }
    
    console.log('Daily form elements found successfully');
    
    let isDropdownOpen = false;
    let selectedCheckin = null;
    let selectedCheckout = null;
    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();
    
    const monthNames = [
        'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
        'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
    ];
    
    // Show/hide dropdown
    function toggleDropdown() {
        console.log('Toggling dropdown, current state:', isDropdownOpen);
        isDropdownOpen = !isDropdownOpen;
        calendarDropdown.style.display = isDropdownOpen ? 'block' : 'none';
        if (isDropdownOpen) {
            renderCalendar();
        }
    }
    
    // Render calendar for both months
    function renderCalendar() {
        console.log('Rendering calendar...');
        const calendarDays1 = document.getElementById('calendar-days-daily-1');
        const calendarDays2 = document.getElementById('calendar-days-daily-2');
        const calendarTitle1 = document.getElementById('calendar-title-daily-1');
        const calendarTitle2 = document.getElementById('calendar-title-daily-2');
        
        if (!calendarDays1 || !calendarDays2 || !calendarTitle1 || !calendarTitle2) {
            console.log('Calendar elements not found');
            return;
        }
        
        // Render first month
        renderMonth(calendarDays1, calendarTitle1, currentMonth, currentYear);
        
        // Render second month
        let nextMonth = currentMonth + 1;
        let nextYear = currentYear;
        if (nextMonth > 11) {
            nextMonth = 0;
            nextYear++;
        }
        renderMonth(calendarDays2, calendarTitle2, nextMonth, nextYear);
    }
    
    // Render individual month
    function renderMonth(calendarDays, calendarTitle, month, year) {
        // Update month title
        calendarTitle.textContent = `${monthNames[month]} ${year}`;
        
        // Clear existing days
        calendarDays.innerHTML = '';
        
        // Get first day of month and number of days
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // Add empty cells for days before first day of month
        for (let i = 0; i < firstDay; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'calendar-day empty';
            calendarDays.appendChild(emptyCell);
        }
        
        // Add days of month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayCell = document.createElement('div');
            dayCell.className = 'calendar-day';
            dayCell.textContent = day;
            
            const cellDate = new Date(year, month, day);
            cellDate.setHours(0, 0, 0, 0);
            
            // Disable past dates
            if (cellDate < today) {
                dayCell.classList.add('disabled');
            } else {
                dayCell.addEventListener('click', (e) => {
                    e.stopPropagation();
                    selectDate(cellDate);
                });
                
                // Highlight selected dates
                if (selectedCheckin && cellDate.getTime() === selectedCheckin.getTime()) {
                    dayCell.classList.add('selected', 'checkin');
                }
                if (selectedCheckout && cellDate.getTime() === selectedCheckout.getTime()) {
                    dayCell.classList.add('selected', 'checkout');
                }
                
                // Highlight dates in range
                if (selectedCheckin && selectedCheckout && 
                    cellDate > selectedCheckin && cellDate < selectedCheckout) {
                    dayCell.classList.add('in-range');
                }
            }
            
            calendarDays.appendChild(dayCell);
        }
    }
    
    // Select date
    function selectDate(date) {
        console.log('Selecting date:', date);
        
        if (!selectedCheckin || (selectedCheckin && selectedCheckout)) {
            // First selection or reset
            selectedCheckin = date;
            selectedCheckout = null;
            checkinInput.value = formatDate(date);
            checkoutInput.value = 'Chọn ngày';
            
            // Update hidden inputs
            document.getElementById('checkin-date-daily').value = formatDateForInput(date);
            document.getElementById('checkout-date-daily').value = '';
            
            // Re-render calendar to show selection but keep dropdown open
            renderCalendar();
        } else if (date > selectedCheckin) {
            // Second selection (checkout) - keep dropdown open until Apply is clicked
            selectedCheckout = date;
            checkoutInput.value = formatDate(date);
            
            // Update hidden input
            document.getElementById('checkout-date-daily').value = formatDateForInput(date);
            
            // Re-render calendar to show selection but keep dropdown open
            renderCalendar();
        } else {
            // New checkin date
            selectedCheckin = date;
            selectedCheckout = null;
            checkinInput.value = formatDate(date);
            checkoutInput.value = 'Chọn ngày';
            
            // Update hidden inputs
            document.getElementById('checkin-date-daily').value = formatDateForInput(date);
            document.getElementById('checkout-date-daily').value = '';
            
            // Re-render calendar to show selection but keep dropdown open
            renderCalendar();
        }
    }
    
    // Format date for display
    function formatDate(date) {
        const dayNames = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];
        const dayName = dayNames[date.getDay()];
        const day = date.getDate();
        const month = date.getMonth() + 1;
        return `${dayName} - ${day} tháng ${month}`;
    }
    
    // Format date for input (YYYY-MM-DD)
    function formatDateForInput(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // Navigation
    const prevBtn = document.getElementById('prev-month-daily');
    const nextBtn = document.getElementById('next-month-daily');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentMonth === 0) {
                currentMonth = 11;
                currentYear--;
            } else {
                currentMonth--;
            }
            renderCalendar();
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentMonth === 11) {
                currentMonth = 0;
                currentYear++;
            } else {
                currentMonth++;
            }
            renderCalendar();
        });
    }
    
    // Apply button
    const applyBtn = document.getElementById('apply-dates-daily');
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            toggleDropdown();
        });
    }
    
    // Clear button
    const clearBtn = document.getElementById('clear-dates-daily');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            selectedCheckin = null;
            selectedCheckout = null;
            checkinInput.value = 'Chọn ngày';
            checkoutInput.value = 'Chọn ngày';
            
            // Update hidden inputs
            document.getElementById('checkin-date-daily').value = '';
            document.getElementById('checkout-date-daily').value = '';
            
            renderCalendar();
        });
    }
    
    // Event listeners for inputs
    checkinInput.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Checkin input clicked');
        toggleDropdown();
    });
    
    checkoutInput.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Checkout input clicked');
        toggleDropdown();
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!calendarDropdown.contains(e.target) && 
            !checkinInput.contains(e.target) && 
            !checkoutInput.contains(e.target)) {
            if (isDropdownOpen) {
                toggleDropdown();
            }
        }
    });
}

// Daily Date Time Selector for Global (base.html)
function setupGlobalDailyDateTimeSelector() {
    console.log('Setting up global daily date time selector...');
    
    const checkinInput = document.getElementById('global-datetime-daily');
    const checkoutInput = document.getElementById('global-checkout-display-daily');
    const calendarDropdown = document.getElementById('global-datetime-dropdown-daily');
    
    if (!checkinInput || !checkoutInput || !calendarDropdown) {
        console.log('Global daily form elements not found:', {
            checkinInput: !!checkinInput,
            checkoutInput: !!checkoutInput,
            calendarDropdown: !!calendarDropdown
        });
        return;
    }
    
    console.log('Global daily form elements found successfully');
    
    let isDropdownOpen = false;
    let selectedCheckin = null;
    let selectedCheckout = null;
    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();
    
    const monthNames = [
        'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
        'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
    ];
    
    // Show/hide dropdown
    function toggleDropdown() {
        console.log('Toggling global dropdown, current state:', isDropdownOpen);
        isDropdownOpen = !isDropdownOpen;
        calendarDropdown.style.display = isDropdownOpen ? 'block' : 'none';
        if (isDropdownOpen) {
            renderCalendar();
        }
    }
    
    // Render calendar for both months
    function renderCalendar() {
        console.log('Rendering global calendar...');
        const calendarDays1 = document.getElementById('global-calendar-days-daily-1');
        const calendarDays2 = document.getElementById('global-calendar-days-daily-2');
        const calendarTitle1 = document.getElementById('global-calendar-title-daily-1');
        const calendarTitle2 = document.getElementById('global-calendar-title-daily-2');
        
        if (!calendarDays1 || !calendarDays2 || !calendarTitle1 || !calendarTitle2) {
            console.log('Global calendar elements not found');
            return;
        }
        
        // Render first month
        renderMonth(calendarDays1, calendarTitle1, currentMonth, currentYear);
        
        // Render second month
        let nextMonth = currentMonth + 1;
        let nextYear = currentYear;
        if (nextMonth > 11) {
            nextMonth = 0;
            nextYear++;
        }
        renderMonth(calendarDays2, calendarTitle2, nextMonth, nextYear);
    }
    
    // Render individual month
    function renderMonth(calendarDays, calendarTitle, month, year) {
        // Update month title
        calendarTitle.textContent = `${monthNames[month]} ${year}`;
        
        // Clear existing days
        calendarDays.innerHTML = '';
        
        // Get first day of month and number of days
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // Add empty cells for days before first day of month
        for (let i = 0; i < firstDay; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'calendar-day empty';
            calendarDays.appendChild(emptyCell);
        }
        
        // Add days of month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayCell = document.createElement('div');
            dayCell.className = 'calendar-day';
            dayCell.textContent = day;
            
            const cellDate = new Date(year, month, day);
            cellDate.setHours(0, 0, 0, 0);
            
            // Disable past dates
            if (cellDate < today) {
                dayCell.classList.add('disabled');
            } else {
                dayCell.addEventListener('click', (e) => {
                    e.stopPropagation();
                    selectDate(cellDate);
                });
                
                // Highlight selected dates
                if (selectedCheckin && cellDate.getTime() === selectedCheckin.getTime()) {
                    dayCell.classList.add('selected', 'checkin');
                }
                if (selectedCheckout && cellDate.getTime() === selectedCheckout.getTime()) {
                    dayCell.classList.add('selected', 'checkout');
                }
                
                // Highlight dates in range
                if (selectedCheckin && selectedCheckout && 
                    cellDate > selectedCheckin && cellDate < selectedCheckout) {
                    dayCell.classList.add('in-range');
                }
            }
            
            calendarDays.appendChild(dayCell);
        }
    }
    
    // Select date
    function selectDate(date) {
        console.log('Selecting global date:', date);
        
        if (!selectedCheckin || (selectedCheckin && selectedCheckout)) {
            // First selection or reset
            selectedCheckin = date;
            selectedCheckout = null;
            checkinInput.value = formatDate(date);
            checkoutInput.value = 'Chọn ngày';
            
            // Update hidden inputs
            document.getElementById('global-checkin-date-daily').value = formatDateForInput(date);
            document.getElementById('global-checkout-date-daily').value = '';
            
            // Re-render calendar to show selection but keep dropdown open
            renderCalendar();
        } else if (date > selectedCheckin) {
            // Second selection (checkout) - keep dropdown open until Apply is clicked
            selectedCheckout = date;
            checkoutInput.value = formatDate(date);
            
            // Update hidden input
            document.getElementById('global-checkout-date-daily').value = formatDateForInput(date);
            
            // Re-render calendar to show selection but keep dropdown open
            renderCalendar();
        } else {
            // New checkin date
            selectedCheckin = date;
            selectedCheckout = null;
            checkinInput.value = formatDate(date);
            checkoutInput.value = 'Chọn ngày';
            
            // Update hidden inputs
            document.getElementById('global-checkin-date-daily').value = formatDateForInput(date);
            document.getElementById('global-checkout-date-daily').value = '';
            
            // Re-render calendar to show selection but keep dropdown open
            renderCalendar();
        }
    }
    
    // Format date for display
    function formatDate(date) {
        const dayNames = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];
        const dayName = dayNames[date.getDay()];
        const day = date.getDate();
        const month = date.getMonth() + 1;
        return `${dayName} - ${day} tháng ${month}`;
    }
    
    // Format date for input (YYYY-MM-DD)
    function formatDateForInput(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // Navigation
    const prevBtn = document.getElementById('global-prev-month-daily');
    const nextBtn = document.getElementById('global-next-month-daily');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentMonth === 0) {
                currentMonth = 11;
                currentYear--;
            } else {
                currentMonth--;
            }
            renderCalendar();
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentMonth === 11) {
                currentMonth = 0;
                currentYear++;
            } else {
                currentMonth++;
            }
            renderCalendar();
        });
    }
    
    // Apply button
    const applyBtn = document.getElementById('global-apply-dates-daily');
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            toggleDropdown();
        });
    }
    
    // Clear button
    const clearBtn = document.getElementById('global-clear-dates-daily');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            selectedCheckin = null;
            selectedCheckout = null;
            checkinInput.value = 'Chọn ngày';
            checkoutInput.value = 'Chọn ngày';
            
            // Update hidden inputs
            document.getElementById('global-checkin-date-daily').value = '';
            document.getElementById('global-checkout-date-daily').value = '';
            
            renderCalendar();
        });
    }
    
    // Event listeners for inputs
    checkinInput.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Global checkin input clicked');
        toggleDropdown();
    });
    
    checkoutInput.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Global checkout input clicked');
        toggleDropdown();
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!calendarDropdown.contains(e.target) && 
            !checkinInput.contains(e.target) && 
            !checkoutInput.contains(e.target)) {
            if (isDropdownOpen) {
                toggleDropdown();
            }
        }
    });
}

// Initialize daily calendar when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing daily calendars...');
    
    // Small delay to ensure all elements are rendered
    setTimeout(() => {
        setupDailyDateTimeSelector();
        setupGlobalDailyDateTimeSelector();
    }, 100);
});

// Function to initialize search form validation
function initializeSearchFormValidation() {
    // Get form elements
    const hourlyForm = document.getElementById('global-hourly-form');
    const dailyForm = document.getElementById('global-daily-form');
    
    // Add validation for hourly form
    if (hourlyForm) {
        hourlyForm.addEventListener('submit', function(e) {
            const checkinDate = document.getElementById('global-checkin-date-hourly').value;
            const checkinTime = document.getElementById('global-checkin-time-hourly').value;
            const hoursDuration = document.getElementById('global-hours-duration-hourly').value;
            
            if (!checkinDate || !checkinTime || !hoursDuration) {
                e.preventDefault();
                showNotification('error', 'Vui lòng chọn ngày giờ');
                return false;
            }
        });
    }
    
    // Add validation for daily form
    if (dailyForm) {
        dailyForm.addEventListener('submit', function(e) {
            const checkinDate = document.getElementById('global-checkin-date-daily').value;
            const checkoutDate = document.getElementById('global-checkout-date-daily').value;
            
            if (!checkinDate || !checkoutDate) {
                e.preventDefault();
                showNotification('error', 'Vui lòng chọn ngày');
                return false;
            }
        });
    }
    
    // Update placeholders based on current values
    updateSearchPlaceholders();
}

// Function to update search placeholders
function updateSearchPlaceholders() {
    // Update hourly form placeholders
    const hourlyCheckinDisplay = document.getElementById('global-datetime-hourly');
    const hourlyCheckoutDisplay = document.getElementById('global-checkout-display-hourly');
    const hourlyCheckinDate = document.getElementById('global-checkin-date-hourly').value;
    const hourlyCheckinTime = document.getElementById('global-checkin-time-hourly').value;
    const hourlyDuration = document.getElementById('global-hours-duration-hourly').value;
    
    if (hourlyCheckinDisplay) {
        if (hourlyCheckinDate && hourlyCheckinTime && hourlyDuration) {
            // Format the display value
            const date = new Date(hourlyCheckinDate);
            const dayNames = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];
            const dayName = dayNames[date.getDay()];
            const day = date.getDate();
            const month = date.getMonth() + 1;
            const year = date.getFullYear();
            
            hourlyCheckinDisplay.value = `${dayName} - ${day} tháng ${month} - ${hourlyCheckinTime}`;
            
            // Calculate checkout time
            const checkinHour = parseInt(hourlyCheckinTime.split(':')[0]);
            const duration = parseInt(hourlyDuration);
            let checkoutHour = checkinHour + duration;
            let checkoutDate = new Date(date);
            
            if (checkoutHour >= 24) {
                checkoutHour -= 24;
                checkoutDate.setDate(checkoutDate.getDate() + 1);
            }
            
            const checkoutDayNames = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];
            const checkoutDayName = checkoutDayNames[checkoutDate.getDay()];
            const checkoutDay = checkoutDate.getDate();
            const checkoutMonth = checkoutDate.getMonth() + 1;
            
            hourlyCheckoutDisplay.value = `${checkoutDayName} - ${checkoutDay} tháng ${checkoutMonth} - ${checkoutHour.toString().padStart(2, '0')}:00`;
        } else {
            hourlyCheckinDisplay.value = 'Hãy chọn ngày và giờ';
            hourlyCheckoutDisplay.value = 'Hãy chọn ngày và giờ';
        }
    }
    
    // Update daily form placeholders
    const dailyCheckinDisplay = document.getElementById('global-datetime-daily');
    const dailyCheckoutDisplay = document.getElementById('global-checkout-display-daily');
    const dailyCheckinDate = document.getElementById('global-checkin-date-daily').value;
    const dailyCheckoutDate = document.getElementById('global-checkout-date-daily').value;
    
    if (dailyCheckinDisplay) {
        if (dailyCheckinDate) {
            const date = new Date(dailyCheckinDate);
            const dayNames = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];
            const dayName = dayNames[date.getDay()];
            const day = date.getDate();
            const month = date.getMonth() + 1;
            dailyCheckinDisplay.value = `${dayName} - ${day} tháng ${month}`;
        } else {
            dailyCheckinDisplay.value = 'Chọn ngày';
        }
    }
    
    if (dailyCheckoutDisplay) {
        if (dailyCheckoutDate) {
            const date = new Date(dailyCheckoutDate);
            const dayNames = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];
            const dayName = dayNames[date.getDay()];
            const day = date.getDate();
            const month = date.getMonth() + 1;
            dailyCheckoutDisplay.value = `${dayName} - ${day} tháng ${month}`;
        } else {
            dailyCheckoutDisplay.value = 'Chọn ngày';
        }
    }
}

// Function to show notification (if not already defined)
function showNotification(type, message) {
    // Check if notification function exists
    if (typeof window.showNotification === 'function') {
        window.showNotification(type, message);
    } else {
        // Fallback to alert
        alert(message);
    }
}