// Configuration file for API keys and other settings
const CONFIG = {
    // Google Maps API Key - Updated with user's API key
    // NOTE: This API key needs to be properly configured in Google Cloud Console
    // Required APIs: Maps JavaScript API, Geocoding API
    // Required Billing: Active billing account
    GOOGLE_MAPS_API_KEY: 'AIzaSyDQtHXQcHIaZgKYX7pEWQkntBPeTfu1hqQ',
    
    // Default map settings
    DEFAULT_MAP_CENTER: {
        lat: 10.7769,  // TP.HCM
        lng: 106.7009
    },
    
    DEFAULT_MAP_ZOOM: 15,
    
    // Map styles
    MAP_STYLES: [
        {
            featureType: "poi",
            elementType: "labels",
            stylers: [{ visibility: "off" }]
        }
    ]
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
} 