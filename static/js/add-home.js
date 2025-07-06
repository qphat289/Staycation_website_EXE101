// Add Home Wizard JavaScript Functions

// Global variables
let currentStep = 1;
let selectedAmenities = [];
let selectedRules = [];
let allAmenities = [];
let allRules = [];

// Initialize the wizard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeWizard();
    loadAmenities();
    loadRules();
    loadLocationData();
    setupEventListeners();
});

// Initialize wizard
function initializeWizard() {
    // Set initial step
    const urlParams = new URLSearchParams(window.location.search);
    const lastStep = urlParams.get('last_step') || 1;
    currentStep = parseInt(lastStep);
    
    // Show current step
    showStep(currentStep);
    
    // Initialize counters
    updateCounterDisplays();
    
    // Initialize pricing display
    updatePricingDisplay();
    
    // Load saved data if available
    loadSavedData();
}

// Step navigation functions
function nextStep() {
    if (validateCurrentStep()) {
        if (currentStep < 3) {
            currentStep++;
            showStep(currentStep);
            saveCurrentStepToSession();
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
        saveCurrentStepToSession();
    }
}

function goToStep(step) {
    if (step >= 1 && step <= 3) {
        currentStep = step;
        showStep(currentStep);
        saveCurrentStepToSession();
    }
}

function showStep(step) {
    // Hide all steps
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Show current step
    const currentStepElement = document.getElementById(`step-${step}`);
    if (currentStepElement) {
        currentStepElement.classList.add('active');
    }
    
    // Update sidebar
    document.querySelectorAll('.step').forEach((stepElement, index) => {
        stepElement.classList.toggle('active', index + 1 === step);
    });
    
    // Update pricing display when showing step 3
    if (step === 3) {
        updatePricingDisplay();
    }
}

// Validation functions
function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            return validateStep1();
        case 2:
            return validateStep2();
        case 3:
            return validateStep3();
        default:
            return true;
    }
}

function validateStep1() {
    const errors = [];
    
    // Check title
    const title = document.getElementById('home_title').value.trim();
    if (!title) {
        errors.push('Vui lòng nhập tên homestay');
    }
    
    // Check description
    const description = document.getElementById('home_description').value.trim();
    if (!description) {
        errors.push('Vui lòng nhập mô tả homestay');
    }
    
    // Check property type
    const propertyType = document.querySelector('input[name="property_type"]:checked');
    if (!propertyType) {
        errors.push('Vui lòng chọn mô hình homestay');
    }
    
    // Check location
    const province = document.getElementById('province').value;
    const district = document.getElementById('district').value;
    const ward = document.getElementById('ward').value;
    const street = document.getElementById('street').value.trim();
    
    if (!province) errors.push('Vui lòng chọn tỉnh/thành phố');
    if (!district) errors.push('Vui lòng chọn quận/huyện');
    if (!ward) errors.push('Vui lòng chọn phường/xã');
    if (!street) errors.push('Vui lòng nhập địa chỉ đường');
    
    if (errors.length > 0) {
        showValidationErrors(errors);
        return false;
    }
    
    return true;
}

function validateStep2() {
    const errors = [];
    
    // Check rental type
    const rentalType = document.querySelector('input[name="rental_type"]:checked');
    if (!rentalType) {
        errors.push('Vui lòng chọn hình thức cho thuê');
    }
    
    if (errors.length > 0) {
        showValidationErrors(errors);
        return false;
    }
    
    return true;
}

function validateStep3() {
    const errors = [];
    
    // Check pricing
    const rentalType = document.querySelector('input[name="rental_type"]:checked');
    if (rentalType) {
        if (rentalType.value === 'hourly') {
            const hourlyPrice = document.querySelector('input[name="hourly_price"]').value;
            if (!hourlyPrice || hourlyPrice.trim() === '') {
                errors.push('Vui lòng nhập giá theo giờ');
            }
        } else if (rentalType.value === 'nightly') {
            const nightlyPrice = document.querySelector('input[name="nightly_price"]').value;
            if (!nightlyPrice || nightlyPrice.trim() === '') {
                errors.push('Vui lòng nhập giá theo đêm');
            }
        }
    }
    
    if (errors.length > 0) {
        showValidationErrors(errors);
        return false;
    }
    
    return true;
}

function showValidationErrors(errors) {
    const errorMessage = errors.join('\n');
    alert(errorMessage);
}

// Counter functions
function increaseCount(type) {
    const countElement = document.getElementById(`${type}-count`);
    const inputElement = document.getElementById(`${type}_count_input`);
    
    if (countElement && inputElement) {
        let currentValue = parseInt(countElement.textContent);
        currentValue++;
        
        // Set maximum limits
        const maxValues = {
            'bathroom': 10,
            'bed': 20,
            'guest': 50
        };
        
        if (currentValue <= maxValues[type]) {
            countElement.textContent = currentValue;
            inputElement.value = currentValue;
        }
    }
}

function decreaseCount(type) {
    const countElement = document.getElementById(`${type}-count`);
    const inputElement = document.getElementById(`${type}_count_input`);
    
    if (countElement && inputElement) {
        let currentValue = parseInt(countElement.textContent);
        currentValue--;
        
        // Set minimum to 1
        if (currentValue >= 1) {
            countElement.textContent = currentValue;
            inputElement.value = currentValue;
        }
    }
}

function updateCounterDisplays() {
    ['bathroom', 'bed', 'guest'].forEach(type => {
        const countElement = document.getElementById(`${type}-count`);
        const inputElement = document.getElementById(`${type}_count_input`);
        
        if (countElement && inputElement) {
            countElement.textContent = inputElement.value || 1;
        }
    });
}

// Pricing functions
function updatePricingDisplay() {
    const rentalType = document.querySelector('input[name="rental_type"]:checked');
    const hourlyPricing = document.getElementById('hourly-pricing');
    const nightlyPricing = document.getElementById('nightly-pricing');
    const noPricingSelected = document.getElementById('no-pricing-selected');
    
    if (rentalType) {
        noPricingSelected.style.display = 'none';
        
        if (rentalType.value === 'hourly') {
            hourlyPricing.style.display = 'block';
            nightlyPricing.style.display = 'none';
        } else if (rentalType.value === 'nightly') {
            hourlyPricing.style.display = 'none';
            nightlyPricing.style.display = 'block';
        }
    } else {
        hourlyPricing.style.display = 'none';
        nightlyPricing.style.display = 'none';
        noPricingSelected.style.display = 'block';
    }
}

function formatPriceInput(input) {
    // Remove all non-numeric characters
    let value = input.value.replace(/[^0-9]/g, '');
    
    // Format with thousands separator
    if (value) {
        value = parseInt(value).toLocaleString('vi-VN');
    }
    
    input.value = value;
}

function validatePrice(input, type) {
    const value = input.value.replace(/[^0-9]/g, '');
    const numericValue = parseInt(value);
    
    if (type === 'hourly') {
        if (numericValue < 50000) {
            alert('Giá theo giờ tối thiểu là 50,000 VND');
            input.focus();
        }
    } else if (type === 'nightly') {
        if (numericValue < 200000) {
            alert('Giá theo đêm tối thiểu là 200,000 VND');
            input.focus();
        }
    }
}

// Amenities functions
function loadAmenities() {
    fetch('/api/amenities')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // Transform the API response to flat array
                allAmenities = [];
                Object.entries(result.data).forEach(([categoryCode, categoryData]) => {
                    categoryData.amenities.forEach(amenity => {
                        allAmenities.push({
                            ...amenity,
                            category: categoryCode
                        });
                    });
                });
                displayAmenities();
            } else {
                throw new Error(result.message || 'Failed to load amenities');
            }
        })
        .catch(error => {
            console.error('Error loading amenities:', error);
            // Fallback data
            allAmenities = [
                {id: 1, name: 'Wi-Fi', icon: 'fas fa-wifi', category: 'internet'},
                {id: 2, name: 'Điều hòa', icon: 'fas fa-snowflake', category: 'comfort'},
                {id: 3, name: 'Tủ lạnh', icon: 'fas fa-archive', category: 'kitchen'},
                {id: 4, name: 'Bếp', icon: 'fas fa-fire', category: 'kitchen'},
                {id: 5, name: 'Máy giặt', icon: 'fas fa-tshirt', category: 'laundry'},
                {id: 6, name: 'Bãi đậu xe', icon: 'fas fa-car', category: 'parking'},
                {id: 7, name: 'Hồ bơi', icon: 'fas fa-swimmer', category: 'entertainment'},
                {id: 8, name: 'Gym', icon: 'fas fa-dumbbell', category: 'entertainment'}
            ];
            displayAmenities();
        });
}

function displayAmenities() {
    const amenitySections = document.querySelector('.amenity-sections');
    if (!amenitySections) return;
    
    // Group amenities by category
    const categories = {
        'internet': 'Kết nối Internet',
        'comfort': 'Tiện nghi',
        'kitchen': 'Bếp & Ăn uống',
        'laundry': 'Giặt ủi',
        'parking': 'Đỗ xe',
        'entertainment': 'Giải trí'
    };
    
    let html = '';
    Object.entries(categories).forEach(([category, title]) => {
        const categoryAmenities = allAmenities.filter(a => a.category === category);
        if (categoryAmenities.length > 0) {
            html += `
                <div class="amenity-section" data-category="${category}">
                    <h4 class="section-title">
                        <i class="fas fa-star me-2"></i>${title}
                    </h4>
                    <div class="amenities-grid">
                        ${categoryAmenities.map(amenity => `
                            <div class="amenity-item" data-amenity-id="${amenity.id}" onclick="toggleAmenitySelection(${amenity.id}, '${amenity.name}', '${amenity.icon}')">
                                <i class="${amenity.icon}"></i>
                                <span>${amenity.name}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    });
    
    amenitySections.innerHTML = html;
}

function showAmenityModal() {
    const modal = document.getElementById('amenityModal');
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        
        // Mark currently selected amenities
        selectedAmenities.forEach(amenity => {
            const item = document.querySelector(`[data-amenity-id="${amenity.id}"]`);
            if (item) {
                item.classList.add('selected');
            }
        });
    }
}

function closeAmenityModal() {
    const modal = document.getElementById('amenityModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function toggleAmenitySelection(amenityId, amenityName, amenityIcon) {
    const item = document.querySelector(`[data-amenity-id="${amenityId}"]`);
    const isSelected = item.classList.contains('selected');
    
    if (isSelected) {
        // Remove from selection
        selectedAmenities = selectedAmenities.filter(a => a.id !== amenityId);
        item.classList.remove('selected');
    } else {
        // Add to selection
        selectedAmenities.push({
            id: amenityId,
            name: amenityName,
            icon: amenityIcon
        });
        item.classList.add('selected');
    }
    
    updateSelectedAmenitiesDisplay();
}

function updateSelectedAmenitiesDisplay() {
    const container = document.getElementById('selectedAmenities');
    if (!container) return;
    
    if (selectedAmenities.length === 0) {
        container.innerHTML = '<p style="color: #666; font-style: italic;">Chưa chọn tiện nghi nào</p>';
    } else {
        container.innerHTML = selectedAmenities.map(amenity => `
            <div class="selected-amenity-item">
                <i class="${amenity.icon}"></i>
                <span>${amenity.name}</span>
                <span class="remove-amenity" onclick="removeAmenity(${amenity.id})">&times;</span>
            </div>
        `).join('');
    }
    
    // Update hidden inputs
    updateAmenityInputs();
}

function removeAmenity(amenityId) {
    selectedAmenities = selectedAmenities.filter(a => a.id !== amenityId);
    updateSelectedAmenitiesDisplay();
    
    // Update modal if open
    const item = document.querySelector(`[data-amenity-id="${amenityId}"]`);
    if (item) {
        item.classList.remove('selected');
    }
}

function updateAmenityInputs() {
    const container = document.getElementById('amenityInputs');
    if (!container) return;
    
    container.innerHTML = selectedAmenities.map(amenity => 
        `<input type="hidden" name="amenities[]" value="${amenity.id}">`
    ).join('');
}

// Rules functions
function loadRules() {
    fetch('/api/rules')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // Transform the API response to flat array
                allRules = [];
                Object.entries(result.data).forEach(([category, rules]) => {
                    rules.forEach(rule => {
                        allRules.push({
                            ...rule,
                            category: category
                        });
                    });
                });
                displayRules();
            } else {
                throw new Error(result.message || 'Failed to load rules');
            }
        })
        .catch(error => {
            console.error('Error loading rules:', error);
            // Fallback data
            allRules = [
                {id: 1, name: 'Không hút thuốc', category: 'smoking'},
                {id: 2, name: 'Không mang thú cưng', category: 'pets'},
                {id: 3, name: 'Không tổ chức tiệc', category: 'party'},
                {id: 4, name: 'Giữ yên lặng sau 22h', category: 'time'},
                {id: 5, name: 'Không mang trẻ em', category: 'children'},
                {id: 6, name: 'Không uống rượu bia', category: 'behavior'}
            ];
            displayRules();
        });
}

function displayRules() {
    const categories = {
        'smoking': 'smokingRules',
        'pets': 'petsRules',
        'children': 'childrenRules',
        'party': 'partyRules',
        'time': 'timeRules',
        'behavior': 'behaviorRules'
    };
    
    Object.entries(categories).forEach(([category, containerId]) => {
        const container = document.getElementById(containerId);
        if (container) {
            const categoryRules = allRules.filter(r => r.category === category);
            container.innerHTML = categoryRules.map(rule => `
                <div class="rule-item" data-rule-id="${rule.id}" onclick="toggleRuleSelection(${rule.id}, '${rule.name}')">
                    <i class="fas fa-check-circle"></i>
                    <span>${rule.name}</span>
                </div>
            `).join('');
        }
    });
}

function showRulesModal() {
    const modal = document.getElementById('rulesModal');
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        
        // Mark currently selected rules
        selectedRules.forEach(rule => {
            const item = document.querySelector(`[data-rule-id="${rule.id}"]`);
            if (item) {
                item.classList.add('selected');
            }
        });
    }
}

function closeRulesModal() {
    const modal = document.getElementById('rulesModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function toggleRuleSelection(ruleId, ruleName) {
    const item = document.querySelector(`[data-rule-id="${ruleId}"]`);
    const isSelected = item.classList.contains('selected');
    
    if (isSelected) {
        // Remove from selection
        selectedRules = selectedRules.filter(r => r.id !== ruleId);
        item.classList.remove('selected');
    } else {
        // Add to selection
        selectedRules.push({
            id: ruleId,
            name: ruleName
        });
        item.classList.add('selected');
    }
    
    updateSelectedRulesDisplay();
}

function updateSelectedRulesDisplay() {
    const container = document.getElementById('selectedRules');
    if (!container) return;
    
    if (selectedRules.length === 0) {
        container.innerHTML = '<p style="color: #666; font-style: italic;">Chưa chọn nội quy nào</p>';
    } else {
        container.innerHTML = selectedRules.map(rule => `
            <div class="selected-rule-item">
                <span>${rule.name}</span>
                <span class="remove-rule" onclick="removeRule(${rule.id})">&times;</span>
            </div>
        `).join('');
    }
    
    // Update hidden inputs
    updateRuleInputs();
}

function removeRule(ruleId) {
    selectedRules = selectedRules.filter(r => r.id !== ruleId);
    updateSelectedRulesDisplay();
    
    // Update modal if open
    const item = document.querySelector(`[data-rule-id="${ruleId}"]`);
    if (item) {
        item.classList.remove('selected');
    }
}

function updateRuleInputs() {
    const container = document.getElementById('ruleInputs');
    if (!container) return;
    
    container.innerHTML = selectedRules.map(rule => 
        `<input type="hidden" name="rules[]" value="${rule.id}">`
    ).join('');
}

function saveSelectedRules() {
    updateSelectedRulesDisplay();
    closeRulesModal();
}

// Location functions
function loadLocationData() {
    fetch('/api/provinces')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const provinceSelect = document.getElementById('province');
                if (provinceSelect) {
                    provinceSelect.innerHTML = '<option value="" disabled selected>Tỉnh/Thành phố</option>';
                    result.data.forEach(province => {
                        provinceSelect.innerHTML += `<option value="${province.code}">${province.name}</option>`;
                    });
                }
            } else {
                throw new Error(result.message || 'Failed to load provinces');
            }
        })
        .catch(error => {
            console.error('Error loading provinces:', error);
        });
}

function updateDistricts() {
    const provinceSelect = document.getElementById('province');
    const districtSelect = document.getElementById('district');
    const wardSelect = document.getElementById('ward');
    
    if (!provinceSelect.value) return;
    
    // Reset dependent selects
    districtSelect.innerHTML = '<option value="" disabled selected>Quận/Huyện</option>';
    wardSelect.innerHTML = '<option value="" disabled selected>Phường/Xã</option>';
    wardSelect.disabled = true;
    
    fetch(`/api/provinces/${provinceSelect.value}/districts`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                result.data.forEach(district => {
                    districtSelect.innerHTML += `<option value="${district.code}">${district.name}</option>`;
                });
                districtSelect.disabled = false;
            } else {
                throw new Error(result.message || 'Failed to load districts');
            }
        })
        .catch(error => {
            console.error('Error loading districts:', error);
        });
}

function updateWards() {
    const districtSelect = document.getElementById('district');
    const wardSelect = document.getElementById('ward');
    
    if (!districtSelect.value) return;
    
    wardSelect.innerHTML = '<option value="" disabled selected>Phường/Xã</option>';
    
    fetch(`/api/districts/${districtSelect.value}/wards`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                result.data.forEach(ward => {
                    wardSelect.innerHTML += `<option value="${ward.code}">${ward.name}</option>`;
                });
                wardSelect.disabled = false;
            } else {
                throw new Error(result.message || 'Failed to load wards');
            }
        })
        .catch(error => {
            console.error('Error loading wards:', error);
        });
}

// Event listeners
function setupEventListeners() {
    // Rental type change
    document.querySelectorAll('input[name="rental_type"]').forEach(radio => {
        radio.addEventListener('change', updatePricingDisplay);
    });
    
    // Character counter for description
    const descriptionTextarea = document.getElementById('home_description');
    if (descriptionTextarea) {
        descriptionTextarea.addEventListener('input', function() {
            const charCount = this.value.length;
            const counter = document.querySelector('.char-count');
            if (counter) {
                counter.textContent = `${charCount}/500`;
                if (charCount > 500) {
                    counter.style.color = '#dc3545';
                } else {
                    counter.style.color = '#999';
                }
            }
        });
    }
    
    // Modal close on backdrop click
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeAmenityModal();
            closeRulesModal();
        }
    });
    
    // Step navigation from sidebar
    document.querySelectorAll('.step').forEach((step, index) => {
        step.addEventListener('click', function() {
            goToStep(index + 1);
        });
    });
}

// Form submission
function prepareFormData() {
    // Update hidden inputs
    updateAmenityInputs();
    updateRuleInputs();
    
    // Set rental type
    const rentalType = document.querySelector('input[name="rental_type"]:checked');
    if (rentalType) {
        document.getElementById('selected_rental_type').value = rentalType.value;
    }
    
    // Validate all steps
    for (let i = 1; i <= 3; i++) {
        currentStep = i;
        if (!validateCurrentStep()) {
            showStep(i);
            return false;
        }
    }
    
    return true;
}

// Session management
function saveCurrentStepToSession() {
    fetch('/save-current-step', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            current_step: currentStep
        })
    }).catch(error => {
        console.error('Error saving step:', error);
    });
}

function loadSavedData() {
    // This function would load any saved form data from the server
    // Implementation depends on your backend session management
    console.log('Loading saved data...');
}

// Back navigation
function goBack() {
    window.history.back();
}

// Image upload functions
function setupImageUpload() {
    const uploadItems = document.querySelectorAll('.upload-item');
    
    uploadItems.forEach(item => {
        const fileInput = item.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.addEventListener('change', function(e) {
                handleImageUpload(e, item);
            });
        }
    });
}

function handleImageUpload(event, uploadItem) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file
    if (!validateImageFile(file)) {
        return;
    }
    
    // Show preview
    showImagePreview(file, uploadItem);
}

function validateImageFile(file) {
    // Check file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        alert('Chỉ cho phép upload file ảnh (JPG, PNG, GIF)');
        return false;
    }
    
    // Check file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        alert('Kích thước file không được vượt quá 5MB');
        return false;
    }
    
    return true;
}

function showImagePreview(file, uploadItem) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        // Create preview element
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.innerHTML = `
            <img src="${e.target.result}" alt="Preview" style="width: 100%; height: 100%; object-fit: cover; border-radius: 6px;">
            <button type="button" class="remove-image" onclick="removeImagePreview(this)">&times;</button>
        `;
        
        // Replace placeholder with preview
        const placeholder = uploadItem.querySelector('.upload-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        // Remove existing preview
        const existingPreview = uploadItem.querySelector('.image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        uploadItem.appendChild(preview);
    };
    
    reader.readAsDataURL(file);
}

function removeImagePreview(button) {
    const uploadItem = button.closest('.upload-item');
    const preview = button.closest('.image-preview');
    const fileInput = uploadItem.querySelector('input[type="file"]');
    const placeholder = uploadItem.querySelector('.upload-placeholder');
    
    // Remove preview
    if (preview) {
        preview.remove();
    }
    
    // Clear file input
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Show placeholder again
    if (placeholder) {
        placeholder.style.display = 'flex';
    }
}

// Initialize image upload when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setupImageUpload();
}); 