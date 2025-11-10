# База лицензий на недропользование

## Overview
This project is a Django-based web application for managing a database of subsurface use licenses. It features an interactive Yandex.Map for visualizing licenses, detailed license information via modal windows, and document upload/download. The application aims to provide a comprehensive tool for tracking and managing mineral extraction licenses, offering filtering, search, and GeoJSON map integration. It prioritizes ease of use, clear visualization, and is designed for future integration with external databases and LDAP authentication for enterprise environments. Key capabilities include dynamic UI elements like filter buttons and map legends based on license types, comprehensive user documentation, and a complete light/dark theme toggle.

## User Preferences
I prefer simple language and clear explanations. I like iterative development and want the agent to ask before making major changes. I prefer detailed explanations for complex tasks. Do not make changes to the `media/` folder. Do not make changes to the `create_test_data.py` file without explicit instruction. **Design preference:** Modern, light, clean design inspired by contemporary property websites like Orrivo - featuring large typography, white backgrounds, statistics dashboards, and SVG icons.

## System Architecture
The application is a Django web application.

- **UI/UX:** The interface features a modern Orrivo-inspired design:
  - Hero section with a light cyan-to-blue gradient background and large dark typography.
  - Live statistics dashboard (total, active licenses, regions, license types).
  - Sticky quick navigation menu with smooth-scroll anchors.
  - Dedicated analytics page (`/analytics/`) with three Chart.js visualizations (doughnut, bar, line) styled with a blue palette.
  - Clean white navigation header with subtle shadows.
  - Light color scheme (white background, black text, accent blue).
  - License cards with large typography, SVG icons, and metadata grid.
  - Pagination controls and item counters.
  - Interactive Yandex.Map (600px height, rounded corners).
  - Section headers with centered titles.
  - Integrated light/dark theme toggle with CSS variables and `localStorage` persistence.
  - Modern login page (`/login/`) with gradient background, centered card, SVG icons in input fields, and full theme support.
  - Uses Bootstrap 5, Chart.js 4.4.0, Vanilla JavaScript, and Inter font family.
  - Dedicated `/help/` page with comprehensive user documentation.
  - Export buttons with Bootstrap tooltips and loading indicators for better UX.

- **Technical Implementations:**
    - **Interactive Map:** Displays licenses using Yandex.Maps JavaScript API 2.1, with markers and polygons colored by mineral usage type.
    - **Pagination:** Django Paginator with 12 items per page, smart controls.
    - **Analytics Dashboard:** Chart.js 4.4.0 for type distribution, regional analysis, and expiry forecast.
    - **Data Management:** CRUD operations for `License` and `Document` models via Django Admin and API.
    - **Filtering & Search:** Filters by status, region, type, mineral; search by license number and user. Dynamic filter buttons and map legend based on license types.
    - **Document Management:** Upload/download functionality for license-linked documents. **Security:** All document downloads, Excel exports, and PDF exports require user authentication via `@login_required` decorator.
    - **GeoJSON Integration:** Web and admin interfaces support drag-and-drop or traditional GeoJSON uploads, automatically updating license data, parsing info, determining regions, and calculating polygon centers.
    - **Authentication:** Django's built-in authentication by default; **Multi-domain LDAP authentication** is configurable via `USE_LDAP=true` environment variable. Supports automatic domain detection or manual domain selection by users. Custom `MultiDomainLDAPBackend` handles authentication across multiple LDAP domains (Active Directory, OpenLDAP).
    - **Data Export:** Supports export to Excel (using `openpyxl`) and PDF (using `reportlab`) with filter integration and professional styling. **Security:** Both export endpoints require user authentication.
    - **Automatic Status Updates:** Expiration detection in API and management command for batch updates.

- **Feature Specifications:**
    - **License Model:** Stores unique number, mineral usage type, user, coordinates, region, dates, mineral type, status, and description.
    - **Document Model:** Links to a license, stores name, file, type, upload date, and user.

- **System Design Choices:**
    - **Modularity:** Project organized into `mineral_licenses` (settings) and `licenses` (application) Django apps.
    - **Page Routes:**
      - `/` - Main page with statistics, licenses, map, and navigation.
      - `/analytics/` - Dedicated analytics page.
      - `/help/` - User documentation page.
    - **API Endpoints:** RESTful API for licenses (paginated, all, by ID), document upload/download, and Excel export.
    - **Navigation Features:** Sticky navigation, back-to-top button, section IDs for anchor links.
    - **Environment Configuration:** Uses environment variables for sensitive data and database connection.

## External Dependencies
- **Database:** PostgreSQL (production), SQLite (development).
- **Mapping Service:** Yandex.Maps JavaScript API 2.1.
- **Web Server:** Gunicorn.
- **Dependency Management:** uv.
- **Frontend Framework:** Bootstrap 5.
- **Charting Library:** Chart.js 4.4.0.
- **Excel Export:** `openpyxl`.
- **PDF Export:** `reportlab`.
- **LDAP Integration (optional):** `django-auth-ldap`, `python-ldap`.

## Documentation
- **DEPLOYMENT_LOCAL.md** - Полная методичка по развертыванию на локальном ПК с детальными инструкциями по PostgreSQL
- **DEPLOYMENT_UBUNTU_SERVER.md** - Полная методичка по развертыванию на Ubuntu Server 22.04 LTS с Apache, mod_wsgi, двумя дисками, SSL, и автоматическими бэкапами
- **PostgreSQL_CHEATSHEET.md** - Шпаргалка по командам PostgreSQL для быстрой справки
- **LDAP_MULTI_DOMAIN.md** - Инструкция по настройке мультидоменной LDAP аутентификации
- **LDAP_SETUP.md** - Общая документация по LDAP аутентификации
- **requirements.txt** - Список зависимостей Python для установки через pip
- **/help/** - Встроенная справка пользователя в веб-интерфейсе