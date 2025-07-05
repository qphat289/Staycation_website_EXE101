// ================================
// Room Preview - Image Management and SessionStorage Integration
// ================================

// Global variables for image management
let allImages = [];
let currentImageIndex = 0;

// ================================
// Initialization
// ================================
document.addEventListener('DOMContentLoaded', function() {
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
        const sessionData = sessionStorage.getItem('room_form_data');
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
                mainImageElement.alt = currentImage.filename || 'Room Image';
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
            modalImage.alt = currentImage.filename || 'Room Image';
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
            confirmBtn.title = `Cần thêm ${minRequiredImages - imageCount} ảnh nữa để có thể đăng phòng`;
            
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
    const minRequiredImages = 5;
    
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
            Phòng cần có ít nhất <strong>${requiredCount} ảnh</strong> để có thể đăng.<br>
            Hiện tại bạn có <strong>${currentCount} ảnh</strong>.
        </p>
        <p style="color: #9ed649; margin-bottom: 24px; font-size: 14px;">
            <i class="fas fa-lightbulb" style="margin-right: 8px;"></i>
            Hãy quay lại trang chỉnh sửa để thêm ${requiredCount - currentCount} ảnh nữa.
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