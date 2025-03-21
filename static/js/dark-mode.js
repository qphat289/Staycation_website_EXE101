document.addEventListener('DOMContentLoaded', function() {
    // Kiểm tra trạng thái dark mode từ localStorage
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
        document.body.classList.add('dark-mode');
        document.getElementById('darkMode').checked = true;
    }

    // Xử lý khi người dùng thay đổi dark mode
    document.getElementById('darkMode').addEventListener('change', function(e) {
        if (e.target.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'false');
        }
    });
}); 