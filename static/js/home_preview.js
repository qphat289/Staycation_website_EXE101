// ================================
// Home Preview - Image Management and SessionStorage Integration
// ================================

// Global variables for image management
let allImages = [];
let currentImageIndex = 0;

// ================================
// Initialization
// ================================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize image gallery
    initializeImageGallery();
    
    // Initialize map if address is available
    initializeMap();
    
    // Initialize amenities and rules display
    initializeAmenitiesRules();
    
    loadImagesFromAllSources();
    setupImageNavigationListeners();
    setupImageModal();
    updateImageDisplay();
    setupFormValidation();
});

// ================================
// Image Loading from SessionStorage and Backend
// ================================
function loadImagesFromAllSources() {
    let sessionImages = [];
    let backendImages = [];
    
    try {
        // Try to get images from sessionStorage first (highest priority)
        const sessionData = sessionStorage.getItem('home_form_data');
        if (sessionData) {
            const parsed = JSON.parse(sessionData);
            
            if (parsed.uploadedImages && parsed.uploadedImages.length > 0) {
                sessionImages = parsed.uploadedImages.map(img => ({
                    src: img.dataUrl || img.src,
                    is_main: img.isMain || img.isMainImage || false,
                    filename: img.fileName || 'session_image'
                }));
            }
        }
    } catch (e) {
        console.warn('Error parsing sessionStorage:', e);
    }
    
    // Get backend images from global variable if available
    if (typeof window.backendImages !== 'undefined') {
        backendImages = window.backendImages;
    }
    
    // Use sessionStorage images if available, otherwise use backend images
    if (sessionImages.length > 0) {
        allImages = sessionImages;
    } else {
        allImages = backendImages;
    }
    
    // Initialize display
    if (allImages.length > 0) {
        currentImageIndex = 0;
    }
}

// ================================
// Image Display Functions
// ================================
function updateImageDisplay() {
    updateMainImage();
    updateImageDots();
    updateImageCounter();
    updateNavigationButtons();
}

function updateMainImage() {
    const mainImageElement = document.querySelector('.main-image img');
    const mainImageBadge = document.querySelector('.main-image-badge');
    const imageGallery = document.getElementById('imageGallery');
    const noImagesPlaceholder = document.getElementById('noImagesPlaceholder');
    
    if (allImages.length > 0) {
        const currentImage = allImages[currentImageIndex];
        
        // Show gallery, hide placeholder
        if (imageGallery) imageGallery.style.display = 'block';
        if (noImagesPlaceholder) noImagesPlaceholder.style.display = 'none';
        
        if (mainImageElement) {
            // Add fade effect
            mainImageElement.style.opacity = '0';
            
            setTimeout(() => {
                mainImageElement.src = currentImage.src;
                mainImageElement.alt = currentImage.filename || 'Home Image';
                mainImageElement.style.display = 'block';
                
                // Show/hide main image badge
                if (mainImageBadge) {
                    mainImageBadge.style.display = currentImage.is_main ? 'block' : 'none';
                }
                
                mainImageElement.style.opacity = '1';
            }, 150);
            
            // Make image clickable to open modal
            mainImageElement.style.cursor = 'pointer';
            mainImageElement.onclick = function() { 
                openImageModal(currentImageIndex); 
            };
        }
        
    } else {
        // Hide gallery, show placeholder
        if (imageGallery) imageGallery.style.display = 'none';
        if (noImagesPlaceholder) noImagesPlaceholder.style.display = 'block';
        
        if (mainImageElement) {
            mainImageElement.style.display = 'none';
        }
        if (mainImageBadge) {
            mainImageBadge.style.display = 'none';
        }
    }
}

function updateImageCounter() {
    const counterElement = document.getElementById('imageCounter');
    if (counterElement) {
        if (allImages.length > 0) {
            counterElement.textContent = `${currentImageIndex + 1}/${allImages.length}`;
        } else {
            counterElement.textContent = '0/0';
        }
    }
}

function updateNavigationButtons() {
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    
    const showNavButtons = allImages.length > 1;
    if (prevBtn) prevBtn.style.display = showNavButtons ? 'flex' : 'none';
    if (nextBtn) nextBtn.style.display = showNavButtons ? 'flex' : 'none';
}

function updateImageDots() {
    const dotsContainer = document.querySelector('.image-dots');
    if (!dotsContainer) return;
    
    // Clear existing dots
    dotsContainer.innerHTML = '';
    
    // Only show dots if there are multiple images
    if (allImages.length <= 1) {
        dotsContainer.style.display = 'none';
        return;
    }
    
    dotsContainer.style.display = 'flex';
    
    // Create dots for each image
    allImages.forEach((_, index) => {
        const dot = document.createElement('span');
        dot.className = 'dot';
        if (index === currentImageIndex) {
            dot.classList.add('active');
        }
        
        dot.addEventListener('click', () => {
            goToImage(index);
        });
        
        dotsContainer.appendChild(dot);
    });
}

// ================================
// Image Navigation Functions
// ================================
function prevImage(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (allImages.length <= 1) return;
    
    currentImageIndex = (currentImageIndex - 1 + allImages.length) % allImages.length;
    updateImageDisplay();
}

function nextImage(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (allImages.length <= 1) return;
    
    currentImageIndex = (currentImageIndex + 1) % allImages.length;
    updateImageDisplay();
}

function goToImage(index, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (index >= 0 && index < allImages.length) {
        currentImageIndex = index;
        updateImageDisplay();
    }
}

function setupImageNavigationListeners() {
    // Navigation buttons
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', prevImage);
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', nextImage);
    }
    
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        const modal = document.getElementById('imageModal');
        const isModalOpen = modal && modal.classList.contains('show');
        
        if (!isModalOpen) {  // Only handle navigation when modal is closed
            if (e.key === 'ArrowLeft') {
                prevImage(e);
            } else if (e.key === 'ArrowRight') {
                nextImage(e);
            }
        }
    });
}

// ================================
// Modal Functionality
// ================================
let currentModalIndex = 0;

function setupImageModal() {
    const modal = document.getElementById('imageModal');
    
    if (modal) {
        // Close modal when clicking backdrop
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeImageModal();
            }
        });
        
        // Setup modal navigation buttons
        const modalPrevBtn = document.getElementById('modalPrevBtn');
        const modalNextBtn = document.getElementById('modalNextBtn');
        
        if (modalPrevBtn) {
            modalPrevBtn.addEventListener('click', prevImageInModal);
        }
        
        if (modalNextBtn) {
            modalNextBtn.addEventListener('click', nextImageInModal);
        }
        
        // Keyboard navigation for modal
        document.addEventListener('keydown', function(e) {
            if (modal.classList.contains('show')) {
                if (e.key === 'Escape') {
                    closeImageModal();
                } else if (e.key === 'ArrowLeft') {
                    prevImageInModal(e);
                } else if (e.key === 'ArrowRight') {
                    nextImageInModal(e);
                }
            }
        });
    }
}

function openImageModal(imageIndex = null) {
    if (allImages.length === 0) return;
    
    // Set the starting index
    if (imageIndex !== null && imageIndex >= 0 && imageIndex < allImages.length) {
        currentModalIndex = imageIndex;
    } else {
        currentModalIndex = currentImageIndex;
    }
    
    const modal = document.getElementById('imageModal');
    
    if (modal) {
        // Update modal content
        updateModalImage();
        
        // Show modal
        modal.classList.add('show');
        modal.style.display = 'flex';
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }
}

function closeImageModal(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const modal = document.getElementById('imageModal');
    
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
        
        // Restore body scroll
        document.body.style.overflow = '';
    }
}

function updateModalImage() {
    const modalImage = document.getElementById('modalImage');
    const modalCounter = document.getElementById('modalCounter');
    const modalMainBadge = document.getElementById('modalMainBadge');
    const modalPrevBtn = document.getElementById('modalPrevBtn');
    const modalNextBtn = document.getElementById('modalNextBtn');
    
    if (modalImage && allImages.length > 0) {
        const currentImage = allImages[currentModalIndex];
        
        // Add fade effect
        modalImage.style.opacity = '0';
        
        setTimeout(() => {
            modalImage.src = currentImage.src;
            modalImage.alt = currentImage.filename || 'Home Image';
            modalImage.style.opacity = '1';
        }, 150);
        
        // Update counter
        if (modalCounter) {
            modalCounter.textContent = `${currentModalIndex + 1}/${allImages.length}`;
        }
        
        // Show/hide main badge
        if (modalMainBadge) {
            modalMainBadge.style.display = currentImage.is_main ? 'block' : 'none';
        }
        
        // Show/hide navigation buttons
        const showNavButtons = allImages.length > 1;
        if (modalPrevBtn) modalPrevBtn.style.display = showNavButtons ? 'flex' : 'none';
        if (modalNextBtn) modalNextBtn.style.display = showNavButtons ? 'flex' : 'none';
    }
}

function prevImageInModal(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (allImages.length <= 1) return;
    
    currentModalIndex = (currentModalIndex - 1 + allImages.length) % allImages.length;
    updateModalImage();
}

function nextImageInModal(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (allImages.length <= 1) return;
    
    currentModalIndex = (currentModalIndex + 1) % allImages.length;
    updateModalImage();
}

// ================================
// Modal Functions for Rules and Amenities
// ================================
function showAllRulesModal() {
    const modal = document.getElementById('allRulesModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeAllRulesModal() {
    const modal = document.getElementById('allRulesModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

function showAllAmenitiesModal() {
    const modal = document.getElementById('allAmenitiesModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeAllAmenitiesModal() {
    const modal = document.getElementById('allAmenitiesModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ================================
// Form Validation
// ================================
function setupFormValidation() {
    const confirmBtn = document.getElementById('confirmBtn');
    const minRequiredImages = 5;
    
    // Check initial state after images are loaded
    setTimeout(() => {
        const imageCount = allImages.length;
        
        if (imageCount < minRequiredImages && confirmBtn) {
            confirmBtn.style.opacity = '0.6';
            confirmBtn.style.cursor = 'not-allowed';
            confirmBtn.title = `Cần thêm ${minRequiredImages - imageCount} ảnh nữa để có thể đăng nhà`;
            
            const warningText = document.createElement('div');
            warningText.style.cssText = `
                color: #f59e0b;
                font-size: 12px;
                margin-top: 4px;
                font-weight: 500;
            `;
            warningText.innerHTML = `<i class="fas fa-exclamation-triangle" style="margin-right: 4px;"></i>Cần ${minRequiredImages - imageCount} ảnh nữa`;
            confirmBtn.parentNode.appendChild(warningText);
        }
    }, 500);
}

function validateImageCount() {
    const imageCount = allImages.length;
    const minRequiredImages = 1;
    
    if (imageCount < minRequiredImages) {
        showImageRequirementAlert(imageCount, minRequiredImages);
        return false;
    }
    
    return true;
}

function showImageRequirementAlert(currentCount, requiredCount) {
    const backdrop = document.createElement('div');
    backdrop.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: white;
        padding: 32px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        max-width: 400px;
        width: 90%;
        text-align: center;
        animation: modalSlideIn 0.3s ease-out;
    `;
    
    modal.innerHTML = `
        <div style="color: #f59e0b; font-size: 48px; margin-bottom: 16px;">
            <i class="fas fa-exclamation-triangle"></i>
        </div>
        <h3 style="color: #333; margin-bottom: 16px; font-size: 20px;">Cần thêm ảnh</h3>
        <p style="color: #666; margin-bottom: 24px; line-height: 1.5;">
            Nhà cần có ít nhất <strong>${requiredCount} ảnh</strong> để có thể đăng.<br>
            Hiện tại bạn có <strong>${currentCount} ảnh</strong>.
        </p>
        <p style="color: #9ed649; margin-bottom: 24px; font-size: 14px;">
            <i class="fas fa-lightbulb" style="margin-right: 8px;"></i>
            Hãy quay lại trang chỉnh sửa để thêm ít nhất ${requiredCount - currentCount} ảnh nữa.
        </p>
        <div style="display: flex; gap: 12px; justify-content: center;">
            <button onclick="closeImageAlert()" style="
                background: #9ed649;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            " onmouseover="this.style.background='#8bc441'" onmouseout="this.style.background='#9ed649'">
                <i class="fas fa-arrow-left" style="margin-right: 8px;"></i>
                Quay lại chỉnh sửa
            </button>
        </div>
    `;
    
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes modalSlideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
    
    window.currentImageAlert = backdrop;
}

function closeImageAlert() {
    if (window.currentImageAlert) {
        document.body.removeChild(window.currentImageAlert);
        window.currentImageAlert = null;
    }
}

// Make functions globally available
window.prevImage = prevImage;
window.nextImage = nextImage;
window.goToImage = goToImage;
window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
window.prevImageInModal = prevImageInModal;
window.nextImageInModal = nextImageInModal;
window.showAllRulesModal = showAllRulesModal;
window.closeAllRulesModal = closeAllRulesModal;
window.showAllAmenitiesModal = showAllAmenitiesModal;
window.closeAllAmenitiesModal = closeAllAmenitiesModal;
window.validateImageCount = validateImageCount;
window.closeImageAlert = closeImageAlert;

function initializeImageGallery() {
    const imageContainer = document.querySelector('.home-images-container');
    if (!imageContainer) return;
    
    const images = imageContainer.querySelectorAll('.home-image');
    const mainImage = document.querySelector('.main-home-image');
    
    images.forEach(image => {
        image.addEventListener('click', function() {
            const src = this.src;
            if (mainImage) {
                mainImage.src = src;
            }
            
            // Update active state
            images.forEach(img => img.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function initializeMap() {
    const mapContainer = document.querySelector('#map');
    if (!mapContainer) return;
    
    const address = mapContainer.dataset.address;
    if (!address) {
        // Try to get address from template data
        const addressElement = document.querySelector('.address-display span');
        if (addressElement) {
            const addressText = addressElement.textContent.trim();
            if (addressText) {
                loadGoogleMaps(addressText);
                return;
            }
        }
        console.log('No address found for map');
        return;
    }
    
    loadGoogleMaps(address);
}

function loadGoogleMaps(address) {
    // Check if Google Maps API is already loaded
    if (typeof google !== 'undefined' && google.maps) {
        initGoogleMap(address);
        return;
    }
    
    // Load Google Maps API
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${CONFIG.GOOGLE_MAPS_API_KEY}&callback=initGoogleMapCallback&libraries=geometry`;
    script.async = true;
    script.defer = true;
    
    // Store address globally for callback
    window.pendingMapAddress = address;
    
    // Define global callback
    window.initGoogleMapCallback = function() {
        if (window.pendingMapAddress) {
            initGoogleMap(window.pendingMapAddress);
            delete window.pendingMapAddress;
        }
    };
    
    document.head.appendChild(script);
}

function initGoogleMap(address) {
    const mapContainer = document.querySelector('#map');
    const loadingElement = document.querySelector('#map-loading');
    
    if (!mapContainer) return;
    
    // Hide loading indicator
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
    
    // Create geocoder
    const geocoder = new google.maps.Geocoder();
    
    // Geocode the address
    geocoder.geocode({ address: address + ', Vietnam' }, function(results, status) {
        if (status === 'OK' && results[0]) {
            const location = results[0].geometry.location;
            
            // Create map
            const map = new google.maps.Map(mapContainer, {
                zoom: CONFIG.DEFAULT_MAP_ZOOM,
                center: location,
                styles: CONFIG.MAP_STYLES,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true
            });
            
            // Create marker
            const marker = new google.maps.Marker({
                position: location,
                map: map,
                title: 'Vị trí nhà',
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="16" cy="16" r="8" fill="#9ed649" stroke="white" stroke-width="2"/>
                            <circle cx="16" cy="16" r="3" fill="white"/>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(32, 32),
                    anchor: new google.maps.Point(16, 16)
                }
            });
            
            // Add info window
            const infoWindow = new google.maps.InfoWindow({
                content: `<div style="padding: 8px; font-family: Arial, sans-serif;">
                    <strong style="color: #333;">Vị trí nhà</strong><br>
                    <span style="color: #666; font-size: 14px;">${address}</span>
                </div>`
            });
            
            marker.addListener('click', function() {
                infoWindow.open(map, marker);
            });
            
        } else {
            console.error('Geocoding failed:', status);
            // Show error message in map container
            mapContainer.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #666; font-size: 14px;">
                    <div style="text-align: center;">
                        <i class="fas fa-map-marked-alt" style="font-size: 24px; margin-bottom: 8px; color: #ccc;"></i><br>
                        Không thể tải bản đồ cho địa chỉ này
                    </div>
                </div>
            `;
        }
    });
}

function initializeAmenitiesRules() {
    // Initialize amenities display
    const amenitiesContainer = document.querySelector('.home-amenities');
    if (amenitiesContainer) {
        const amenityItems = amenitiesContainer.querySelectorAll('.amenity-item');
        amenityItems.forEach(item => {
            item.addEventListener('click', function() {
                const tooltip = this.querySelector('.amenity-tooltip');
                if (tooltip) {
                    tooltip.classList.toggle('show');
                }
            });
        });
    }
    
    // Initialize rules display
    const rulesContainer = document.querySelector('.home-rules');
    if (rulesContainer) {
        const ruleItems = rulesContainer.querySelectorAll('.rule-item');
        ruleItems.forEach(item => {
            item.addEventListener('click', function() {
                const tooltip = this.querySelector('.rule-tooltip');
                if (tooltip) {
                    tooltip.classList.toggle('show');
                }
            });
        });
    }
}

// Function to handle home booking
function bookHome(homeId) {
    if (!homeId) {
        alert('Không tìm thấy thông tin nhà');
        return;
    }
    
    window.location.href = `/renter/book/${homeId}`;
}

// Function to handle home sharing
function shareHome() {
    const url = window.location.href;
    const title = document.title;
    
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        }).then(() => {
            console.log('Shared successfully');
        }).catch((error) => {
            console.log('Error sharing:', error);
            fallbackShare(url);
        });
    } else {
        fallbackShare(url);
    }
}

function fallbackShare(url) {
    // Fallback for browsers that don't support Web Share API
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(() => {
            alert('Đã copy link vào clipboard!');
        });
    } else {
        // Even more basic fallback
        const textArea = document.createElement('textarea');
        textArea.value = url;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        alert('Đã copy link vào clipboard!');
    }
}

// Function to save/unsave home
function toggleSaveHome(homeId) {
    // This would integrate with user favorites/saved homes functionality
    console.log('Toggle save home:', homeId);
    
    const saveBtn = document.querySelector('#saveHomeBtn');
    if (saveBtn) {
        const isSaved = saveBtn.classList.contains('saved');
        
        if (isSaved) {
            saveBtn.classList.remove('saved');
            saveBtn.innerHTML = '<i class="fas fa-heart-o"></i>';
            saveBtn.title = 'Lưu';
        } else {
            saveBtn.classList.add('saved');
            saveBtn.innerHTML = '<i class="fas fa-heart"></i>';
            saveBtn.title = 'Đã lưu';
        }
    }
}

// Function to show single image in modal
function showSingleImage(imageSrc, imageTitle) {
    // Create modal if it doesn't exist
    let modal = document.querySelector('#imageModal');
    if (!modal) {
        modal = createImageModal();
    }
    
    const modalImg = modal.querySelector('.modal-image');
    const modalTitle = modal.querySelector('.modal-title');
    
    if (modalImg) modalImg.src = imageSrc;
    if (modalTitle) modalTitle.textContent = imageTitle || 'Ảnh nhà';
    
    // Show modal
    modal.style.display = 'block';
}

function createImageModal() {
    const modal = document.createElement('div');
    modal.id = 'imageModal';
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close">&times;</span>
            <h4 class="modal-title"></h4>
            <img class="modal-image" src="" alt="Home image">
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add close functionality
    const closeBtn = modal.querySelector('.close');
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    return modal;
} 