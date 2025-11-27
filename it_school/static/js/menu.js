document.addEventListener('DOMContentLoaded', function() {
    const savedState = localStorage.getItem('openSubmenus');
    if (savedState) {
        const openSubmenus = JSON.parse(savedState);
        openSubmenus.forEach(submenuId => {
            const submenu = document.getElementById(submenuId + '-submenu');
            const link = document.querySelector(`[data-submenu="${submenuId}-submenu"]`);
            if (submenu && link) {
                submenu.classList.add('open');
                const arrow = link.querySelector('.nav-arrow');
                if (arrow) {
                    arrow.style.transform = 'rotate(90deg)';
                }
            }
        });
    }

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const submenu = this.nextElementSibling;
            const submenuId = submenu.id.replace('-submenu', '');
            
            submenu.classList.toggle('open');
            
            const arrow = this.querySelector('.nav-arrow');
            if (arrow) {
                arrow.style.transform = submenu.classList.contains('open') 
                    ? 'rotate(90deg)' 
                    : 'rotate(0deg)';
            }
            
            saveSubmenuState();
        });
    });
    
    function saveSubmenuState() {
        const openSubmenus = [];
        document.querySelectorAll('.submenu.open').forEach(menu => {
            openSubmenus.push(menu.id.replace('-submenu', ''));
        });
        localStorage.setItem('openSubmenus', JSON.stringify(openSubmenus));
    }
});