// Shared components: Navbar and Sidebar

// Render Navbar
function renderNavbar() {
    const navbarContainer = document.getElementById('navbar-container');
    if (!navbarContainer) return;

    // Detect if we're in a subdirectory (pages/) or root
    const isInPagesDir = window.location.pathname.includes('/pages/');
    const homeHref = isInPagesDir ? '../index.html' : './index.html';

    navbarContainer.innerHTML = `
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container-fluid">
                <button class="btn btn-link text-white me-2" id="sidebar-toggle-btn" onclick="toggleSidebar()">
                    <i class="bi bi-list fs-4"></i>
                </button>
                <a class="navbar-brand" href="${homeHref}">
                    <i class="bi bi-file-earmark-check"></i>
                    Corrector de Documentos
                </a>
            </div>
        </nav>
    `;
}

// Render Sidebar
function renderSidebar(activePage = '') {
    const sidebarContainer = document.getElementById('sidebar-container');
    if (!sidebarContainer) return;

    // Detect if we're in a subdirectory (pages/) or root
    const isInPagesDir = window.location.pathname.includes('/pages/');
    const baseHref = isInPagesDir ? '..' : '.';

    const menuItems = [
        { id: 'home', label: 'Dashboard', icon: 'house-door', href: `${baseHref}/index.html` },
        { id: 'upload-commercial', label: 'Documentos Comerciales', icon: 'cloud-upload', href: `${baseHref}/pages/upload-commercial.html` },
        { id: 'upload-provisional', label: 'Documento Provisorio', icon: 'file-earmark-plus', href: `${baseHref}/pages/upload-provisional.html` },
        { id: 'compare', label: 'Comparar', icon: 'arrow-left-right', href: `${baseHref}/pages/compare.html` },
        { id: 'prompts', label: 'Gestión de Prompts', icon: 'chat-left-text', href: `${baseHref}/pages/prompts.html` },
        { id: 'page-types', label: 'Tipos de Páginas', icon: 'file-earmark-ruled', href: `${baseHref}/pages/page-types.html` },
        { id: 'page-detection', label: 'Detectar Páginas', icon: 'file-earmark-check', href: `${baseHref}/pages/page-detection.html` },
        { id: 'attribute-extraction', label: 'Configurar Atributos', icon: 'bounding-box', href: `${baseHref}/pages/attribute-extraction.html` },
        { id: 'extract-attributes', label: 'Extraer Atributos', icon: 'file-text', href: `${baseHref}/pages/extract-attributes.html` },
        { id: 'history', label: 'Historial', icon: 'clock-history', href: `${baseHref}/pages/history.html` }
    ];

    let menuHtml = menuItems.map(item => {
        const activeClass = activePage === item.id ? 'active' : '';
        return `
            <li class="nav-item">
                <a class="nav-link ${activeClass}" href="${item.href}">
                    <i class="bi bi-${item.icon}"></i> ${item.label}
                </a>
            </li>
        `;
    }).join('');

    sidebarContainer.innerHTML = `
        <div class="sidebar" id="sidebar">
            <ul class="nav flex-column nav-pills px-2">
                ${menuHtml}
            </ul>
        </div>
    `;
}

// Toggle Sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');

    if (sidebar && mainContent) {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');

        if (toggleBtn) {
            const icon = toggleBtn.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.className = 'bi bi-list fs-4';
            } else {
                icon.className = 'bi bi-x-lg fs-4';
            }
        }
    }
}

// Initialize components on page load
document.addEventListener('DOMContentLoaded', () => {
    renderNavbar();

    // Detect active page from current URL
    const currentPath = window.location.pathname;
    let activePage = 'home';

    if (currentPath.includes('upload-commercial')) activePage = 'upload-commercial';
    else if (currentPath.includes('upload-provisional')) activePage = 'upload-provisional';
    else if (currentPath.includes('compare')) activePage = 'compare';
    else if (currentPath.includes('prompts')) activePage = 'prompts';
    else if (currentPath.includes('page-types')) activePage = 'page-types';
    else if (currentPath.includes('page-detection')) activePage = 'page-detection';
    else if (currentPath.includes('extract-attributes')) activePage = 'extract-attributes';
    else if (currentPath.includes('attribute-extraction')) activePage = 'attribute-extraction';
    else if (currentPath.includes('history')) activePage = 'history';

    renderSidebar(activePage);
});
