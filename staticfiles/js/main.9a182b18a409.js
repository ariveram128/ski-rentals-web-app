// SkiRentals - Main JavaScript

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Equipment filter functionality
    const equipmentFilters = document.querySelectorAll('.equipment-filter');
    if (equipmentFilters.length) {
        equipmentFilters.forEach(filter => {
            filter.addEventListener('change', filterEquipment);
        });
    }

    // Function to filter equipment
    function filterEquipment() {
        const selectedType = document.querySelector('#type-filter').value;
        const selectedSkillLevel = document.querySelector('#skill-level-filter').value;
        
        const equipmentCards = document.querySelectorAll('.equipment-card');
        
        equipmentCards.forEach(card => {
            const cardType = card.dataset.type;
            const cardSkillLevel = card.dataset.skillLevel;
            
            const typeMatch = selectedType === 'all' || cardType === selectedType;
            const skillMatch = selectedSkillLevel === 'all' || cardSkillLevel === selectedSkillLevel;
            
            if (typeMatch && skillMatch) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Star rating functionality
    const ratingInputs = document.querySelectorAll('.rating-input');
    if (ratingInputs.length) {
        ratingInputs.forEach(input => {
            input.addEventListener('change', updateRatingDisplay);
        });
        
        // Initialize rating display
        updateRatingDisplay();
    }

    function updateRatingDisplay() {
        const ratingValue = document.querySelector('.rating-input:checked')?.value || 0;
        const ratingStars = document.querySelectorAll('.rating-star');
        
        ratingStars.forEach((star, index) => {
            if (index < ratingValue) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }

    // Equipment search functionality
    const searchInput = document.querySelector('#equipment-search');
    if (searchInput) {
        searchInput.addEventListener('input', searchEquipment);
    }

    function searchEquipment() {
        const searchTerm = searchInput.value.toLowerCase();
        const equipmentCards = document.querySelectorAll('.equipment-card');
        
        equipmentCards.forEach(card => {
            const cardTitle = card.querySelector('.card-title').textContent.toLowerCase();
            const cardBrand = card.querySelector('.card-brand').textContent.toLowerCase();
            const cardModel = card.querySelector('.card-model').textContent.toLowerCase();
            
            if (cardTitle.includes(searchTerm) || 
                cardBrand.includes(searchTerm) || 
                cardModel.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
}); 