// Home Preview JavaScript
let currentImageIndex = 0;
let images = [];

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Home Preview JS loaded');
    initializeImageGallery();
});

function initializeImageGallery() {
    // Get images from backend data
    images = window.backendImages || [];
    console.log('Images loaded:', images);
    
    if (images.length === 0) {
        showNoImagesPlaceholder();
        return;
    }
    
    setupImageGallery();
    displayMainImage();
    setupImageDots();
    updateImageCounter();
    setupNavigationButtons();
}

function showNoImagesPlaceholder() {
    const placeholder = document.getElementById('noImagesPlaceholder');
    const gallery = document.getElementById('imageGallery');
    
    if (placeholder) {
        placeholder.style.display = 'block';
    }
    if (gallery) {
        gallery.style.display = 'none';
    }
    
    // Update counter to show 0/0
    updateImageCounter();
}

function setupImageGallery() {
    const gallery = document.getElementById('imageGallery');
    const placeholder = document.getElementById('noImagesPlaceholder');
    
    if (gallery) {
        gallery.style.display = 'block';
    }
    if (placeholder) {
        placeholder.style.display = 'none';
    }
}

function displayMainImage() {
    if (images.length === 0) return;
    
    const mainImageContainer = document.getElementById('mainImage');
    const imgElement = mainImageContainer.querySelector('img');
    const badge = mainImageContainer.querySelector('.main-image-badge');
    
    if (imgElement && images[currentImageIndex]) {
        const currentImage = images[currentImageIndex];
        
        // Add fade out effect
        imgElement.classList.add('fade-out');
        
        setTimeout(() => {
            imgElement.src = currentImage.src;
            imgElement.alt = 'Home Image ' + (currentImageIndex + 1);
            imgElement.style.display = 'block';
            imgElement.style.opacity = '1';
            
            // Add click listener for modal
            imgElement.onclick = () => openImageModal(currentImageIndex);
            imgElement.style.cursor = 'pointer';
            
            // Remove fade out and add fade in
            imgElement.classList.remove('fade-out');
            imgElement.classList.add('fade-in');
            
            // Show/hide main image badge
            if (badge) {
                if (currentImage.is_main) {
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }
            
            setTimeout(() => {
                imgElement.classList.remove('fade-in');
            }, 300);
        }, 150);
    }
}

function setupImageDots() {
    const dotsContainer = document.querySelector('.image-dots');
    if (!dotsContainer || images.length <= 1) {
        if (dotsContainer) dotsContainer.style.display = 'none';
        return;
    }
    
    dotsContainer.style.display = 'flex';
    dotsContainer.innerHTML = '';
    
    images.forEach((image, index) => {
        const dot = document.createElement('button');
        dot.className = 'image-dot';
        if (index === currentImageIndex) {
            dot.classList.add('active');
        }
        
        dot.onclick = () => {
            currentImageIndex = index;
            displayMainImage();
            updateImageDots();
            updateImageCounter();
        };
        
        dotsContainer.appendChild(dot);
    });
}

function updateImageDots() {
    const dots = document.querySelectorAll('.image-dot');
    dots.forEach((dot, index) => {
        if (index === currentImageIndex) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

function updateImageCounter() {
    const counter = document.getElementById('imageCounter');
    if (counter) {
        if (images.length === 0) {
            counter.textContent = '0/0';
        } else {
            counter.textContent = `${currentImageIndex + 1}/${images.length}`;
        }
    }
}

function setupNavigationButtons() {
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    
    if (images.length <= 1) {
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
        return;
    }
    
    if (prevBtn) {
        prevBtn.style.display = 'block';
        prevBtn.onclick = () => {
            currentImageIndex = currentImageIndex > 0 ? currentImageIndex - 1 : images.length - 1;
            displayMainImage();
            updateImageDots();
            updateImageCounter();
        };
    }
    
    if (nextBtn) {
        nextBtn.style.display = 'block';
        nextBtn.onclick = () => {
            currentImageIndex = currentImageIndex < images.length - 1 ? currentImageIndex + 1 : 0;
            displayMainImage();
            updateImageDots();
            updateImageCounter();
        };
    }
}

// Modal functions
function openImageModal(index) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalCounter = document.getElementById('modalCounter');
    const modalBadge = document.getElementById('modalMainBadge');
    
    if (modal && modalImage && images[index]) {
        currentImageIndex = index;
        modalImage.src = images[index].src;
        modalImage.alt = 'Home Image ' + (index + 1);
        
        if (modalCounter) {
            modalCounter.textContent = `${index + 1}/${images.length}`;
        }
        
        if (modalBadge) {
            if (images[index].is_main) {
                modalBadge.style.display = 'block';
            } else {
                modalBadge.style.display = 'none';
            }
        }
        
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        setupModalNavigation();
    }
}

function closeImageModal(event) {
    const modal = document.getElementById('imageModal');
    
    // Only close if clicking on the modal background, not the content
    if (event && event.target !== modal) {
        return;
    }
    
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
}

function setupModalNavigation() {
    const prevBtn = document.getElementById('modalPrevBtn');
    const nextBtn = document.getElementById('modalNextBtn');
    
    if (images.length <= 1) {
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
        return;
    }
    
    if (prevBtn) {
        prevBtn.style.display = 'block';
    }
    
    if (nextBtn) {
        nextBtn.style.display = 'block';
    }
}

function prevImageInModal(event) {
    event.stopPropagation();
    currentImageIndex = currentImageIndex > 0 ? currentImageIndex - 1 : images.length - 1;
    updateModalImage();
}

function nextImageInModal(event) {
    event.stopPropagation();
    currentImageIndex = currentImageIndex < images.length - 1 ? currentImageIndex + 1 : 0;
    updateModalImage();
}

function updateModalImage() {
    const modalImage = document.getElementById('modalImage');
    const modalCounter = document.getElementById('modalCounter');
    const modalBadge = document.getElementById('modalMainBadge');
    
    if (modalImage && images[currentImageIndex]) {
        modalImage.src = images[currentImageIndex].src;
        modalImage.alt = 'Home Image ' + (currentImageIndex + 1);
        
        if (modalCounter) {
            modalCounter.textContent = `${currentImageIndex + 1}/${images.length}`;
        }
        
        if (modalBadge) {
            if (images[currentImageIndex].is_main) {
                modalBadge.style.display = 'block';
            } else {
                modalBadge.style.display = 'none';
            }
        }
    }
    
    // Also update main gallery
    displayMainImage();
    updateImageDots();
    updateImageCounter();
}

// Keyboard navigation
document.addEventListener('keydown', function(event) {
    const modal = document.getElementById('imageModal');
    if (modal && modal.classList.contains('show')) {
        if (event.key === 'Escape') {
            closeImageModal();
        } else if (event.key === 'ArrowLeft') {
            prevImageInModal(event);
        } else if (event.key === 'ArrowRight') {
            nextImageInModal(event);
        }
    }
});

// Image validation function for form submission
function validateImageCount() {
    if (images.length === 0) {
        alert('Vui lòng thêm ít nhất 1 ảnh cho nhà của bạn.');
        return false;
    }
    return true;
}

// Utility function to show all rules modal
function showAllRulesModal() {
    const modal = document.getElementById('allRulesModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeAllRulesModal() {
    const modal = document.getElementById('allRulesModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Utility function to show all amenities modal
function showAllAmenitiesModal() {
    const modal = document.getElementById('allAmenitiesModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeAllAmenitiesModal() {
    const modal = document.getElementById('allAmenitiesModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const rulesModal = document.getElementById('allRulesModal');
    const amenitiesModal = document.getElementById('allAmenitiesModal');
    
    if (event.target === rulesModal) {
        closeAllRulesModal();
    }
    
    if (event.target === amenitiesModal) {
        closeAllAmenitiesModal();
    }
}; 