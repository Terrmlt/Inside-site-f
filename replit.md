# База лицензий на недропользование

## Overview
This project is a Django-based web application designed to manage a database of subsurface use licenses. It features an interactive Yandex.Map for visualizing licenses, detailed license information through modal windows, and document upload/download functionality. The application aims to provide a comprehensive tool for tracking and managing mineral extraction licenses, offering filtering, search capabilities, and GeoJSON map integration. It is built with a focus on ease of use for administrators and clear visualization for all users, with an eye towards future integration with external databases and LDAP authentication for enterprise environments.

## Recent Changes
- **November 5, 2025 (Latest - UX Enhancements & LDAP):** Added drag-and-drop file upload and LDAP authentication templates:
  - **Drag-and-Drop GeoJSON Upload**: Admin panel now features interactive file drop zone with visual feedback (hover effects, file validation)
  - **Dual Upload Methods**: Both drag-and-drop and traditional file picker work simultaneously
  - **LDAP Authentication Ready**: Complete LDAP setup with templates, detailed configuration file (`settings_ldap.py`), and comprehensive documentation
  - **LDAP Documentation**: Created `LDAP_SETUP.md` with step-by-step instructions, examples for Active Directory/OpenLDAP/FreeIPA, and troubleshooting guide
  - **Conditional LDAP**: LDAP enabled via `USE_LDAP=true` environment variable, disabled by default
  - **Installed Packages**: `django-auth-ldap` (5.2.0) and `python-ldap` (3.4.5)
- **November 4, 2025 (Dynamic UI Generation):** Made filter buttons and map legend fully dynamic to support arbitrary license types:
  - **Static Statistics Cards**: Hero section shows 4 fixed cards (Total licenses, Active, Regions, License types count)
  - **Dynamic Filter Buttons**: Quick filter tabs generate automatically from unique license types with live counters
  - **Dynamic Map Legend**: Color legend generates based on actual license types in data using `getColorByUsageType()`
  - **Automatic Updates**: Filters, counters, and legend update when new GeoJSON files with different license types are loaded
  - **Functions**: `generateLicenseTypeTabs()`, `generateMapLegend()`, `updateStatistics()`, and `updateTabCounts()`
- **November 4, 2025 (Bug Fixes):** Fixed pagination and filter duplication issues:
  - Fixed dual-mode pagination (server-side without filters, client-side with filters)
  - Fixed filter dropdown duplication by clearing old options before repopulating
  - Fixed map display to show all 55 polygons without filters
  - Added `updateResultsCount()` to `loadLicenses()` for consistent UI
- **November 4, 2025 (Navigation & Analytics Separation):** Separated analytics to dedicated page and added navigation:
  - **Separate Analytics Page**: Created `/analytics/` with own view and template, showing all three Chart.js visualizations
  - **Quick Navigation Menu**: Sticky navigation bar with smooth-scroll anchors (Статистика, Лицензии, Карта) + external link to Analytics
  - **Back to Top Button**: Fixed button (bottom-right) with smooth animation, appears after 300px scroll
  - **Main Page Cleanup**: Removed analytics section, Chart.js dependency, and related code from homepage
  - **Orrivo Styling**: Navigation menu and buttons styled with orange accents (#ff6b35) and clean design
- **November 1, 2025 (Pagination & Analytics):** Added pagination and data analytics with Chart.js:
  - **Pagination**: Smart pagination with 12 licenses per page, page navigation controls (prev/next, numbered pages with ellipsis), and "Showing X-Y of Z" counter
  - **Analytics Dashboard**: Three interactive Chart.js visualizations in Orrivo style:
    - Круговая диаграмма распределения по типам недропользования
    - Столбчатая диаграмма топ-5 регионов по количеству лицензий
    - Линейный график истечения лицензий (прогноз на 12 месяцев)
  - **Dual API Architecture**: Separate endpoints `/api/licenses/` (paginated) and `/api/licenses/all/` (complete dataset for analytics)
- **November 1, 2025 (Quick Improvements):** Added three productivity enhancements:
  - **Quick Filter Tabs**: Interactive tabs for instant filtering by license type (All, БЭ, БП, БР, ТП) with live counters
  - **Excel Export**: One-click export to professionally formatted Excel with current filters applied (openpyxl integration)
  - **Auto Status Updates**: Automatic expiration detection in API + management command for batch updates (`python manage.py update_license_statuses`)
- **November 1, 2025:** Complete redesign in Orrivo style - modern, light, and clean:
  - Switched to light color scheme with white background and dark text for better readability
  - Added hero section with dark gradient background featuring large typography
  - Implemented live statistics dashboard (total licenses, active licenses, regions, license types)
  - Redesigned license cards with large typography, SVG icons, and metadata grid layout
  - Created clean white navigation header with subtle shadows
  - Updated color palette: accent orange (#ff6b35), neutral grays, clean whites
  - Added section headers with centered titles and subtitles
  - Implemented modern card hover effects with translateY animations
  - Enhanced modal windows with gradient headers and refined styling
- **November 1, 2025:** Initial design modernization - removed all emoji icons for professional appearance, implemented Inter font family, created professional color palette with CSS custom properties

## User Preferences
I prefer simple language and clear explanations. I like iterative development and want the agent to ask before making major changes. I prefer detailed explanations for complex tasks. Do not make changes to the `media/` folder. Do not make changes to the `create_test_data.py` file without explicit instruction. **Design preference:** Modern, light, clean design inspired by contemporary property websites like Orrivo - featuring large typography, white backgrounds, statistics dashboards, and SVG icons.

## System Architecture
The application is a Django web application.
- **UI/UX:** The interface features a modern Orrivo-inspired design with:
  - Hero section with light cyan-to-blue gradient background (#ecfeff to #eff6ff) and large dark typography
  - Live statistics dashboard showing total licenses, active count, regions, and license types
  - Sticky quick navigation menu with smooth-scroll anchors and external analytics link
  - Back-to-top button (fixed, bottom-right, appears on scroll >300px)
  - Dedicated analytics page (`/analytics/`) with three Chart.js visualizations (doughnut, bar, line) styled with blue palette
  - Clean white navigation header with subtle shadows
  - Light color scheme (white #ffffff background, black #1a1a1a text, accent blue #3B82F6)
  - License cards with large typography, SVG icons, and metadata grid showing region, type, and minerals
  - Pagination controls with numbered pages, prev/next buttons, and item counters
  - Interactive Yandex.Map with 600px height and rounded corners
  - Section headers with centered titles and descriptive subtitles
  - Bootstrap 5, Chart.js 4.4.0, Vanilla JavaScript, and Inter font family for the frontend
- **Technical Implementations:**
    - **Interactive Map:** Displays licenses using Yandex.Maps JavaScript API 2.1, with markers and polygons (colored by mineral usage type, e.g., БЭ, БП, БР)
    - **Pagination:** Django Paginator with 12 items per page, smart page controls with ellipsis for large datasets
    - **Analytics Dashboard:** Chart.js 4.4.0 with three visualizations (type distribution, regional analysis, expiry forecast)
    - **Data Management:** CRUD operations for `License` and `Document` models, accessible via Django Admin and API endpoints.
    - **Filtering & Search:** Licenses can be filtered by status, region, type, and mineral, and searched by license number and user.
    - **Document Management:** Upload and download functionality for documents linked to licenses.
    - **GeoJSON Integration:** Web and admin interfaces allow for uploading GeoJSON files via drag-and-drop or traditional file picker, which automatically update or create license data, parse information, determine regions, and calculate polygon centers.
    - **Authentication:** Django's built-in authentication is default. LDAP authentication ready to enable via `USE_LDAP=true` environment variable. Full LDAP configuration templates included for Active Directory, OpenLDAP, and FreeIPA with detailed documentation in `LDAP_SETUP.md` and `mineral_licenses/settings_ldap.py`.
    - **Database:** PostgreSQL is configured as the production database, with SQLite for development.
- **Feature Specifications:**
    - **License Model:** Stores unique license number, mineral usage type, user, coordinates, region, dates, mineral type, status, and description.
    - **Document Model:** Links to a license, stores document name, file, type, upload date, and user.
- **System Design Choices:**
    - **Modularity:** The project is organized into `mineral_licenses` (project settings) and `licenses` (core application) Django apps.
    - **Page Routes:**
      - `/` - Main page with statistics, licenses, map, and navigation
      - `/analytics/` - Dedicated analytics page with Chart.js visualizations
    - **API Endpoints:** Provides RESTful API for:
      - Licenses: `GET /api/licenses/` (paginated), `GET /api/licenses/all/` (complete dataset), `GET /api/licenses/<id>/`
      - Documents: `POST /api/licenses/<id>/upload/`, `GET /api/documents/<id>/download/`
      - Export: `GET /api/licenses/export/excel/`
    - **Navigation Features:**
      - Sticky quick navigation with smooth-scroll anchors
      - Back-to-top button with scroll-triggered visibility
      - Section IDs for anchor links: #statistics, #licenses, #map-section
    - **Environment Configuration:** Uses environment variables for sensitive data (`SECRET_KEY`, `YANDEX_MAPS_API_KEY`) and database connection.

## External Dependencies
- **Database:** PostgreSQL (via Neon on Replit), SQLite (for development).
- **Mapping Service:** Yandex.Maps JavaScript API 2.1.
- **Web Server:** Gunicorn.
- **Dependency Management:** uv.
- **Frontend Framework:** Bootstrap 5.
- **Authentication (planned):** `django-auth-ldap` for LDAP integration.