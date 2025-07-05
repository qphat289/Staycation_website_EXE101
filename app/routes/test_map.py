from flask import Blueprint, render_template_string

test_map_bp = Blueprint('test_map', __name__)

@test_map_bp.route('/debug-code')
def debug_code():
    with open('debug_code_issues.html', 'r', encoding='utf-8') as f:
        return f.read()

@test_map_bp.route('/test-map')
def test_map():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Map Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #map { width: 100%; height: 400px; border: 1px solid #ccc; margin: 20px 0; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .info { background-color: #d1ecf1; color: #0c5460; }
        .address { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Map Test - Staycation Website</h1>
    <div class="address">
        <strong>Test Address:</strong> 945 Quốc lộ 1A, Phường An Lạc, Quận Bình Tân, TP. Hồ Chí Minh
    </div>
    <div id="status" class="status info">Testing map loading...</div>
    <div id="map"></div>

    <script src="{{ url_for('static', filename='js/config.js') }}"></script>
    <script>
        function initMap() {
            const statusDiv = document.getElementById('status');
            
            try {
                // Test address from your application
                const address = "945 Quốc lộ 1A, Phường An Lạc, Quận Bình Tân, TP. Hồ Chí Minh, Vietnam";
                
                // Create geocoder
                const geocoder = new google.maps.Geocoder();
                
                // Geocode the address
                geocoder.geocode({ address: address }, function(results, status) {
                    if (status === 'OK' && results[0]) {
                        const location = results[0].geometry.location;
                        
                        // Create map
                        const map = new google.maps.Map(document.getElementById('map'), {
                            zoom: 15,
                            center: location,
                            mapTypeControl: false,
                            streetViewControl: false,
                            fullscreenControl: true,
                            zoomControl: true
                        });
                        
                        // Create marker
                        const marker = new google.maps.Marker({
                            position: location,
                            map: map,
                            title: 'Test Location',
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
                                <strong style="color: #333;">Test Location</strong><br>
                                <span style="color: #666; font-size: 14px;">${address}</span>
                            </div>`
                        });
                        
                        marker.addListener('click', function() {
                            infoWindow.open(map, marker);
                        });
                        
                        statusDiv.className = 'status success';
                        statusDiv.textContent = 'SUCCESS: Map loaded successfully with geocoding!';
                        
                    } else {
                        statusDiv.className = 'status error';
                        statusDiv.textContent = 'ERROR: Geocoding failed - ' + status;
                    }
                });
                
            } catch (error) {
                statusDiv.className = 'status error';
                statusDiv.textContent = 'ERROR: ' + error.message;
            }
        }
        
        function handleApiError() {
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status error';
            statusDiv.textContent = 'ERROR: Failed to load Google Maps API. Check API key and internet connection.';
        }
        
        // Load Google Maps API
        if (typeof CONFIG !== 'undefined' && CONFIG.GOOGLE_MAPS_API_KEY) {
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${CONFIG.GOOGLE_MAPS_API_KEY}&callback=initMap&libraries=geometry`;
            script.async = true;
            script.defer = true;
            script.onerror = handleApiError;
            document.head.appendChild(script);
        } else {
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status error';
            statusDiv.textContent = 'ERROR: CONFIG or Google Maps API key not found.';
        }
    </script>
</body>
</html>
    ''') 